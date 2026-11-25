"""More word-order features of the deck against real Attic prose and the books (aggregates only).

usage: style2.py UNITS.jsonl [ALL_RAW [PAGES_JSON]]   (venv python; ALL_RAW = the books' text, PAGES_JSON = its page
       index with chapters, for the books' aggregates and the chapter bands; both private)
Same method on every side: the deck's own analyser, no parser; a word counts as a noun, verb … only when every
analysis of it agrees. Sentences of LO–HI words (env STYLE_LO / STYLE_HI, default 4–9); STYLE_CLAUSE=1 counts clauses between high stops;
STYLE_CH=LO-HI limits the deck column to those chapters; UNITS '-' skips the corpus.
Features (Smyth § where he states the rule):
  first word       what a sentence starts with
  vocative         ὦ + vocative at the start, inside, at the end (§1285: usually inside; initial is emphatic)
  attributive adj  ὁ σοφὸς ἀνήρ / ὁ ἀνὴρ ὁ σοφός (§1154)
  genitive         ὁ τοῦ πατρὸς οἶκος (embedded) / ὁ οἶκος τοῦ πατρός / ὁ οἶκος ὁ τοῦ πατρός
  demonstrative    οὗτος ὁ ἀνήρ / ὁ ἀνὴρ οὗτος (§1171)
  negative         οὐ / μή right before the finite verb, or before another word (§2690)
  subject          article + noun in the nominative before / after the finite verb
  prep. phrase     before / after the finite verb
  enclitic pronoun με μοι μου σε σοι σου in second position or later (§1192)
  circ. participle a nominative participle before / after the finite verb
  particles        sentences with δέ, γάρ, οὖν, μέν, γε, δή, τε"""
import collections
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import config as P  # noqa: E402
import check2 as K  # noqa: E402

LO, HI = int(os.environ.get('STYLE_LO', 4)), int(os.environ.get('STYLE_HI', 9))
AUTH = ('Xen.', 'Lys.', 'Isoc.', 'Dem.', 'Pl.', 'Andoc.', 'Aeschin.', 'Isae.', 'Antiph.', 'Lycurg.')
ENCL = {'με', 'μοι', 'μου', 'σε', 'σοι', 'σου'}
PART = {'δε': 'δέ', 'γαρ': 'γάρ', 'ουν': 'οὖν', 'μεν': 'μέν', 'γε': 'γε', 'δη': 'δή', 'τε': 'τε'}
cache = {}


def an(tok):
    if tok not in cache:
        cache[tok] = K.analyses(tok) or []
    return cache[tok]


def only(a, test):
    return bool(a) and all(test(l, t) for l, t, s in a)


def is_art(a):
    """the article: the treebank also tags it as a pronoun (its old demonstrative use), so one article analysis is
    enough, and the case is taken from the article analyses"""
    return any(l == 'ὁ' and t[0] == 'l' for l, t, s in a)


def is_noun(a):
    return only(a, lambda l, t: t[0] == 'n')


def is_adj(a):
    return only(a, lambda l, t: t[0] == 'a')


def is_fin(a):
    return only(a, lambda l, t: t[0] == 'v' and t[4] in 'isom')


def case_of(a):
    cs = {t[7] for l, t, s in a if t[0] == 'l'} if is_art(a) else {t[7] for l, t, s in a}
    return cs.pop() if len(cs) == 1 else None


def agree(a, b):
    """some analysis of a and some of b share gender, number and case"""
    return any(x[2] == y[2] and x[6] == y[6] and x[7] == y[7] for _, x, _ in a for _, y, _ in b)


def first_kind(tok, a):
    b = K.bare(tok)
    if b in ('και', 'αλλα', 'ουδε', 'ουτε', 'η', 'ει', 'επει', 'ως', 'οτι', 'οτε', 'ινα', 'εαν', 'αλλ'):
        return 'conjunction'
    if b in ('ου', 'ουκ', 'ουχ', 'μη'):
        return 'negative'
    if b in ('τι', 'τισ', 'πωσ', 'που', 'ποι', 'ποτε', 'αρα', 'ποθεν', 'διατι'):
        return 'question word'
    if b == 'ω':
        return 'ὦ (vocative)'
    if is_art(a):
        return 'article'
    if is_fin(a):
        return 'finite verb'
    if is_noun(a):
        return 'noun'
    if only(a, lambda l, t: t[0] == 'v'):
        return 'participle / infinitive'
    if is_adj(a):
        return 'adjective'
    if only(a, lambda l, t: t[0] == 'r'):
        return 'preposition'
    if only(a, lambda l, t: t[0] == 'p'):
        return 'pronoun'
    if only(a, lambda l, t: t[0] == 'd'):
        return 'adverb'
    return 'other'


CLAUSE = os.environ.get('STYLE_CLAUSE') == '1'
STOP = re.compile(r'[·\u0387:]\s+|(?<=[αεηιουωνςάέήίόύώὰὲὴὶὸὺὼᾶῆῖῦῶἀἐἠἰὀὐὠἁἑἡἱὁὑὡἄἔἤἴὄὔὤἅἕἥἵὅὕὥἆἦἶὖὦἇἧἷὗὧ])’\s+')


def clauses(sentences):
    """STYLE_CLAUSE=1: count each clause between high stops (·, or ’ after a vowel, ν or ς in the books' OCR,
    where an elision mark cannot stand) as a sentence of its own"""
    for s in sentences:
        if CLAUSE:
            yield from (p for p in STOP.split(s) if p.strip())
        else:
            yield s


def stats(sentences):
    c = collections.Counter()
    for s in clauses(sentences):
        toks = [m.group(0) for m in K.WORD.finditer(K.nfc(s))]
        if not LO <= len(toks) <= HI:
            continue
        n = len(toks)
        c['sentences'] += 1
        al = [an(t) for t in toks]
        bt = [K.bare(t) for t in toks]
        c['first: ' + first_kind(toks[0], al[0])] += 1
        # vocative
        if 'ω' in bt:
            i = bt.index('ω')
            c['voc'] += 1
            c['voc start' if i == 0 else 'voc end' if i >= n - 2 else 'voc inside'] += 1
        fin = [i for i, a in enumerate(al) if is_fin(a)]
        v = fin[0] if len(fin) == 1 else None
        for i in range(n - 1):
            if is_art(al[i]):
                # attributive adjective
                if i + 2 < n and is_adj(al[i + 1]) and is_noun(al[i + 2]) and agree(al[i + 1], al[i + 2]):
                    c['attr'] += 1; c['attr ὁ σοφὸς ἀνήρ'] += 1
                if i + 3 < n and is_noun(al[i + 1]) and is_art(al[i + 2]) and is_adj(al[i + 3]) and agree(al[i + 1], al[i + 3]):
                    c['attr'] += 1; c['attr ὁ ἀνὴρ ὁ σοφός'] += 1
                # genitive inside a noun phrase
                if i + 3 < n and is_art(al[i + 1]) and is_noun(al[i + 2]) and case_of(al[i + 2]) == 'g' \
                        and is_noun(al[i + 3]) and case_of(al[i + 3]) != 'g':
                    c['gen'] += 1; c['gen embedded'] += 1
                if i + 3 < n and is_noun(al[i + 1]) and case_of(al[i + 1]) not in ('g', None) and is_art(al[i + 2]) \
                        and is_noun(al[i + 3]) and case_of(al[i + 3]) == 'g':
                    c['gen'] += 1; c['gen after the noun'] += 1
        for i, b in enumerate(bt):
            if b in ('ουτοσ', 'αυτη', 'τουτο', 'ουτοι', 'αυται', 'ταυτα', 'εκεινοσ', 'εκεινη', 'εκεινο', 'οδε', 'ηδε', 'τοδε'):
                if i + 2 < n and is_art(al[i + 1]) and is_noun(al[i + 2]):
                    c['dem'] += 1; c['dem before'] += 1
                elif i >= 2 and is_noun(al[i - 1]) and is_art(al[i - 2]):
                    c['dem'] += 1; c['dem after'] += 1
            if b in ('ου', 'ουκ', 'ουχ', 'μη') and i + 1 < n:
                c['neg'] += 1
                c['neg before the verb' if is_fin(al[i + 1]) else 'neg before another word'] += 1
            if toks[i] in ENCL:
                c['encl'] += 1
                c['encl second' if i == 1 else 'encl later'] += 1
            if b in PART:
                c['with ' + PART[b]] += 1
        c['words'] += n
        cop = [i for i, a in enumerate(al) if only(a, lambda l, t: l == 'εἰμί' and t[0] == 'v' and t[4] in 'isom')]
        if len(cop) == 1 and len(fin) == 1:
            i = cop[0]
            c['cop'] += 1
            c['cop first' if i == 0 else 'cop second' if i == 1 else 'cop last' if i == n - 1 else 'cop later'] += 1
        if not fin and not any(only(a, lambda l, t: t[0] == 'v') for a in al):
            c['no verb'] += 1
        # hyperbaton: an adjective (or attributive pronoun) and its noun with other words between them
        for i in range(n):
            if is_adj(al[i]) and not (i and is_art(al[i - 1])):
                for j in range(i + 2, min(n, i + 5)):
                    if is_noun(al[j]) and agree(al[i], al[j]) and not any(is_noun(al[k]) and agree(al[i], al[k]) for k in range(i + 1, j)):
                        if not any(is_art(al[k]) for k in range(i + 1, j)) and is_noun(al[i + 1]) is False:
                            c['hyperbaton'] += 1
                        break
                else:
                    continue
                break
        if v is not None:
            c['one verb'] += 1
            c['verb first' if v == 0 else 'verb last' if v == n - 1 else 'verb medial'] += 1
            for i in range(n):
                if only(al[i], lambda l, t: t[0] == 'd') and bt[i] not in ('ου', 'ουκ', 'ουχ', 'μη', 'ουδε', 'μηδε'):
                    c['adv'] += 1; c['adv before' if i < v else 'adv after'] += 1
                    break
            for i in range(n):
                if is_noun(al[i]) and case_of(al[i]) == 'd' and not (i and only(al[i - 1], lambda l, t: t[0] == 'r')) \
                        and not (i > 1 and is_art(al[i - 1]) and only(al[i - 2], lambda l, t: t[0] == 'r')):
                    c['dat'] += 1; c['dat before' if i < v else 'dat after'] += 1
                    break
            for i in range(n):
                if is_noun(al[i]) and case_of(al[i]) == 'a' and not (i and only(al[i - 1], lambda l, t: t[0] == 'r')) \
                        and not (i > 1 and is_art(al[i - 1]) and only(al[i - 2], lambda l, t: t[0] == 'r')):
                    c['obj'] += 1; c['obj before' if i < v else 'obj after'] += 1
                    d = (i and is_art(al[i - 1])) or (i > 1 and is_art(al[i - 2]) and is_adj(al[i - 1]))
                    k = 'objd' if d else 'obji'
                    c[k] += 1; c[k + (' before' if i < v else ' after')] += 1
                    break
            for i in range(n):
                if bt[i] in ('εισ', 'εσ', 'προσ') and i != v:
                    c['ppg'] += 1; c['ppg before' if i < v else 'ppg after'] += 1
                    break
            for i in range(n):
                if bt[i] in ('εν',) and i != v:
                    c['ppl'] += 1; c['ppl before' if i < v else 'ppl after'] += 1
                    break
            if only(al[v], lambda l, t: t[4] == 'm'):
                c['imp'] += 1
                c['imp first' if v == 0 or (v == 1 and bt[0] in ('ω', 'και', 'αλλα', 'αλλ', 'μη')) else 'imp later'] += 1
            for i in range(n):
                if only(al[i], lambda l, t: t[0] == 'v' and t[4] == 'n'):
                    c['inf'] += 1; c['inf before' if i < v else 'inf after'] += 1
                    break
            for i in range(n - 1):
                if is_art(al[i]) and case_of(al[i]) == 'n' and is_noun(al[i + 1]) and case_of(al[i + 1]) == 'n':
                    c['subj'] += 1; c['subj before' if i < v else 'subj after'] += 1
                    break
            for i in range(n):
                if only(al[i], lambda l, t: t[0] == 'r') and i != v:
                    c['pp'] += 1; c['pp before' if i < v else 'pp after'] += 1
                    break
            for i in range(n):
                if only(al[i], lambda l, t: t[0] == 'v' and t[4] == 'p' and t[7] == 'n'):
                    c['ptc'] += 1; c['ptc before' if i < v else 'ptc after'] += 1
                    break
    return c


def pct(c, k, base):
    return '%4.0f%%' % (100 * c[k] / c[base]) if c[base] else '   –'


ROWS = [('sentence shape', None), ('no verb', 'sentences'), ('hyperbaton', 'sentences'),
        ('one finite verb', None), ('verb first', 'one verb'), ('verb medial', 'one verb'), ('verb last', 'one verb'),
        ('εἰμί as the one verb', None), ('cop first', 'cop'), ('cop second', 'cop'), ('cop later', 'cop'), ('cop last', 'cop'),
        ('accusative noun (object)', None), ('obj before', 'obj'), ('obj after', 'obj'),
        ('  object with the article', None), ('objd before', 'objd'), ('objd after', 'objd'),
        ('  object without the article', None), ('obji before', 'obji'), ('obji after', 'obji'),
        ('εἰς / πρός phrase (goal)', None), ('ppg before', 'ppg'), ('ppg after', 'ppg'),
        ('ἐν phrase (place)', None), ('ppl before', 'ppl'), ('ppl after', 'ppl'),
        ('dative noun (no preposition)', None), ('dat before', 'dat'), ('dat after', 'dat'),
        ('adverb', None), ('adv before', 'adv'), ('adv after', 'adv'),
        ('infinitive', None), ('inf before', 'inf'), ('inf after', 'inf'),
        ('imperative (the one verb)', None), ('imp first', 'imp'), ('imp later', 'imp'),
        ('starts with', None), ('first: article', 'sentences'), ('first: noun', 'sentences'),
        ('first: finite verb', 'sentences'), ('first: conjunction', 'sentences'), ('first: adverb', 'sentences'),
        ('first: pronoun', 'sentences'), ('first: adjective', 'sentences'), ('first: participle / infinitive', 'sentences'),
        ('first: preposition', 'sentences'), ('first: negative', 'sentences'), ('first: question word', 'sentences'),
        ('first: ὦ (vocative)', 'sentences'),
        ('vocative (ὦ …)', None), ('voc start', 'voc'), ('voc inside', 'voc'), ('voc end', 'voc'),
        ('attributive adjective', None), ('attr ὁ σοφὸς ἀνήρ', 'attr'), ('attr ὁ ἀνὴρ ὁ σοφός', 'attr'),
        ('genitive in a noun phrase', None), ('gen embedded', 'gen'), ('gen after the noun', 'gen'),
        ('demonstrative', None), ('dem before', 'dem'), ('dem after', 'dem'),
        ('negative', None), ('neg before the verb', 'neg'), ('neg before another word', 'neg'),
        ('subject (article + noun, nom.)', None), ('subj before', 'subj'), ('subj after', 'subj'),
        ('prepositional phrase', None), ('pp before', 'pp'), ('pp after', 'pp'),
        ('nominative participle', None), ('ptc before', 'ptc'), ('ptc after', 'ptc'),
        ('enclitic pronoun', None), ('encl second', 'encl'), ('encl later', 'encl'),
        ('particles (share of sentences)', None)] + [('with ' + p, 'sentences') for p in PART.values()]


W = 12


def table(cols):
    names = list(cols)
    print()
    print('%-34s' % ('%d–%d words' % (LO, HI)) + ''.join('%*s' % (W, k) for k in names))
    print('%-34s' % 'sentences' + ''.join('%*d' % (W, cols[k]['sentences']) for k in names))
    print('%-34s' % 'words per sentence' + ''.join('%*.1f' % (W, cols[k]['words'] / max(cols[k]['sentences'], 1)) for k in names))
    print('%-34s' % 'one finite verb (count)' + ''.join('%*d' % (W, cols[k]['one verb']) for k in names))
    for j, (label, base) in enumerate(ROWS):
        if base is None:
            nb = ROWS[j + 1][1] if j + 1 < len(ROWS) else None
            print('%-34s' % label + (''.join('%*s' % (W, 'n=%d' % cols[k][nb]) for k in names) if nb and nb != 'sentences' else ''))
            continue
        print('  %-32s' % label.replace('attr ', '').replace('gen ', '').replace('dem ', '').replace('neg ', '')
              .replace('subj ', '').replace('pp ', '').replace('ptc ', '').replace('encl ', '').replace('first: ', '')
              .replace('voc ', '').replace('cop ', '').replace('obj ', '').replace('dat ', '')
              .replace('adv ', '').replace('inf ', '').replace('imp ', '')
              .replace('objd ', '').replace('obji ', '').replace('ppg ', '').replace('ppl ', '') + ''.join('%*s' % (W, pct(cols[k], label, base)) for k in names))



def main():
    global W
    cards, known, uses = K.run(P.sentence_paths(), quiet=True, show=False)
    CH = [int(x) for x in os.environ.get('STYLE_CH', '1-99').split('-')]
    cols = {'deck': stats(c['gr'] for c in cards if c['src'] == 'composed' and CH[0] <= c['chapter'] <= CH[-1])}
    if sys.argv[1] != '-':
        corp = []
        for line in open(sys.argv[1], encoding='utf-8'):
            u = json.loads(line)
            if u['kind'] == 'full' and u['src'].split()[0] in AUTH:
                corp.append(u['text'])
        cols['Attic prose'] = stats(corp)
    if len(sys.argv) > 2:
        raw = open(sys.argv[2], encoding='utf-8').read().split('\f')
        G = re.compile(r'[Ͱ-Ͽἀ-῿]')

        def sents(pages):
            for t in pages:
                t = re.sub(r'-\n\s*', '', t).replace('\n', ' ')
                for s in re.split(r'(?<=[.;;!])\s+|[«»“”]', t):
                    s = s.strip()
                    if s and not re.search(r'[A-Za-z0-9]', s) and len(G.findall(s)) > len(s) * 0.6:
                        yield s
        cols['Athenaze I'] = stats(sents(raw[29:610]))
        cols['Athenaze II'] = stats(sents(raw[621:1130]))
    table(cols)
    if len(sys.argv) > 3:      # by chapter band: the deck's composed cards and the books' readings (page index: pdf = raw + 1)
        pages = json.load(open(sys.argv[3], encoding='utf-8'))
        BANDS = ((1, 5), (6, 12), (13, 20), (21, 31))
        bc = {}
        for lo, hi in BANDS:
            bc['deck %d–%d' % (lo, hi)] = stats(c['gr'] for c in cards if c['src'] == 'composed' and lo <= c['chapter'] <= hi)
            bc['book %d–%d' % (lo, hi)] = stats(sents(raw[e['pdf'] - 1] for e in pages if e['sec'] == 'R' and lo <= e['ch'] <= hi))
        W = 11
        table(bc)


if __name__ == '__main__':
    main()
