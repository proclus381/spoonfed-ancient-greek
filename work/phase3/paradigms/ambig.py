"""Cards whose new inflection cell sits on a form with another case reading (neuter nom./acc., nom./voc. pl.,
sg./pl. …): the checker took the cheapest reading, which may not be the sentence's.  Review list.
usage: ambig.py [FROM TO]     (repository root)"""
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
os.chdir(os.path.join(ROOT, 'project'))
sys.path.insert(0, os.getcwd())
import check2 as K  # noqa: E402

paths = sorted(os.path.join('sentences', f) for f in os.listdir('sentences') if re.match(r'ch\d\d\.txt$', f))
cards, known, uses = K.run(paths, quiet=True, show=False)
a, b = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (0, 10 ** 6)
for c in cards:
    if not a <= c['n'] <= b:
        continue
    for it in c['new']:
        if it.startswith(('L:', 'C:', 'X:', 'S:')) or not re.search(r':(nom|gen|dat|acc|voc)\.', it):
            continue
        for ti in c['items'][it]:
            tok = c['toks'][ti][2]
            ch = c['chosen'][ti]
            if not ch or not isinstance(ch[1], str):
                continue
            alts = {(t[7], t[2], t[6]) for l, t, s in (K.analyses(tok) or []) if l == ch[0] and len(t) > 7}
            if len(alts) > 1 and any(x[0] != ch[1][7] or x[1] != ch[1][2] for x in alts):
                if any(h for h in c['hints']):
                    hs = ' '.join('@%s' % h for h in c['hints'])
                else:
                    hs = ''
                print('%d\t%s\t%s\t%s\t%s\t%s' % (c['n'], it, tok, ''.join(ch[1][7] + ch[1][2] + ch[1][6]),
                                                  ' '.join(sorted(x[0] + x[1] + x[2] for x in alts)), c['gr'][:70] + ' ' + hs))
