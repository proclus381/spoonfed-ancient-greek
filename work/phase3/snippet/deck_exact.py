"""The snippet measures of style3.py for the deck, exactly: with the analysis the checker chose for each word.

usage: deck_exact.py [LO HI]        (venv python, repository root; chapters LO..HI, default all)
       DECK_LIST=1 also lists the cards with a stated article + noun subject (number, chapter, before/after)
Definitions as in tools/phase3/style3.py: 3rd-person clauses with one finite verb (not εἰμί) and whether a subject
is stated (a nominative noun, adjective, pronoun or article; a participle only after a nominative article);
position of a stated article + noun subject; sentences with a connective; present-tense predications without the
copula (a past or future copula cannot be left out, so those are not counted);
1st/2nd-person clauses with ἐγώ / σύ / ἡμεῖς / ὑμεῖς stated; vocative position. Sentences are cut at . ; ! and quotation marks, clauses at · : ; and commas."""
import collections
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.path.insert(0, os.path.join(ROOT, 'project'))
import config as P  # noqa: E402
import check2 as K  # noqa: E402

LO, HI = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (1, 99)
LIST = os.environ.get('DECK_LIST') == '1'     # print each card with a stated article + noun subject
PERS = {'ἐγώ', 'σύ', 'ἡμεῖς', 'ὑμεῖς'}
POSTCONN = {'δε', 'γαρ', 'ουν', 'μεν', 'τοινυν', 'μεντοι', 'δη', 'αρα'}
INITCONN = {'και', 'αλλα', 'αλλ', 'ουδε', 'ουτε', 'μηδε'}
SENT = re.compile(r'[.;;!«»“”]')
CLAUSE = re.compile(r'[··:;;,.!«»“”]')


def tags(c, i):
    ch = c['chosen'][i]
    if ch and ch[0] != 'chunk':
        return [ch]
    return [(l, t) for l, t, x in (K.analyses(c['toks'][i][2]) or [])]


def one(a, f):
    return bool(a) and all(f(l, t) for l, t in a)


def is_art(a):
    return any(l == 'ὁ' and t[0] == 'l' for l, t in a)


def case(a):
    cs = {t[7] for l, t in a if t[0] == 'l'} if is_art(a) else {t[7] for l, t in a}
    return cs.pop() if len(cs) == 1 else None


def groups(c, rx):
    out, cur = [], []
    for i, (a, b, t) in enumerate(c['toks']):
        if cur and rx.search(c['gr'][c['toks'][i - 1][1]:a]):
            out.append(cur)
            cur = []
        cur.append(i)
    if cur:
        out.append(cur)
    return out


def measure(cards):
    m = collections.Counter()
    for c in cards:
        for sent in groups(c, SENT):
            al = [tags(c, i) for i in sent]
            bt = [K.bare(c['toks'][i][2]) for i in sent]
            m['sentences'] += 1
            if any(b in POSTCONN for b in bt[:3]) or bt[0] in INITCONN:
                m['connected'] += 1
            art_n = [k for k, a in enumerate(al) if is_art(a) and case(a) == 'n']
            pred = [k for k, a in enumerate(al) if one(a, lambda l, t: t[0] == 'a' and t[7] == 'n') and
                    not (k and is_art(al[k - 1]))]
            fins = [k for k, a in enumerate(al) if any(t[0] == 'v' for l, t in a)]
            # only the present copula can be left out (Smyth §944): a past or future ἦν / ἔσται is not counted
            if art_n and pred and len(sent) <= 8 and all(any(l == 'εἰμί' and t[3] == 'p' and t[4] == 'i'
                                                             for l, t in al[k]) for k in fins):
                m['pred'] += 1
                m['pred no copula'] += not fins
            if 'ω' in bt:
                k = bt.index('ω')
                m['voc'] += 1
                m['voc ' + ('start' if k == 0 else 'end' if k >= len(bt) - 2 else 'inside')] += 1
        for seg in groups(c, re.compile(r'[·\u0387:;;.!«»“”]')):
            sb = [K.bare(c['toks'][i][2]) for i in seg]
            m['segments'] += 1
            m['seg connected'] += any(b in POSTCONN for b in sb[:3]) or sb[0] in INITCONN
        for cl in groups(c, CLAUSE):
            al = [tags(c, i) for i in cl]
            fin = [k for k, a in enumerate(al) if one(a, lambda l, t: t[0] == 'v' and t[4] in 'isom')]
            if len(fin) != 1:
                continue
            v = fin[0]
            ps = {t[1] for l, t in al[v]}
            if ps in ({'1'}, {'2'}):
                m['12p'] += 1
                m['12p pron'] += any(one(a, lambda l, t: l in PERS and t[7] == 'n') for a in al)
                continue
            if ps != {'3'} or any(l == 'εἰμί' for l, t in al[v]):
                continue
            m['3p'] += 1
            st = False
            for k, a in enumerate(al):
                if k == v:
                    continue
                if one(a, lambda l, t: t[0] in 'nalp' and t[7] == 'n') or \
                        (k and is_art(al[k - 1]) and case(al[k - 1]) == 'n' and
                         one(a, lambda l, t: t[0] == 'v' and t[4] == 'p' and t[7] == 'n')):
                    st = True
            m['3p stated'] += st
            # the same, but a neuter that could be accusative does not count as a subject of an active verb
            # (τὸ μάθημα μανθάνει: the checker may have chosen the nominative)
            act = all(t[5] == 'a' for l, t in al[v])
            st2 = False
            for k, a in enumerate(al):
                if k == v:
                    continue
                if one(a, lambda l, t: t[0] in 'nalp' and t[7] == 'n') or \
                        (k and is_art(al[k - 1]) and case(al[k - 1]) == 'n' and
                         one(a, lambda l, t: t[0] == 'v' and t[4] == 'p' and t[7] == 'n')):
                    if act and all(t[6] == 'n' for l, t in a) and \
                            any(t[7] == 'a' for l, t, x in (K.analyses(c['toks'][cl[k]][2]) or [])):
                        continue
                    st2 = True
            m['3p stated2'] += st2
            bcl = [K.bare(c['toks'][i][2]) for i in cl]
            for k in range(len(al) - 1):
                j = k + 2 if k + 2 < len(al) and bcl[k + 1] in POSTCONN else k + 1       # ὁ δὲ δοῦλος
                if is_art(al[k]) and case(al[k]) == 'n' and one(al[j], lambda l, t: t[0] == 'n') and \
                        case(al[j]) == 'n':
                    m['subj'] += 1
                    m['subj after'] += k > v
                    if LIST:
                        print('%s\t%d\t%s\t%s\t%s' % (c['n'], c['chapter'], 'after' if k > v else 'before',
                                                      c['gr'], ','.join(sorted(c['new']))))
                    break
    return m


def report(m, label='deck'):
    pc = lambda a, b: '%.0f%%' % (100 * m[a] / m[b]) if m[b] else '–'  # noqa: E731
    print('%s: %d sentences' % (label, m['sentences']))
    print('  3rd-person clauses %d: subject left out %s' % (m['3p'], '%.0f%%' % (100 - 100 * m['3p stated'] / m['3p'])
                                                           if m['3p'] else '–'))
    print('  … not counting neuters that could be objects of an active verb: subject left out %s' %
          ('%.0f%%' % (100 - 100 * m['3p stated2'] / m['3p']) if m['3p'] else '–'))
    print('  1st/2nd-person clauses %d: ἐγώ / σύ / ἡμεῖς / ὑμεῖς stated %s' % (m['12p'], pc('12p pron', '12p')))
    print('  stated article + noun subject after the verb: %s (of %d)' % (pc('subj after', 'subj'), m['subj']))
    print('  sentences with a connective: %s; segments between high stops: %s' % (pc('connected', 'sentences'),
                                                                               pc('seg connected', 'segments')))
    print('  present-tense predications without the copula: %s (of %d)' % (pc('pred no copula', 'pred'), m['pred']))
    print('  vocative: start %s, inside %s, end %s (of %d)' % (pc('voc start', 'voc'), pc('voc inside', 'voc'),
                                                              pc('voc end', 'voc'), m['voc']))


if __name__ == '__main__':
    cards, known, uses = K.run(P.sentence_paths(), quiet=True, show=False)
    report(measure([c for c in cards if c['src'] == 'composed' and LO <= c['chapter'] <= HI]),
           'deck ch. %d–%d' % (LO, HI))
