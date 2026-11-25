"""Subjects, connectives and verbless sentences: the deck against Attic prose and the Athenaze readings.

usage: style3.py UNITS.jsonl ALL_RAW PAGES_JSON      (venv python; the books' text and page index stay private,
       only aggregates are printed). STYLE_CH=LO-HI limits the deck; STYLE_DECK_ONLY=1 measures the deck alone.
Same analyser and method on every side (see style2.py). Sentences of LO–HI words (STYLE_LO / STYLE_HI, default
3–12), cut into clauses at punctuation; a clause with exactly one finite verb is measured:
  3rd person, not εἰμί   subject stated? strict: a word whose every analysis is a nominative (noun, adjective,
                         pronoun, article, participle); loose: a nominal word with any nominative analysis
                         (neuter nominative/accusative). The truth lies between the two.
  1st / 2nd person       is ἐγώ / σύ / ἡμεῖς / ὑμεῖς stated?
  subject position       article + noun in the nominative before / after the verb (when stated)
Per sentence:
  connective             a postpositive connective in the first three words (δέ γάρ οὖν μέν τοίνυν μέντοι δή ἄρα),
                         or the sentence starts with καί / ἀλλά / οὐδέ / οὔτε; otherwise asyndeton
  verbless sentence      no verb form at all; type: with ὦ, answer, exclamation, question, nominal predication
                         (a nominative adjective/noun with a nominative article phrase), other"""
import collections
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style2 as S2  # noqa: E402

K, P = S2.K, S2.P
LO, HI = int(os.environ.get('STYLE_LO', 3)), int(os.environ.get('STYLE_HI', 12))
an, only = S2.an, S2.only
POSTCONN = {'δε', 'γαρ', 'ουν', 'μεν', 'τοινυν', 'μεντοι', 'δη', 'αρα'}
INITCONN = {'και', 'αλλα', 'αλλ', 'ουδε', 'ουτε', 'μηδε'}
ANSWER = {'ναι', 'ου', 'ουκ', 'ουχ', 'πανυ', 'μαλιστα', 'ουδαμωσ', 'αληθη', 'ευ', 'καλωσ', 'πωσ', 'ισωσ', 'μαλα'}
EXCL = {'οιμοι', 'φευ', 'αιαι', 'ιου', 'ιδου', 'παπαι', 'ιω', 'ω'}
PERS = {'ἐγώ', 'σύ', 'ἡμεῖς', 'ὑμεῖς'}
CUT = re.compile(r'[··:;;,]\s*')


def nominal(l, t):
    return t[0] in 'nalp'


def stated(cal, v, strict=True):
    """a nominative nominal in the clause other than the verb; a participle counts only after a nominative article
    (ὁ τρέχων), since an anarthrous one (τρέχων πίπτει) agrees with an omitted subject"""
    test = (lambda a, f: only(a, f)) if strict else (lambda a, f: any(f(l, t) for l, t, x in a))
    for i, a in enumerate(cal):
        if i == v:
            continue
        if test(a, lambda l, t: nominal(l, t) and t[7] == 'n'):
            return True
        if i and S2.is_art(cal[i - 1]) and S2.case_of(cal[i - 1]) == 'n' and \
                test(a, lambda l, t: t[0] == 'v' and t[4] == 'p' and t[7] == 'n'):
            return True
    return False


def stats(sentences):
    c = collections.Counter()
    for s in sentences:
        toks_all = [m.group(0) for m in K.WORD.finditer(K.nfc(s))]
        if not LO <= len(toks_all) <= HI:
            continue
        c['sentences'] += 1
        bt = [K.bare(t) for t in toks_all]
        al = [an(t) for t in toks_all]
        # connectives
        if any(b in POSTCONN for b in bt[:3]):
            c['conn post'] += 1
        elif bt[0] in INITCONN:
            c['conn initial'] += 1
        else:
            c['asyndeton'] += 1
        # connectives at every high stop or full stop (does not depend on how a text punctuates)
        for seg in re.split(r'[·\u0387:;;.]\s*', K.nfc(s)):
            sb = [K.bare(m.group(0)) for m in K.WORD.finditer(seg)]
            if sb:
                c['segments'] += 1
                c['seg connected'] += any(b in POSTCONN for b in sb[:3]) or sb[0] in INITCONN
        # verbless
        if not any(any(t[0] == 'v' for l, t, x in a) for a in al):
            c['verbless'] += 1
            if 'ω' in bt:
                k = 'with ὦ'
            elif bt[0] in ANSWER:
                k = 'answer'
            elif bt[0] in EXCL:
                k = 'exclamation'
            elif ';' in s or ';' in s or bt[0] in ('τι', 'τισ', 'πωσ', 'που', 'ποι', 'ποθεν', 'ποτερον', 'ποσοσ'):
                k = 'question'
            elif any(only(a, lambda l, t: t[0] in 'an' and t[7] == 'n') for a in al) and \
                    any(only(a, lambda l, t: l == 'ὁ' and t[7] == 'n') or S2.is_art(a) for a in al):
                k = 'nominal predication'
            else:
                k = 'other'
            c['vl ' + k] += 1
        # predication: an article phrase in the nominative and a nominative adjective not right after an article
        art_n = [i for i, a in enumerate(al) if S2.is_art(a) and S2.case_of(a) == 'n']
        pred = [i for i, a in enumerate(al) if only(a, lambda l, t: t[0] == 'a' and t[7] == 'n')
                and not (i and S2.is_art(al[i - 1]))]
        fins = [i for i, a in enumerate(al) if any(t[0] == 'v' for l, t, x in a)]
        if art_n and pred and len(toks_all) <= 8 and not any(not any(l == 'εἰμί' for l, t, x in al[i]) for i in fins):
            c['pred'] += 1
            c['pred no copula' if not fins else 'pred copula'] += 1
        if 'ω' in bt:
            i = bt.index('ω')
            c['voc'] += 1
            c['voc start' if i == 0 else 'voc end' if i >= len(bt) - 2 else 'voc inside'] += 1
        # clauses
        for cl in CUT.split(K.nfc(s)):
            toks = [m.group(0) for m in K.WORD.finditer(cl)]
            if not toks:
                continue
            cal = [an(t) for t in toks]
            fin = [i for i, a in enumerate(cal) if only(a, lambda l, t: t[0] == 'v' and t[4] in 'isom')]
            if len(fin) != 1:
                continue
            v = fin[0]
            tags = {t for l, t, x in cal[v]}
            persons = {t[1] for t in tags}
            if len(persons) != 1:
                continue
            p = persons.pop()
            if p == '3':
                if any(l == 'εἰμί' for l, t, x in cal[v]):
                    continue
                c['3p'] += 1
                strict = stated(cal, v, True)
                loose = stated(cal, v, False)
                c['3p strict'] += strict
                c['3p loose'] += loose
                for i in range(len(toks) - 1):
                    j = i + 2 if i + 2 < len(toks) and K.bare(toks[i + 1]) in POSTCONN else i + 1   # ὁ δὲ δοῦλος
                    if S2.is_art(cal[i]) and S2.case_of(cal[i]) == 'n' and S2.is_noun(cal[j]) and \
                            S2.case_of(cal[j]) == 'n':
                        c['subj'] += 1
                        c['subj before' if i < v else 'subj after'] += 1
                        break
            elif p in '12':
                c['12p'] += 1
                c['12p pron'] += any(any(l in PERS and t[7] == 'n' for l, t, x in a) for a in cal)
    return c


def deck_sentences(cards, CH):
    """the composed cards' sentences, cut like the books' (at . ; ! and quotation marks)"""
    for c in cards:
        if c['src'] == 'composed' and CH[0] <= c['chapter'] <= CH[-1]:
            for s in re.split(r'(?<=[.;;!])\s+|[«»“”]', c['gr']):
                if s.strip():
                    yield s.strip()


def pct(c, k, b):
    return '%5.0f%%' % (100 * c[k] / c[b]) if c[b] else '    –'


def table(cols):
    names = list(cols)
    W = 13
    line = lambda lab, vals: print('%-44s' % lab + ''.join('%*s' % (W, v) for v in vals))  # noqa: E731
    line('%d–%d words' % (LO, HI), names)
    line('sentences', [cols[k]['sentences'] for k in names])
    print('3rd-person clause (one finite verb, not εἰμί)')
    line('  n', [cols[k]['3p'] for k in names])
    line('  subject stated (strict)', [pct(cols[k], '3p strict', '3p') for k in names])
    line('  subject stated (loose)', [pct(cols[k], '3p loose', '3p') for k in names])
    line('  subject left out (strict … loose)', ['%s–%s' % (pct(cols[k], '3p', '3p').strip() if False else
                                                           '%.0f' % (100 - 100 * cols[k]['3p loose'] / max(cols[k]['3p'], 1)),
                                                           '%.0f%%' % (100 - 100 * cols[k]['3p strict'] / max(cols[k]['3p'], 1)))
                                                  for k in names])
    print('subject (article + noun) when stated')
    line('  before the verb', [pct(cols[k], 'subj before', 'subj') for k in names])
    line('  after the verb', [pct(cols[k], 'subj after', 'subj') for k in names])
    print('1st/2nd-person clause')
    line('  n', [cols[k]['12p'] for k in names])
    line('  ἐγώ / σύ / ἡμεῖς / ὑμεῖς stated', [pct(cols[k], '12p pron', '12p') for k in names])
    print('connectives (share of sentences)')
    line('  postpositive in the first three words', [pct(cols[k], 'conn post', 'sentences') for k in names])
    line('  starts with καί / ἀλλά / οὐδέ …', [pct(cols[k], 'conn initial', 'sentences') for k in names])
    line('  asyndeton', [pct(cols[k], 'asyndeton', 'sentences') for k in names])
    line('  segments (between high stops) connected', [pct(cols[k], 'seg connected', 'segments') for k in names])
    print('predication (article phrase + adjective, nominative, up to 8 words)')
    line('  n', [cols[k]['pred'] for k in names])
    line('  without the copula', [pct(cols[k], 'pred no copula', 'pred') for k in names])
    print('vocative (ὦ …)')
    line('  n', [cols[k]['voc'] for k in names])
    for t in ('start', 'inside', 'end'):
        line('  ' + t, [pct(cols[k], 'voc ' + t, 'voc') for k in names])
    print('verbless sentences')
    line('  share of sentences', [pct(cols[k], 'verbless', 'sentences') for k in names])
    for t in ('with ὦ', 'answer', 'exclamation', 'question', 'nominal predication', 'other'):
        line('    ' + t, [pct(cols[k], 'vl ' + t, 'verbless') for k in names])


def main():
    cards, known, uses = K.run(P.sentence_paths(), quiet=True, show=False)
    CH = [int(x) for x in os.environ.get('STYLE_CH', '1-99').split('-')]
    cols = {'deck': stats(deck_sentences(cards, CH))}
    if os.environ.get('STYLE_DECK_ONLY'):
        table(cols)
        return
    corp = []
    for line in open(sys.argv[1], encoding='utf-8'):
        u = json.loads(line)
        if u['kind'] == 'full' and u['src'].split()[0] in S2.AUTH:
            corp.append(u['text'])
    cols['Attic prose'] = stats(corp)
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
    R = lambda lo, hi: [raw[e['pdf'] - 1] for e in pages if e['sec'] == 'R' and lo <= e['ch'] <= hi]  # noqa: E731
    cols['Ath. 1–5'] = stats(sents(R(1, 5)))
    cols['Ath. 6–16'] = stats(sents(R(6, 16)))
    cols['Ath. 17–31'] = stats(sents(R(17, 31)))
    table(cols)


if __name__ == '__main__':
    main()
