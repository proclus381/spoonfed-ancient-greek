"""Placement plan for untaught inflection cells (schemes, lemma-specific words): where each new card goes.

usage: plan2.py CATALOG.tsv OUT.tsv      (venv python, repository root; work/tmp/items.json current)
For every key the catalog lists as never taught, and every key that is a second new item on a card (a gap the
card exposes), the anchor is the first card at or after the key's chapter that introduces a cell of the same
scheme (so the paradigm's cells stand together); if the key is used earlier than that, the card before its
first use. Candidates: lemmas known before the anchor whose generated paradigm has the cell.
OUT rows: chapter, anchor card n, key, first use (n or -), anchor Greek, candidates (lemma=form …)."""
import collections
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'project'))
os.chdir(os.path.join(ROOT, 'project'))
import check2 as K  # noqa: E402

cards, known, uses = K.run(K.P.sentence_paths() if hasattr(K, 'P') else
                           sorted(os.path.join('sentences', f) for f in os.listdir('sentences')
                                  if re.match(r'ch\d\d\.txt$', f)), quiet=True, show=False)
items = json.load(open(os.path.join(ROOT, 'work', 'tmp', 'items.json'), encoding='utf-8'))
first_use, intro, lemma_at = {}, {}, {}
for c in items:
    for it in c['items']:
        first_use.setdefault(it, c['n'])
    for it in c['new']:
        intro.setdefault(it, c['n'])
        if it.startswith('L:'):
            lemma_at[it[2:]] = c['n']
by_n = {c['n']: c for c in items}
SKIP = re.compile(r'^(ἄγω:A|πάρειμι:|ἄπειμι:|ἔξεστι:)|δυναμ')


def scheme(k):
    return k.split(':', 1)[0]


todo = set()
for line in open(sys.argv[1], encoding='utf-8'):
    k, taught = line.split('\t')[:2]
    if taught == '-' and not SKIP.search(k) and not k.startswith('V'):
        todo.add(k)

coarse = {c['gr']: set(c['new']) for c in json.load(open(os.path.join(ROOT, 'work', 'tmp', 'items_coarse.json'),
                                                         encoding='utf-8'))}
NOMINAL = set(K.SCH.NOUN_SCHEMES) | set(K.SCH.ADJ_SCHEMES) | set(K.SCH.PTC_SCHEMES) | K.SPECIFIC | set(K.IRREG_ADJ) | \
    {'pers', 'ἐγώ', 'σύ', 'ἕ', 'σφεῖς'}
probcards = {}
for c in cards:
    if any(p.endswith(' NEW') for p in c['problems']):
        old = coarse.get(c['gr'], set())
        nn = [x for x in c['new'] if scheme(x) in NOMINAL and ':' in x and not x.startswith('L:')]
        keep = [x for x in nn if x in old or K.FINE_OF.get(x, set()) & old]      # the card's own item (refined)
        probcards[c['n']] = c['new']
        for x in nn:
            if x not in keep:
                todo.add(x)
todo = {k for k in todo if scheme(k) in NOMINAL}
# candidate forms per key
cand = collections.defaultdict(list)
src = [(f, lst) for f, lst in K.GEN.items()] + [(f, [tuple(a) for a in al if len(a) == 2]) for f, al in K.EXTRA.items()]
K.TRUST[0] = True
for f, lst in src:
    for l, t in lst:
        try:
            ks = {K.gkey(l, t[:9], f), K.ptc_key(l, t[:9], f)}
        except Exception:
            continue
        pk = K.ptc_key(l, t[:9], f)
        if pk:
            K.FINE_OF[pk].add(K.gkey(l, t[:9], f) or 'Vpaptc.mn')
        for k in ks:
            if k in todo and (l, f) not in cand[k]:
                cand[k].append((l, f))
sib = collections.defaultdict(list)            # scheme → cards introducing one of its cells, in order
for k, n in intro.items():
    if ':' in k and not k.startswith(('L:', 'C:', 'X:', 'S:')):
        sib[scheme(k)].append(n)
rows = []
for k in sorted(todo):
    ch = K.ch_of(k)
    sc = scheme(k)
    after = [n for n in sorted(sib[sc]) if by_n[n]['ch'] >= ch]
    anchor = after[0] if after else next((c['n'] for c in items if c['ch'] >= ch), items[-1]['n'])
    fu = first_use.get(k)
    words = sorted({lemma_at[l] for l, f in cand[k] if l in lemma_at})
    note = ''
    if words and anchor < words[0]:
        anchor = words[0]                      # not before a word of the scheme is known
    if fu and anchor >= fu:
        anchor = fu - 1
        if not words or words[0] >= fu:
            note = 'LEMMA-FIRST '               # the first use brings its word too: a card for the word before it
    ach = by_n[anchor]['ch']
    cs = [(l, f) for l, f in cand[k] if lemma_at.get(l, 99999) <= anchor]
    cs.sort(key=lambda x: (len(f) > len(l) + 3 and ('τατ' in f or 'τερ' in f), lemma_at.get(x[0], 0)))
    rows.append((ach, anchor, k, fu or '-', by_n[anchor]['gr'][:50],
                 note + (' '.join('%s=%s' % x for x in cs[:6]) or '(no known word: %d later)' % len(cand[k]))))
rows.sort(key=lambda r: (r[1], r[2]))
with open(sys.argv[2], 'w', encoding='utf-8') as out:
    for r in rows:
        out.write('\t'.join(str(x) for x in r) + '\n')
print(len(rows), 'cells to place;', sum(1 for r in rows if r[5].startswith('(no')), 'without a known word')
print(collections.Counter(r[0] for r in rows))
print('LEMMA-FIRST', sum(1 for r in rows if r[5].startswith('LEMMA')))
