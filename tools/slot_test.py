"""Try candidate sentences in the slot of existing cards: same known items as the card, same chapter.

usage: slot_test.py CANDIDATES.tsv
CANDIDATES.tsv: lines  n <TAB> greek <TAB> english [<TAB> extras]   (n = card number in deck order, as in
cards_current.tsv / fallback_status.tsv; extras = column-4 tokens such as +X:e-than or @form hints).
For each candidate prints the card's new items, the candidate's new items, and problems; 'OK' when they match."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as P  # noqa: E402
import check2 as K  # noqa: E402

want = {}
for line in open(sys.argv[1], encoding='utf-8'):
    if line.strip() and not line.startswith('#'):
        p = line.rstrip('\n').split('\t')
        want.setdefault(int(p[0]), []).append(p[1:] + [''] * (3 - len(p[1:])))


def extras(s):
    manual = [w[1:] for w in s.split() if w.startswith('+')]
    hints = {}
    for w in s.split():
        if w.startswith('@'):
            import re
            m = re.match(r'@([^=:]+)(?:=([^:]+))?(?::(.+))?$', K.nfc(w))
            if m:
                hints[m.group(1)] = (m.group(2), (m.group(3) or '').split('.') if m.group(3) else [])
    return manual, hints


known, n = set(), 0
for path in P.sentence_paths():
    for c in K.read_cards(path):
        n += 1
        items, toks, chosen, probs = K.card_items(c['gr'], known, c['chapter'], c['manual'], c['hints'], c['en'])
        if n in want:
            cnew = sorted(x for x in items if x not in known)
            print('#%d ch%d card: %s  [%s]' % (n, c['chapter'], c['gr'], ', '.join(cnew)))
            for gr, en, ex in want[n]:
                manual, hints = extras(ex)
                fi, _, fch, fp = K.card_items(K.nfc(gr), known, c['chapter'], manual, hints, en)
                fnew = sorted(x for x in fi if x not in known)
                late = [x for x in fi if K.ch_of(x) > c['chapter'] and not x.startswith('S:')]
                if late:
                    fp = fp + ['too early: ' + ', '.join(late)]
                tag = 'OK  ' if not fp and fnew == cnew else ('DIFF' if not fp else 'PROB')
                print('   %s %s  [%s] %s' % (tag, gr, ', '.join(fnew), '; '.join(fp)))
        known |= {('L:' + l) for x in items if x.startswith('C:') for t in K.WORD.findall(x[2:])
                  for l, tg, s in (K.analyses(t) or []) if l in K.SYL and K.SYL[l] <= c['chapter'] and l not in K.FREE_LEMMAS}
        known |= set(items)
