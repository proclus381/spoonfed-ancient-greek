"""Class every syllabus noun, adjective and participle into its inflection scheme (project/schemes.py).
usage (from project/): ../.venv/bin/python ../work/phase3/paradigms/classify.py   → distribution + unclassified"""
import collections
import os
import sys

sys.path.insert(0, os.getcwd())
import check2 as K   # noqa: E402
import schemes as S  # noqa: E402

LF = collections.defaultdict(dict)
for f, al in K.GEN.items():
    for l, t in al:
        LF[l].setdefault(t[:9], f)
for f, al in K.EXTRA.items():
    for a in al:
        if len(a) == 2:
            LF[a[0]].setdefault(a[1][:9], f)


def Fn(l, g=None):
    def F(case, num):
        for t, f in LF[l].items():
            if t[0] == 'n' and t[2] == num and t[7] == case:
                return K.bare(f)
        return ''
    return F


dist = collections.defaultdict(list)
bad = []
for l, tags in LF.items():
    nt = [t for t in tags if t[0] == 'n']
    if nt and l not in K.SPECIFIC:
        t0 = nt[0]
        g = t0[6]
        d = K.decl(l, t0, tags[t0])
        sc = S.noun_scheme(Fn(l), d, g)
        (dist[sc].append(l) if sc else bad.append(('n', l, d, Fn(l)('n', 's'), Fn(l)('g', 's'))))
    at = [t for t in tags if t[0] == 'a']
    if at and l not in K.SPECIFIC:
        for deg in sorted({t[8] for t in at}):
            def F(case, num, gen, deg=deg):
                for t, f in tags.items():
                    if t[0] == 'a' and t[2] == num and t[7] == case and t[6] == gen and t[8] == deg:
                        return K.bare(f)
                return ''
            sc = S.adj_scheme(F, l, deg) if l not in K.IRREG_ADJ else 'Aοη'
            (dist[sc].append(l + deg) if sc else bad.append(('a' + deg, l, F('n', 's', 'm'), F('n', 's', 'f'),
                                                               F('g', 's', 'm'))))
    vt = {(t[3], t[5]) for t in tags if t[0] == 'v' and t[4] == 'p'}
    for tn, vc in vt:
        nm = next((f for t, f in tags.items() if t[0] == 'v' and t[4] == 'p' and t[3] == tn and t[5] == vc and
                   t[2] == 's' and t[6] == 'm' and t[7] == 'n'), '')
        nf = next((f for t, f in tags.items() if t[0] == 'v' and t[4] == 'p' and t[3] == tn and t[5] == vc and
                   t[2] == 's' and t[6] == 'f' and t[7] == 'n'), '')
        sc = S.ptc_scheme(K.bare(nm), K.bare(nf), vc, nm)
        (dist[sc].append('%s/%s%s' % (l, tn, vc)) if sc else bad.append(('ptc', l, tn + vc, nm, nf)))
for k in sorted(dist, key=lambda k: -len(dist[k])):
    print('%-6s %5d  %s' % (k, len(dist[k]), ' '.join(dist[k][:8])))
print('unclassified', len(bad))
for b in bad[:80]:
    print('  ', *b)
