"""Every grammar key the paradigm generator can produce, against the keys the deck teaches.

usage: catalog.py OUT.tsv        (venv python, from project/)
OUT: key, taught chapter (or -), example lemma, its chapter, example form. Keys come from check2.gkey applied to every
generated (lemma, tag, form): what a card could introduce with the syllabus as it is."""
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..', '..', '..')
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.path.insert(0, os.path.join(ROOT, 'project'))
import check2 as K  # noqa: E402

items = json.load(open(os.path.join(ROOT, 'work', 'tmp', 'items.json'), encoding='utf-8'))
taught = {}
for c in items:
    for it in c['new']:
        taught.setdefault(it, c['ch'])
best = {}
K.TRUST[0] = True
src = [(f, [(l, t) for l, t in lst]) for f, lst in K.GEN.items()]
src += [(f, [tuple(a) for a in al if len(a) == 2]) for f, al in K.EXTRA.items()]
for f, lst in src:
    for l, t in lst:
        try:
            k = K.gkey(l, t[:9], f)
        except Exception:
            continue
        ch = K.SYL.get(l, 99)
        for kk in (k, K.ptc_key(l, t[:9], f)):
            if kk and (kk not in best or ch < best[kk][1]):
                best[kk] = (l, ch, f)
with open(sys.argv[1], 'w', encoding='utf-8') as out:
    for k in sorted(best):
        l, ch, f = best[k]
        out.write('%s\t%s\t%s\t%s\t%s\n' % (k, taught.get(k, '-'), l, ch, f))
tot = len(best)
miss = [k for k in best if k not in taught]
print('producible keys %d, taught %d, never taught %d' % (tot, tot - len(miss), len(miss)))
by = collections.Counter('verb' if k.startswith('V') or any(k.startswith(v + ':') for v in ('δίδωμι', 'τίθημι', 'ἵημι', 'ἵστημι', 'δείκνυμι')) else
                         'noun/adj (class)' if k[:1] in '123' else 'specific word' for k in miss)
print(by)
fine = collections.Counter(k.split(':')[0] for k in miss if k.split(':')[0] in K.SCH.NOUN_SCHEMES or
                           k.split(':')[0] in K.SCH.ADJ_SCHEMES or k.split(':')[0] in K.SCH.PTC_SCHEMES)
print('untaught cells by scheme:', ' '.join('%s %d' % x for x in sorted(fine.items(), key=lambda x: -x[1])))
have = {k.split(':')[0] for k in best}
for tab in (K.SCH.NOUN_SCHEMES, K.SCH.ADJ_SCHEMES, K.SCH.PTC_SCHEMES):
    for sc, (sm, desc, ex) in tab.items():
        if sc not in have:
            print('scheme without a syllabus word: %s (%s %s, %s)' % (sc, sm, desc, ex))
