"""Propose word-order rewrites of composed cards by the rules of docs/WORD_ORDER.md §2 (deterministic; every
proposal is read before it is applied).

usage: propose.py LO HI OUT.tsv        (venv python, from the repository root; chapters LO..HI)
OUT: n, chapter, rule, old Greek, new Greek, English, new items, note. Rows with rule 'manual' are verb- or
copula-final clauses the proposer could not segment safely (participles, enclitics, particles, elision …): they
are listed for reading by hand, with no proposal.

Per clause (between punctuation marks), with the checker's chosen analyses:
  phrases   article + modifiers + noun (+ genitive / αὐτοῦ), preposition + phrase, anarthrous noun + adjective,
            pronoun, adverb, οὐ/μή attached to what follows, a set phrase (C: chunk) as one block.
  focus     the phrase holding the card's new item.
  copula    S PRED ἐστί -> S ἐστι PRED (item on S, on the copula, or elsewhere)  | PRED ἐστιν S (item on PRED)
            anarthrous subject + place phrase -> PLACE ἐστιν S (existential)
            evaluative predicate -> also the copula-less PRED S as an alternative (note column)
  verb      S X… V: given phrases (with the article, names, αὐτόν …) not holding the item move after the verb;
            adverbs, negatives, anarthrous phrases and ἐν-phrases (settings) stay before it; the focus phrase
            stays right before the verb.  Thetic verbs (appearance, arrival, weather, sudden events): S V -> V S.
Accents are recomputed for the new neighbours: final acute/grave, enclitic ἐστί/εἰσί after oxytone, paroxytone,
proparoxytone and properispomenon words, the extra accent before an enclitic removed when it no longer applies;
movable ν before vowels and at a pause."""
import os
import re
import sys
import unicodedata as ud

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.path.insert(0, os.path.join(ROOT, 'project'))
import config as P  # noqa: E402
import check2 as K  # noqa: E402

if __name__ == '__main__':
    LO, HI, OUT = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
ACUTE, GRAVE, CIRC, DIAER = '́', '̀', '͂', '̈'
VOWELS = set('αεηιουω')
DIPH = {'αι', 'ει', 'οι', 'υι', 'αυ', 'ευ', 'ηυ', 'ου'}
COP = {'εστι', 'εστιν', 'εισι', 'εισιν', 'εσμεν', 'εστε', 'ειμι'}
ENCL_PRON = {'με', 'μοι', 'μου', 'σε', 'σοι', 'σου'}
ENCL_UNACC = {'τισ', 'τι', 'τινα', 'τινοσ', 'τινι', 'τινεσ', 'τινασ', 'τινων', 'τισι', 'τισιν', 'ποτε', 'πω', 'που',
              'πωσ', 'πη', 'ποθεν', 'γε', 'τε', 'τοι', 'περ'}
ENCL_ALWAYS = {'φημι', 'φησι', 'φησιν', 'φασι', 'φασιν'}


def enclitic(tok):
    b = K.bare(tok)
    return b in ENCL_PRON or b in ENCL_ALWAYS or (b in ENCL_UNACC and kind(tok) is None)


POSTPOS = {'δε', 'γαρ', 'ουν', 'μεν', 'δη', 'αν', 'μην', 'τοινυν', 'αρα', 'δητα', 'γουν'}
THETIC = {'φαίνομαι', 'ἥκω', 'πάρειμι', 'ἀφικνέομαι', 'γίγνομαι', 'πίπτω', 'καίομαι', 'φλέγω', 'ὕω', 'βροντάω',
          'ἔρχομαι', 'ἐπέρχομαι', 'προσέρχομαι', 'ἀνατέλλω', 'καταδύνω', 'δύω', 'ἐπιγίγνομαι', 'συμβαίνω',
          'ἐπιπίπτω', 'καταπίπτω', 'πνέω', 'σαλπίζω', 'ψοφέω', 'ἐπιφαίνομαι', 'προσχωρέω', 'ἐπανέρχομαι',
          'ἐξέρχομαι', 'εἰσέρχομαι', 'ἀπέρχομαι', 'πάρειμι2', 'ἐπιτέλλω', 'σείω', 'βρέχω', 'ἀστράπτω'}
EVAL = {'καλός', 'κακός', 'χαλεπός', 'δεινός', 'ἄξιος', 'δῆλος', 'ἀληθής', 'αἰσχρός', 'ἄριστος', 'κάλλιστος',
        'ἡδύς', 'δυνατός', 'ἀδύνατος', 'ἕτοιμος', 'πρόθυμος', 'δίκαιος', 'ἄδικος', 'θαυμαστός', 'φοβερός',
        'ἄθλιος', 'μακάριος', 'εὐδαίμων', 'ῥᾴδιος', 'ἄτοπος', 'αἴτιος', 'κατάρατος', 'τλήμων', 'μῶρος', 'ἀνόητος',
        'σοφός', 'ἄφρων', 'φίλος', 'ἐχθρός', 'βέλτιστος', 'χρηστός', 'πονηρός', 'ἀγαθός', 'οἰκτρός', 'ἀργός'}
SETTING_PREP = {'ἐν'}
GIVEN_PRON = {'αὐτός'}


# ------------------------------------------------------------------ accents
def nfd(s):
    return ud.normalize('NFD', s)


def nfc(s):
    return ud.normalize('NFC', s)


def letters(w):
    """[(base letter, [marks])] of an NFD word"""
    out = []
    for ch in nfd(w):
        if ud.combining(ch) and out:
            out[-1][1].append(ch)
        else:
            out.append([ch, []])
    return out


def syllables(L):
    """indices of the letter that carries the nucleus accent, one per syllable (diphthongs: second vowel)"""
    nuc, i = [], 0
    while i < len(L):
        b = L[i][0].lower()
        if b in VOWELS:
            if i + 1 < len(L) and (b + L[i + 1][0].lower()) in DIPH and DIAER not in L[i + 1][1] \
                    and not any(m in (ACUTE, GRAVE, CIRC) for m in L[i][1]):
                nuc.append(i + 1)
                i += 2
                continue
            nuc.append(i)
        i += 1
    return nuc


def accent_info(w):
    """-> list of (syllable from the end, mark)"""
    L = letters(w)
    nuc = syllables(L)
    out = []
    for k, i in enumerate(nuc):
        for m in L[i][1]:
            if m in (ACUTE, GRAVE, CIRC):
                out.append((len(nuc) - k, m))
    return out


def kind(w):
    a = [x for x in accent_info(w)]
    if not a:
        return None
    pos, m = max(a)                       # the word's own accent is the leftmost one
    if pos == 1:
        return 'peri' if m == CIRC else 'oxy'
    if pos == 2:
        return 'properi' if m == CIRC else 'paroxy'
    return 'proparoxy'


def set_marks(w, fn):
    L = letters(w)
    nuc = syllables(L)
    fn(L, nuc)
    return nfc(''.join(b + ''.join(ms) for b, ms in L))


def final_mark(w, mark):
    """oxytone word: final acute/grave -> mark"""
    def fn(L, nuc):
        i = nuc[-1]
        L[i][1] = [mark if m in (ACUTE, GRAVE) else m for m in L[i][1]]
    return set_marks(w, fn)


def drop_extra(w):
    """remove an enclitic-induced second accent on the final syllable"""
    a = accent_info(w)
    if len(a) < 2:
        return w

    def fn(L, nuc):
        i = nuc[-1]
        L[i][1] = [m for m in L[i][1] if m not in (ACUTE, GRAVE)]
    return set_marks(w, fn)


def add_extra(w):
    def fn(L, nuc):
        i = nuc[-1]
        if not any(m in (ACUTE, GRAVE, CIRC) for m in L[i][1]):
            L[i][1].append(ACUTE)
    return set_marks(w, fn)


def strip_acc(w):
    def fn(L, nuc):
        for b in L:
            b[1] = [m for m in b[1] if m not in (ACUTE, GRAVE, CIRC)]
    return set_marks(w, fn)


def starts_vowel(w):
    return nfd(w)[0].lower() in VOWELS


def movable_nu(w, tag, nxt):
    """add/remove movable ν for the following word (None = pause)"""
    b = K.bare(w)
    mov = (b.endswith(('σι', 'σιν')) and bool(tag) and (tag[0] == 'v' or (tag[0] in 'na' and tag[7] == 'd' and
                                                                        tag[2] == 'p'))) \
        or (tag and tag[0] == 'v' and tag[1] == '3' and tag[2] == 's'
                                         and tag[3].lower() in 'iarlp' and b.endswith(('ε', 'εν')) and tag[4] == 'i')
    if b in COP:
        mov = b.startswith(('εστι', 'εισι'))
    elif b.endswith(('εστι', 'εστιν')) and tag and tag[0] == 'v':
        mov = True
    if not mov:
        return w
    want = nxt is None or starts_vowel(nxt)
    has = w.endswith('ν')
    if want and not has:
        return w + 'ν'
    if not want and has:
        return w[:-1]
    return w


def copula_form(base, prev, nxt):
    """the enclitic copula after prev (already accent-fixed), before nxt (None = pause)"""
    b = strip_acc(base)
    k = kind(prev)
    if k == 'paroxy':
        b = add_extra(b)                  # λίθος ἐστί(ν)
        if nxt is not None:
            b = final_mark(b, GRAVE)
    return b


def render(seq):
    """seq: [(word, tag, is_cop)] of one clause in the new order -> words with accents and ν fixed"""
    words = [w for w, t, c in seq]
    out = list(words)
    for i, (w, t, c) in enumerate(seq):
        nxt = seq[i + 1] if i + 1 < len(seq) else None
        if c:
            continue
        x = drop_extra(w)
        if nxt is not None and nxt[2]:                 # an enclitic copula follows
            k = kind(x)
            if k in ('proparoxy', 'properi'):
                x = add_extra(x)
            elif k == 'oxy':
                x = final_mark(x, ACUTE)
        elif kind(x) == 'oxy' and K.bare(x) not in ('τισ', 'τι'):     # interrogative τίς / τί keep the acute
            x = final_mark(x, GRAVE if nxt is not None else ACUTE)
        x = movable_nu(x, t, nxt[0] if nxt else None)
        out[i] = x
    for i, (w, t, c) in enumerate(seq):
        if c:
            nxt = out[i + 1] if i + 1 < len(seq) else None
            out[i] = movable_nu(copula_form(w, out[i - 1], nxt), t, nxt)
    return out


# ------------------------------------------------------------------ phrases
def tk(ch):
    if ch is None:
        return None
    if ch[0] == 'chunk':
        return 'chunk'
    lem, tag = ch
    if lem == 'ὁ' and tag[0] == 'l':
        return 'art'
    if tag[0] == 'v':
        return 'fin' if tag[4] in 'isom' else ('ptc' if tag[4] == 'p' else 'inf')
    return {'n': 'noun', 'a': 'adj', 'r': 'prep', 'd': 'adv', 'p': 'pron', 'm': 'num', 'c': 'conj', 'g': 'part',
            'i': 'excl', 'e': 'excl'}.get(tag[0], 'other')


class Phrase:
    def __init__(self, idx, typ, case=None):
        self.idx, self.typ, self.case = idx, typ, case

    def __repr__(self):
        return '%s%s' % (self.typ, self.idx)


def phrases(ix, chosen, toks):
    """ix: token indices of one clause -> [Phrase] or None when the clause is not safe to reorder"""
    out, j = [], 0
    ks = [tk(chosen[i]) for i in ix]
    bt = [K.bare(toks[i][2]) for i in ix]
    neg = None
    while j < len(ix):
        i, k = ix[j], ks[j]
        if k is None or k in ('ptc', 'inf', 'part', 'other') or bt[j] in POSTPOS or enclitic(toks[i][2]) \
                or '᾽' in toks[i][2] or '\'' in toks[i][2]:
            return None
        if bt[j] in ('ου', 'ουκ', 'ουχ', 'μη'):
            neg = i
            j += 1
            continue
        start = j
        if k == 'chunk':
            item = chosen[i][1]
            while j < len(ix) and ks[j] == 'chunk' and chosen[ix[j]][1] == item:
                j += 1
            typ = 'pp' if tk(chosen[ix[start]]) == 'prep' or K.bare(toks[ix[start]][2]) in ('εν', 'εισ', 'εκ', 'προσ',
                                                                                          'απο', 'επι', 'μετα', 'υπο',
                                                                                          'δια', 'κατα', 'παρα') \
                else 'chunk'
            ph = Phrase([ix[x] for x in range(start, j)], typ)
        elif k == 'art':
            j = np_end(ix, ks, chosen, j)
            if j is None:
                return None
            ph = Phrase([ix[x] for x in range(start, j)], 'np', chosen[i][1][7])
        elif k == 'prep':
            j += 1
            if j + 1 < len(ix) and ks[j] in ('pron', 'adj') and ks[j + 1] == 'art':     # ἐν ταύταις ταῖς ἡμέραις
                j += 1
            if j < len(ix) and ks[j] == 'art':
                j = np_end(ix, ks, chosen, j)
                if j is None:
                    return None
            else:
                while j < len(ix) and ks[j] in ('noun', 'adj', 'pron', 'num'):
                    j += 1
            if j == start + 1:
                return None
            ph = Phrase([ix[x] for x in range(start, j)], 'pp')
            ph.prep = chosen[i][0]
            ph.art = any(ks[x] == 'art' for x in range(start, j))
        elif k in ('noun', 'adj', 'num'):
            c = chosen[i][1][7]
            while j < len(ix) and ks[j] in ('noun', 'adj', 'num') and chosen[ix[j]][1][7] == c:
                j += 1
            ph = Phrase([ix[x] for x in range(start, j)], 'npi' if any(ks[x] == 'noun' for x in range(start, j))
                        else 'adj', c)
            ph.name = toks[i][2][:1].isupper() and j - start == 1 and ks[start] == 'noun' and start > 0
        elif k == 'pron':
            if j + 1 < len(ix) and ks[j + 1] == 'art':      # οὗτος ὁ ἀνήρ
                e = np_end(ix, ks, chosen, j + 1)
                if e is None:
                    return None
                j = e
                ph = Phrase([ix[x] for x in range(start, j)], 'np', chosen[i][1][7])
            else:
                j += 1
                ph = Phrase([i], 'pron', chosen[i][1][7])
                ph.lemma = chosen[i][0]
        elif k == 'fin':
            j += 1
            ph = Phrase([i], 'V')
            ph.lemma, ph.tag = chosen[i]
        elif k in ('adv', 'conj', 'excl'):
            j += 1
            ph = Phrase([i], k)
        else:
            return None
        if neg is not None:
            ph.idx = [neg] + ph.idx
            ph.neg = True
            neg = None
        out.append(ph)
    if neg is not None:
        return None
    # keep together: a genitive phrase after a nominal one (partitive, possessive: πολλοὶ τῶν πολιτῶν,
    # τὸ ἥμισυ τοῦ σίτου), and πᾶς / ὅλος + article phrase (πάντα τὸν σῖτον)
    merged = []
    for ph in out:
        prev = merged[-1] if merged else None
        if prev is not None and ph.typ == 'np' and ph.case == 'g' and prev.typ in ('npi', 'adj', 'pron', 'chunk', 'np'):
            prev.idx += ph.idx
            continue
        if prev is not None and ph.typ == 'np' and prev.typ in ('npi', 'adj') and \
                chosen[prev.idx[-1]] and chosen[prev.idx[-1]][0] in ('πᾶς', 'ἅπας', 'ὅλος'):
            prev.idx += ph.idx
            prev.typ, prev.case = 'np', ph.case
            continue
        merged.append(ph)
    return merged


def np_end(ix, ks, chosen, j):
    """article at j: -> index after the noun phrase (article, modifiers, head, genitive / αὐτοῦ)"""
    art_case = chosen[ix[j]][1][7]
    j += 1
    while j < len(ix) and (ks[j] in ('adj', 'num', 'adv') or (ks[j] == 'pron' and chosen[ix[j]][0] == 'αὐτός' and
                                                            j + 1 < len(ix) and ks[j + 1] == 'noun')) \
            and not (ks[j] == 'adv' and j + 1 < len(ix) and ks[j + 1] == 'fin'):
        j += 1                                         # modifiers, attributive αὐτός (ἡ αὐτὴ γνώμη)
    if j < len(ix) and ks[j] == 'art':                 # ὁ τοῦ πατρὸς οἶκος
        g = np_end(ix, ks, chosen, j)
        if g is None:
            return None
        j = g
    if j < len(ix) and ks[j] in ('noun', 'pron') and (chosen[ix[j]][1][7] == art_case or
                                                    {chosen[ix[j]][1][7], art_case} <= {'n', 'a', 'v'}):
        j += 1
    elif j < len(ix) and ks[j - 1] in ('adj', 'num'):
        pass                                           # substantival adjective (οἱ ἄλλοι)
    else:
        return None
    if j < len(ix) and ks[j] == 'art' and chosen[ix[j]][1][7] == 'g':     # ὁ οἶκος τοῦ πατρός
        g = np_end(ix, ks, chosen, j)
        if g is None:
            return None
        j = g
    elif j < len(ix) and ks[j] == 'art' and chosen[ix[j]][1][7] == art_case and j + 1 < len(ix) and ks[j + 1] == 'adj':
        j += 2                                         # ὁ ἀνὴρ ὁ σοφός
    if j < len(ix) and ks[j] == 'pron' and chosen[ix[j]][1][7] == 'g' and chosen[ix[j]][0] in ('αὐτός',):
        j += 1                                         # ὁ δοῦλος αὐτοῦ
    return j


def given(ph):
    if ph.typ == 'np' and ph.case in ('a', 'd', 'g'):
        return True
    if ph.typ == 'pp' and getattr(ph, 'art', False) and ph.prep not in SETTING_PREP:
        return True
    if ph.typ == 'pron' and getattr(ph, 'lemma', '') in GIVEN_PRON and ph.case in ('a', 'd', 'g'):
        return True
    if ph.typ == 'npi' and getattr(ph, 'name', False) and ph.case in ('a', 'd'):
        return True
    return False


# ------------------------------------------------------------------ rules
def propose(c):
    toks, chosen = c['toks'], c['chosen']
    gr = c['gr']
    itoks = set()
    for it in c['new']:
        itoks |= set(c['items'].get(it, []))
    # clauses
    bounds, cur = [], [0]
    for i in range(1, len(toks)):
        gap = gr[toks[i - 1][1]:toks[i][0]]
        if gap.strip():
            bounds.append(cur)
            cur = [i]
        else:
            cur.append(i)
    bounds.append(cur)
    slot = {}                                  # position -> new word
    rules, notes, manual = [], [], False
    for ix in bounds:
        res = clause(ix, toks, chosen, itoks, c)
        if res is None:
            continue
        if res == 'manual':
            manual = True
            continue
        newix, rule, note, copidx = res
        if newix == ix:
            continue
        cap = toks[ix[0]][2][:1].isupper() and not is_name(chosen[ix[0]])
        seq = []
        for i in newix:
            w = toks[i][2]
            if cap and i == ix[0]:
                w = w[:1].lower() + w[1:]
            tag = chosen[i][1] if chosen[i] and chosen[i][0] != 'chunk' else None
            seq.append((w, tag, i in copidx))
        words = render(seq)
        if cap:
            words[0] = words[0][:1].title() + words[0][1:]
        for k, pos in enumerate(ix):
            slot[pos] = words[k]
        rules.append(rule)
        if note:
            notes.append(note)
    if not rules:
        return ('manual', None, '') if manual else None
    out, last = [], 0
    for pos, (a, b, t) in enumerate(toks):
        out.append(gr[last:a])
        out.append(slot.get(pos, t))
        last = b
    out.append(gr[last:])
    return ('+'.join(rules), ''.join(out), '; '.join(notes))


def is_name(ch):
    return bool(ch) and ch[0] != 'chunk' and ch[0][:1].isupper()


def clause(ix, toks, chosen, itoks, c):
    """-> None (nothing to do) | 'manual' | (new order of ix, rule, note, copula token indices)"""
    fins = [i for i in ix if tk(chosen[i]) == 'fin']
    if len(fins) != 1:
        return None
    v = fins[0]
    if v != ix[-1]:
        return None                                      # not verb-final: leave
    if len(ix) < 3:
        return None
    phs = phrases(ix, chosen, toks)
    if phs is None:
        return 'manual'
    # fixed head: conjunctions, exclamations, setting adverbs at the start
    head = []
    while phs and phs[0].typ in ('conj', 'excl'):
        head.append(phs.pop(0))
    V = phs[-1]
    body = phs[:-1]
    if not body:
        return None
    foc = [p for p in body if set(p.idx) & itoks]
    vfoc = bool(set(V.idx) & itoks)
    flat = lambda ps: [i for p in ps for i in p.idx]  # noqa: E731
    is_cop = V.lemma == 'εἰμί' and V.tag[4] == 'i' and not getattr(V, 'neg', False)
    encl = {i for i in V.idx if K.bare(toks[i][2]) in COP}     # ἦν, ἦσαν … are not enclitic
    if is_cop:
        if len(body) != 2:
            return 'manual' if len(body) > 2 else None
        S, PR = body
        if S.typ == 'np' and S.case == 'n':
            if PR.typ == 'pp' and not getattr(PR, 'neg', False):
                return (flat(head) + S.idx + V.idx + PR.idx, 'copula-second', '', encl)
            if set(PR.idx) & itoks or getattr(PR, 'neg', False):     # a negated predicate leads: οὐ μακρός ἐστιν ὁ …
                note = ''
                lem = chosen[PR.idx[-1]][0] if chosen[PR.idx[-1]] and chosen[PR.idx[-1]][0] != 'chunk' else ''
                if lem in EVAL and not vfoc:
                    note = 'alt no-copula'
                return (flat(head) + PR.idx + V.idx + S.idx, 'given-subject', note, encl)
            return (flat(head) + S.idx + V.idx + PR.idx, 'copula-second', '', encl)
        if S.typ == 'pp' and PR.typ in ('npi',) and PR.case == 'n':          # existential
            return (flat(head) + S.idx + V.idx + PR.idx, 'thetic', 'existential', encl)
        return None
    # ordinary verb
    lead = []                                            # the clause's frame: initial adverbs, phrases, set phrases
    b = list(body)
    while b and b[0].typ in ('adv', 'pp', 'chunk'):
        lead.append(b.pop(0))
    nom = [k for k, p in enumerate(b) if p.typ in ('np', 'npi', 'pron') and p.case == 'n']
    if nom and nom[0] > 0:                               # what precedes the subject is the frame (time, topic)
        lead += b[:nom[0]]
        b = b[nom[0]:]
    S = b[0] if b and b[0].typ in ('np', 'npi', 'pron') and b[0].case == 'n' else None
    rest = b[1:] if S else b
    if any(p.typ in ('conj', 'excl') for p in b) or any(K.bare(toks[i][2]) in ('ωσπερ', 'ωσ', 'και', 'αλλα', 'ουτε',
                                                                               'ουδε', 'μονον') for p in b for i in p.idx):
        return 'manual'                                  # coordination or comparison inside the clause
    for p in rest:                                       # after a subject, a neuter nominative/accusative is the object
        if S is not None and p.typ == 'np' and p.case in ('n', 'v') and chosen[p.idx[0]][1][6] == 'n':
            p.case = 'a'
    if S is not None and V.lemma in THETIC and not rest and not getattr(V, 'neg', False) \
            and not (set(S.idx) & itoks and not vfoc) and S.typ == 'np':
        return (flat(head) + flat(lead) + V.idx + S.idx, 'thetic', 'review: thetic?', set())
    if not rest:
        return None
    focus_j = [k for k, p in enumerate(rest) if set(p.idx) & itoks]
    move, stay = [], []
    for k, p in enumerate(rest):
        if k in focus_j:
            stay.append(p)
        elif given(p):
            move.append(p)
        else:
            stay.append(p)
    if not move:
        return None
    if S is not None and set(S.idx) & itoks and not vfoc and not focus_j:
        return None                                      # the new item is the subject: a new topic, leave it first
    rule = 'given-object' if any(p.typ != 'pp' for p in move) else 'goal-after'
    if focus_j and not vfoc:
        rule = 'focus-tail'
    return (flat(head) + flat(lead) + (S.idx if S else []) + flat(stay) + V.idx + flat(move), rule, '', set())


def main():
    cards, known, uses = K.run(P.sentence_paths(), quiet=True, show=False)
    rows = []
    for c in cards:
        if c['src'] != 'composed' or not LO <= c['chapter'] <= HI:
            continue
        r = propose(c)
        if r is None:
            continue
        rule, new, note = r
        if rule == 'manual':
            rows.append((c['n'], c['chapter'], 'manual', c['gr'], '', c['en'], ','.join(sorted(c['new'])), ''))
            continue
        if K.nfc(new) == K.nfc(c['gr']):
            continue
        rows.append((c['n'], c['chapter'], rule, c['gr'], new, c['en'], ','.join(sorted(c['new'])), note))
    with open(OUT[:-4] + '_cards.tsv', 'w', encoding='utf-8') as f:    # every composed card of the range
        for c in cards:
            if c['src'] == 'composed' and LO <= c['chapter'] <= HI:
                f.write('%d\t%d\t%s\t%s\t%s\n' % (c['n'], c['chapter'], c['gr'], c['en'], ','.join(sorted(c['new']))))
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('n\tch\trule\told\tnew\ten\tnew_items\tnote\n')
        for r in rows:
            f.write('\t'.join(str(x) for x in r) + '\n')
    import collections
    print(len(rows), collections.Counter(r[2] for r in rows).most_common())


if __name__ == '__main__':
    main()
