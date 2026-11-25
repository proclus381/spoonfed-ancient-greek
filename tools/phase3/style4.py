"""Word order by clause class: the deck against Attic prose and the Athenaze readings (docs/WORD_ORDER_PLAN.md §3A).

usage: style4.py UNITS.jsonl ALL_RAW PAGES_JSON     (venv python; the books' text stays private, only aggregates print)
       STYLE_CH=LO-HI limits the deck; STYLE_BANDS=1-10,11-16,17-32 gives one deck column per band.
Same analyser and sentence cutting as style2/style3 (sentences of 3–12 words, clauses cut at punctuation, one finite
verb, 3rd person, not εἰμί). Every clause gets a class:
  speech        the verb is a verb of saying or asking (λέγω, φημί, εἶπον, ἐρωτάω, ἀποκρίνομαι, ὑπολαμβάνω …)
  presentative  a verb of arriving, appearing, happening (ἥκω, ἔρχομαι, ἀφικνέομαι, πάρειμι, γίγνομαι, φαίνομαι …)
  other         any other verb
and, independently: subordinate (the clause opens with a subordinating word), contrast-marked (an article + noun in
the nominative followed by μέν or δέ, or ὁ δέ / ὁ μέν), with a noun object (a word whose every analysis is an
accusative noun).
Measured per class: subject stated (strict: a word whose every analysis is nominative), the position of a stated
article + noun subject, the One Lexical Argument share (a noun object and a noun subject in one clause), and the
position of a definite object (article + noun in the accusative): before the verb, and first in the clause with the
stated subject after the verb (O…V…S, which reads as a contrast). An article + noun subject not marked by μέν / δέ is
'given' when its lemma occurs as a noun in the two sentences before (deck: the two sentences before in card order)."""
import collections
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style2 as S2  # noqa: E402
import style3 as S3  # noqa: E402

K, P = S2.K, S2.P
an, only = S2.an, S2.only
SPEECH = {'λέγω', 'φημί', 'εἶπον', 'ἐρωτάω', 'ἔρομαι', 'ἀποκρίνομαι', 'ὑπολαμβάνω', 'βοάω', 'ἀγορεύω', 'φράζω'}
PRES = {'ἥκω', 'ἔρχομαι', 'ἀφικνέομαι', 'πάρειμι', 'γίγνομαι', 'φαίνομαι', 'παραγίγνομαι', 'ἐπιγίγνομαι',
        'προσέρχομαι', 'εἰσέρχομαι', 'ἀπέρχομαι', 'ἐξέρχομαι', 'ἔπειμι', 'ἐπέρχομαι', 'πάρεστι'}
SUBORD = {'επει', 'επειδη', 'οτε', 'οποτε', 'ωσ', 'ει', 'εαν', 'ην', 'αν', 'οτι', 'διοτι', 'ινα', 'οπωσ', 'εωσ',
          'πριν', 'μεχρι', 'εν', 'ωστε', 'καιπερ', 'οσ', 'η', 'ο', 'οι', 'αι', 'α', 'ου', 'ησ', 'ω', 'ων', 'οισ',
          'αισ', 'ον', 'ην', 'οσοσ', 'οιοσ', 'οπου', 'οπη', 'οποι', 'οθεν', 'ενθα', 'ηνικα'}
REL = {'ὅς', 'ὅστις', 'ὅσος', 'οἷος'}
POSTMD = {'μεν', 'δε'}


def clause_class(toks, cal, v):
    lem = {l for l, t, x in cal[v]}
    vc = 'speech' if lem & SPEECH else 'presentative' if lem & PRES else 'other'
    b0 = K.bare(toks[0])
    sub = b0 in SUBORD and (b0 not in ('η', 'ο', 'οι', 'αι', 'α', 'ου', 'ησ', 'ω', 'ων', 'οισ', 'αισ', 'ον', 'ην', 'εν')
                            or any(l in REL for l, t, x in cal[0]) or b0 == 'εν' and len(toks) > 1
                            and K.bare(toks[1]) == 'ω')
    return vc, sub


def noun_lemmas(toks):
    out = set()
    for t in toks:
        for l, tg, x in an(t) or []:
            if tg[0] == 'n':
                out.add(l)
    return out


def measure(sentences):
    c = collections.Counter()
    recent = collections.deque(maxlen=2)          # noun lemmas of the two sentences before: the givenness proxy
    for s in sentences:
        toks_all = [m.group(0) for m in K.WORD.finditer(K.nfc(s))]
        prev = set().union(*recent) if recent else set()
        recent.append(noun_lemmas(toks_all))
        if not S3.LO <= len(toks_all) <= S3.HI:
            continue
        for cl in S3.CUT.split(K.nfc(s)):
            toks = [m.group(0) for m in K.WORD.finditer(cl)]
            if not toks:
                continue
            cal = [an(t) for t in toks]
            fin = [i for i, a in enumerate(cal) if only(a, lambda l, t: t[0] == 'v' and t[4] in 'iso')]
            if len(fin) != 1:
                continue
            v = fin[0]
            persons = {t[1] for l, t, x in cal[v]}
            if persons != {'3'} or any(l == 'εἰμί' for l, t, x in cal[v]):
                continue
            vc, sub = clause_class(toks, cal, v)
            bt = [K.bare(t) for t in toks]
            # the stated article + noun subject, and whether μέν / δέ marks it
            subj, contrast, nsubj_given = None, False, None
            for i in range(len(toks) - 1):
                j = i + 2 if i + 2 < len(toks) and bt[i + 1] in S3.POSTCONN else i + 1
                if S2.is_art(cal[i]) and S2.case_of(cal[i]) == 'n' and j < len(toks) and S2.is_noun(cal[j]) and \
                        S2.case_of(cal[j]) == 'n':
                    subj = i
                    contrast = any(b in POSTMD for b in bt[i + 1:j + 2])
                    nsubj_given = bool({l for l, t, x in cal[j]} & prev)
                    break
                if S2.is_art(cal[i]) and S2.case_of(cal[i]) == 'n' and i + 1 < len(toks) and bt[i + 1] in POSTMD:
                    subj, contrast = i, True      # ὁ δέ / ὁ μέν as subject
                    break
            keys = ['all', ('sub' if sub else 'main') + ' ' + vc]
            if contrast:
                keys.append('μέν/δέ subject')
            nobj = [i for i, a in enumerate(cal) if only(a, lambda l, t: t[0] == 'n' and t[7] == 'a')]
            nsub = any(only(a, lambda l, t: t[0] == 'n' and t[7] == 'n') for a in cal)
            stated = S3.stated(cal, v, True)
            dobj = [i for i in range(len(toks) - 1) if S2.is_art(cal[i]) and S2.case_of(cal[i]) == 'a' and
                    S2.is_noun(cal[i + 1]) and S2.case_of(cal[i + 1]) == 'a']
            for k in keys:
                c[k, 'n'] += 1
                c[k, 'stated'] += stated
                if subj is not None:
                    c[k, 'subj'] += 1
                    c[k, 'subj after'] += subj > v
                if nsubj_given is not None and not contrast:     # article + noun subject, not marked by μέν / δέ
                    g = 'given' if nsubj_given else 'new'
                    c[k, 'ns ' + g] += 1
                    c[k, 'ns ' + g + ' after'] += subj > v
                if nobj:
                    c[k, 'nobj'] += 1
                    c[k, 'nobj+nsubj'] += nsub
                if dobj:
                    c[k, 'dobj'] += 1
                    c[k, 'dobj before'] += dobj[0] < v
                    if not stated:                          # no stated subject: the object may open the clause
                        c[k, 'dobj ns'] += 1
                        c[k, 'dobj ns before'] += dobj[0] < v
                        c[k, 'dobj ns first'] += dobj[0] == 0
                    if subj is not None:
                        c[k, 'dobj+subj'] += 1
                        c[k, 'O…V…S'] += dobj[0] == 0 and subj > v
    return c


ROWS = ['all', 'main other', 'main presentative', 'main speech', 'sub other', 'sub presentative', 'sub speech',
        'μέν/δέ subject']


def table(cols):
    names = list(cols)
    W = 12
    line = lambda lab, vals: print('%-40s' % lab + ''.join('%*s' % (W, v) for v in vals))  # noqa: E731
    pc = lambda c, a, b: '%.0f%% %d' % (100 * c[a] / c[b], c[b]) if c[b] else '–'  # noqa: E731
    line('(share, then its base n)', names)
    for r in ROWS:
        print(r)
        line('  3rd-person clauses', [cols[k][r, 'n'] for k in names])
        line('  subject left out (strict)', ['%.0f%%' % (100 - 100 * cols[k][r, 'stated'] / cols[k][r, 'n'])
                                             if cols[k][r, 'n'] else '–' for k in names])
        line('  art.+noun subject after the verb', [pc(cols[k], (r, 'subj after'), (r, 'subj')) for k in names])
        line('  … noun subject, no μέν/δέ, given: after', [pc(cols[k], (r, 'ns given after'), (r, 'ns given'))
                                                            for k in names])
        line('  … noun subject, no μέν/δέ, new: after', [pc(cols[k], (r, 'ns new after'), (r, 'ns new'))
                                                          for k in names])
        line('  noun object with a noun subject', [pc(cols[k], (r, 'nobj+nsubj'), (r, 'nobj')) for k in names])
        line('  definite object before the verb', [pc(cols[k], (r, 'dobj before'), (r, 'dobj')) for k in names])
        line('  definite object, no subject: before verb', [pc(cols[k], (r, 'dobj ns before'), (r, 'dobj ns'))
                                                             for k in names])
        line('  … opening the clause', [pc(cols[k], (r, 'dobj ns first'), (r, 'dobj ns')) for k in names])
        line('  … first, subject after the verb', [pc(cols[k], (r, 'O…V…S'), (r, 'dobj+subj')) for k in names])


def main():
    cards, known, uses = K.run(P.sentence_paths(), quiet=True, show=False)
    cols = {}
    for band in os.environ.get('STYLE_BANDS', os.environ.get('STYLE_CH', '1-99')).split(','):
        CH = [int(x) for x in band.split('-')]
        cols['deck ' + band] = measure(S3.deck_sentences(cards, CH))
    if sys.argv[1] != '-':
        corp = [json.loads(l) for l in open(sys.argv[1], encoding='utf-8')]
        cols['Attic prose'] = measure(u['text'] for u in corp if u['kind'] == 'full' and u['src'].split()[0] in S2.AUTH)
        raw = open(sys.argv[2], encoding='utf-8').read().split('\f')
        pages = json.load(open(sys.argv[3], encoding='utf-8'))
        G = re.compile(r'[Ͱ-Ͽἀ-῿]')

        def sents(pp):
            for t in pp:
                t = re.sub(r'-\n\s*', '', t).replace('\n', ' ')
                for s in re.split(r'(?<=[.;;!])\s+|[«»“”]', t):
                    s = s.strip()
                    if s and not re.search(r'[A-Za-z0-9]', s) and len(G.findall(s)) > len(s) * 0.6:
                        yield s
        cols['Athenaze'] = measure(sents(raw[e['pdf'] - 1] for e in pages if e['sec'] == 'R' and 1 <= e['ch'] <= 31))
    table(cols)


if __name__ == '__main__':
    main()
