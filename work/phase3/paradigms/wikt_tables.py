"""Parse the declension tables of Wiktionary's Appendix:Ancient_Greek_grammar_tables (raw wikitext).

usage: python3 -I wikt_tables.py PAGE.wikitext OUT.tsv
Reads only the <noinclude> copy of each table. Output rows: section, example word, case, number, form(s).
Columns are matched by the 'colspan' example headers and the Singular / Dual / Plural header row."""
import re
import sys
import unicodedata as ud

txt = ud.normalize('NFC', open(sys.argv[1], encoding='utf-8').read())
txt = re.sub(r'<includeonly>.*?</includeonly>', '', txt, flags=re.S)
LANG = re.compile(r'\{\{lang\|grc\|([^}]*)\}\}')
out = []
sect = []
lines = txt.split('\n')
i = 0
while i < len(lines):
    ln = lines[i]
    m = re.match(r'^(=+)\s*(.*?)\s*\1\s*$', ln)
    if m:
        lvl = len(m.group(1))
        sect = sect[:lvl - 2] + [LANG.sub(r'\1', m.group(2))]
        i += 1
        continue
    if '{|' in ln:
        heads, nums, rows = [], [], []
        j = i
        while j < len(lines) and '|}' not in lines[j]:
            l2 = lines[j]
            if l2.startswith('!') and 'colspan' in l2 and LANG.search(l2):
                span = int(re.search(r'colspan="?(\d+)', l2).group(1))
                heads.append((LANG.search(l2).group(1), span))
            elif l2.strip() in ('! Singular', '! Dual', '! Plural'):
                nums.append(l2.strip()[2:])
            elif l2.startswith('! ') and l2[2:].strip() in ('Nominative', 'Genitive', 'Dative', 'Accusative',
                                                            'Vocative'):
                case = l2[2:].strip()
                cells = lines[j + 1].lstrip('|').split('||')
                rows.append((case, [', '.join(LANG.findall(c)) for c in cells]))
            j += 1
        if heads and nums and rows:
            cols = []
            for h, span in heads:
                cols += [h] * span
            for case, cells in rows:
                for k, form in enumerate(cells):
                    if k < len(cols) and k < len(nums) and form:
                        out.append(('/'.join(sect[-2:]), cols[k], case[:3].lower(), nums[k][0].lower(), form))
        i = j + 1
        continue
    i += 1
with open(sys.argv[2], 'w', encoding='utf-8') as f:
    for r in out:
        f.write('\t'.join(r) + '\n')
seen = []
for r in out:
    if (r[0], r[1]) not in seen:
        seen.append((r[0], r[1]))
for s, w in seen:
    print(s, '|', w, '|', sum(1 for r in out if r[0] == s and r[1] == w))
