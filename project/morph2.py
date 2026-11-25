# -*- coding: utf-8 -*-
"""Paradigms for Athenaze II (ch.17–31): future, subjunctive, optative, aorist passive, perfect, -μι verbs …
Built on morph.py; every function returns [(form, tag9)], tense codes: f future, r perfect, l pluperfect,
P aorist passive (θη-aorist; the future passive is tense f + voice p)."""
import unicodedata as ud
from morph import (nfc, strip, strip_len, put_accent, acc_pos, verb, recessive, persistent, syllabify,
                   onset_nucleus_coda, perispomenon_ultima, rec_aug, mark_len, augment, ACUTE, CIRC, CASES,
                   END1, END2, PL1, _contracted)

CIRC_CH = '͂'


def _pseudo(spec):
    """future 1st sg. → a 'present' verb with the same endings: λύσω, ὄψομαι, μενῶ → μενέω, μαχοῦμαι → μαχέομαι,
    ἐλῶ~α → ἐλάω.  Returns (pseudo lemma, contract class, deponent?)"""
    spec = nfc(spec)
    cls = 'ε'
    if '~' in spec:
        spec, cls = spec.split('~')
    s = strip(spec)
    circ = CIRC_CH in ud.normalize('NFD', spec)[-6:]
    if circ and s.endswith('ουμαι'):
        return s[:-5] + ('ά' if cls == 'α' else 'έ') + 'ομαι', cls, True
    if circ and s.endswith('ωμαι'):
        return s[:-4] + 'άομαι', 'α', True
    if s.endswith('ομαι'):
        return spec, '', True
    if circ and s.endswith('ω'):
        return s[:-1] + ('ά' if cls == 'α' else 'έ') + 'ω', cls, False
    return spec, '', False


def future(lemma, spec, mid=False, long=False, short=False):
    """future indicative, infinitive and participle from the 1st sg. (λύσω, πέμψω, ὄψομαι, μενῶ, μαχοῦμαι)"""
    pseudo, cls, dep = _pseudo(spec)
    out = []
    for f, t in verb(pseudo, impf=False, mid=mid and not dep, long=long, short=short, auto_pass=False):
        if t[3] == 'p' and t[4] in 'inpo':
            out.append((f, t[:3] + 'f' + t[4:]))
    return out


def fut_class(spec):
    return _pseudo(spec)[1]


# ---------------------------------------------------------------- compounds of irregular verbs
SMOOTH, ROUGH = '̓', '̔'
VOWELS = 'αεηιουω'
P_ELIDE = {'ἀνα': 'ἀν', 'ἀπο': 'ἀπ', 'δια': 'δι', 'ἐπι': 'ἐπ', 'κατα': 'κατ', 'μετα': 'μετ', 'παρα': 'παρ',
           'ὑπο': 'ὑπ', 'ἀντι': 'ἀντ', 'ἐκ': 'ἐξ', 'ἐπανα': 'ἐπαν', 'συνανα': 'συναν', 'προσανα': 'προσαν',
           'ἀνταπο': 'ἀνταπ', 'συγκατα': 'συγκατ', 'προκατα': 'προκατ', 'ἐγκατα': 'ἐγκατ', 'παρακατα': 'παρακατ'}
P_ASPIR = {'ἀπ': 'ἀφ', 'ἐπ': 'ἐφ', 'κατ': 'καθ', 'μετ': 'μεθ', 'ὑπ': 'ὑφ', 'ἀντ': 'ἀνθ'}


def _nobreath(w):
    d = ud.normalize('NFD', w)
    return nfc(''.join(c for c in d if c not in (SMOOTH, ROUGH)))


def _join(pre, form):
    """prefix (full form: ἀπο, κατα, ἐν, συν, ἐκ, προσ …) + a form of the simple verb, without accent"""
    f = strip(form)
    d = ud.normalize('NFD', f)
    rough = ROUGH in d[:4]
    body = _nobreath(f)
    if ud.normalize('NFD', body)[0] in VOWELS:
        p = P_ELIDE.get(pre, pre)
        if rough:
            p = P_ASPIR.get(p, p)
        return p + body, p
    p = pre
    if pre in ('ἐν', 'συν'):
        c = body[0]
        p = pre[:-1] + ('μ' if c in 'βπφμψ' else 'γ' if c in 'γκχξ' else 'λ' if c == 'λ' else 'ν')
        if pre == 'συν' and c in 'σζ':
            p = 'συ'
    return p + body, p


def compound(pre, base_forms):
    """forms of a compound from those of the simple verb: [(form, tag)] → [(form, tag)].
    The accent stays where the simple verb has it (ἀποδοῦναι, ἀπιών, ἀπέδωκα); present indicatives and
    imperatives throw it back, but not beyond the last syllable of the prefix (ἄπειμι, ἄπιθι, ἀπόδος, ἀνάστηθι)."""
    out = []
    for form, tag in base_forms:
        if ' ' in form:
            continue
        joined, p = _join(pre, form)
        syl_b = syllabify(strip(form))
        pos, kind = acc_pos(form)
        try:
            if tag[0] == 'v' and (tag[4] == 'm' or tag[4] == 'i' and tag[3] == 'p') and not (
                    kind == CIRC and len(syl_b) > pos):   # contracted ἱστᾶσι keeps its accent: καθιστᾶσι
                n_pre = len(syllabify(p)) if any(v in p[-1:] for v in VOWELS) else len(syllabify(p + 'α')) - 1
                w = rec_aug(joined, max(n_pre - 1, 0))
                p2, k2 = acc_pos(w)
                sy = syllabify(strip(w))
                if k2 == CIRC and len(sy) - p2 < n_pre and len(strip(onset_nucleus_coda(sy[len(sy) - p2])[1])) == 1:
                    w = put_accent(w, p2, ACUTE)             # the vowels of the prefixes are short: σύνδος
            elif pos:
                w = put_accent(joined, pos, kind)
            else:
                w = recessive(joined)
        except Exception:
            continue
        out.append((nfc(strip_len(w)), tag))
    return out


# ---------------------------------------------------------------- more nouns
def noun_eus(lemma):
    """ὁ βασιλεύς-type: γονεύς, γονέως, γονεῖ, γονέα, γονεῦ; γονῆς / γονεῖς, γονέων, γονεῦσι(ν), γονέας"""
    st = strip(lemma)[:-3]
    forms = [('ns', 'εύς'), ('gs', 'έως'), ('ds', 'εῖ'), ('as', 'έα'), ('vs', 'εῦ'), ('np', 'ῆς'), ('np', 'εῖς'),
             ('gp', 'έων'), ('dp', 'εῦσι'), ('dp', 'εῦσιν'), ('ap', 'έας'), ('vp', 'ῆς'), ('vp', 'εῖς')]
    return [(nfc(st + e), 'n-%s---m%s-' % (k[1], k[0])) for k, e in forms]


def noun_is(lemma, gender='f'):
    """ἡ πόλις-type: ὄφις, ὄφεως, ὄφει, ὄφιν; ὄφεις, ὄφεων, ὄφεσι(ν), ὄφεις — accent as in the nominative"""
    st = strip(lemma)[:-2]
    pos, kind = acc_pos(lemma)
    out = []
    for k, e in [('ns', 'ις'), ('gs', 'εως'), ('ds', 'ει'), ('as', 'ιν'), ('vs', 'ι'), ('np', 'εις'), ('gp', 'εων'),
                 ('dp', 'εσι'), ('dp', 'εσιν'), ('ap', 'εις'), ('vp', 'εις')]:
        w = st + e
        n = len(syllabify(w))
        base_n = len(syllabify(strip(lemma)))
        # the accent keeps its syllable (counted from the start): πόλις, πόλεως, πόλεων; δύναμις, δυνάμεως
        from_start = base_n - pos
        if k in ('gs', 'gp'):
            p = n - from_start
            p = min(p, 3)
            f = put_accent(w, p, ACUTE)
        else:
            try:
                f = persistent(w, lemma)
            except Exception:
                f = put_accent(w, min(n - from_start, 3), ACUTE)
        out.append((nfc(f), 'n-%s---%s%s-' % (k[1], gender, k[0])))
    return out


def adj_us(lemma):
    """ταχύς, ταχεῖα, ταχύ: βαθύς, βαρύς, βραδύς, ἡδύς, τραχύς … (all oxytone)"""
    st = strip(lemma)[:-2]
    m = [('ns', 'ύς'), ('gs', 'έος'), ('ds', 'εῖ'), ('as', 'ύν'), ('vs', 'ύ'), ('np', 'εῖς'), ('gp', 'έων'),
         ('dp', 'έσι'), ('dp', 'έσιν'), ('ap', 'εῖς'), ('vp', 'εῖς')]
    n = [('ns', 'ύ'), ('gs', 'έος'), ('ds', 'εῖ'), ('as', 'ύ'), ('vs', 'ύ'), ('np', 'έα'), ('gp', 'έων'),
         ('dp', 'έσι'), ('dp', 'έσιν'), ('ap', 'έα'), ('vp', 'έα')]
    f = [('ns', 'εῖα'), ('gs', 'είας'), ('ds', 'είᾳ'), ('as', 'εῖαν'), ('vs', 'εῖα'), ('np', 'εῖαι'), ('gp', 'ειῶν'),
         ('dp', 'είαις'), ('ap', 'είας'), ('vp', 'εῖαι')]
    out = []
    for g, ends in (('m', m), ('n', n), ('f', f)):
        for k, e in ends:
            out.append((nfc(st + e), 'a-%s---%s%s-' % (k[1], g, k[0])))
    return out


def numi(lemma, aor=None, impf=None):
    """verbs in -νυμι (δείκνυμι, ζεύγνυμι, ῥήγνυμι): present and imperfect, active and middle; the present subjunctive
    and the sigmatic aorist (aor='ἔδειξα/δειξ') are the ordinary thematic ones.  impf: augmented stem ('ἐρρηγνυ')"""
    from morph import strip, put_accent, recessive, persistent, augment, verb, nfc, ACUTE, CIRC, perispomenon_ultima
    st = strip(lemma)[:-2]                                  # δεικνυ
    out = []

    def add(f, t):
        out.append((nfc(f), t))
    def rec(w):                                            # the υ of -νυ- is short outside the singular
        return recessive(w)
    add(lemma, 'v1spia---')
    add(put_accent(st + 'ς', 2, ACUTE), 'v2spia---')
    for e in ('σι', 'σιν'):
        add(recessive(st + e), 'v3spia---')
    add(recessive(st + 'μεν'), 'v1ppia---')
    add(recessive(st + 'τε'), 'v2ppia---')
    add(recessive(st + 'τε'), 'v2ppma---')
    for e in ('ασι', 'ασιν'):
        add(put_accent(st + e, 3, ACUTE), 'v3ppia---')      # δεικνύασι
    add(put_accent(st + 'ναι', 2, ACUTE), 'v--pna---')      # δεικνύναι
    add(put_accent(st, 2, ACUTE), 'v2spma---')              # δείκνυ (long υ)
    a = strip(impf) if impf else augment(st)
    pre, _, rest = a.rpartition('|')
    a = pre + rest
    for pn, e in (('1s', 'ν'), ('2s', 'ς'), ('3s', ''), ('1p', 'μεν'), ('2p', 'τε'), ('3p', 'σαν')):
        add(put_accent(a + e, 2, ACUTE) if pn[1] == 's' else recessive(a + e), 'v%s%siia---' % (pn[0], pn[1]))   # ἐδείκνῡν
    for pn, e in (('1s', 'μαι'), ('2s', 'σαι'), ('3s', 'ται'), ('1p', 'μεθα'), ('2p', 'σθε'), ('3p', 'νται')):
        add(recessive(st + e), 'v%s%spim---' % (pn[0], pn[1]))
    add(recessive(st + 'σθε'), 'v2ppmm---')
    add(recessive(st + 'σο'), 'v2spmm---')
    add(recessive(st + 'σθαι'), 'v--pnm---')
    for pn, e in (('1s', 'μην'), ('2s', 'σο'), ('3s', 'το'), ('1p', 'μεθα'), ('2p', 'σθε'), ('3p', 'ντο')):
        add(recessive(a + e), 'v%s%siim---' % (pn[0], pn[1]))
    # participles: δεικνύς δεικνύντος, δεικνῦσα δεικνύσης, δεικνύν; δεικνύμενος
    CASES = 'ngdav'
    m = ['ύς', 'ύντος', 'ύντι', 'ύντα', 'ύς', 'ύντες', 'ύντων', 'ῦσι', 'ύντας', 'ύντες']
    n = ['ύν', 'ύντος', 'ύντι', 'ύν', 'ύν', 'ύντα', 'ύντων', 'ῦσι', 'ύντα', 'ύντα']
    f = ['ῦσα', 'ύσης', 'ύσῃ', 'ῦσαν', 'ῦσα', 'ῦσαι', 'υσῶν', 'ύσαις', 'ύσας', 'ῦσαι']
    b = st[:-1]
    for g, ends in (('m', m), ('n', n), ('f', f)):
        for i, e in enumerate(ends):
            add(b + e, 'v-%sppa%s%s-' % ('s' if i < 5 else 'p', g, CASES[i % 5]))
    for g, ends in (('m', ['ος', 'ου', 'ῳ', 'ον', 'ε', 'οι', 'ων', 'οις', 'ους', 'οι']),
                    ('n', ['ον', 'ου', 'ῳ', 'ον', 'ον', 'α', 'ων', 'οις', 'α', 'α']),
                    ('f', ['η', 'ης', 'ῃ', 'ην', 'η', 'αι', 'ων', 'αις', 'ας', 'αι'])):
        for i, e in enumerate(ends):
            try:
                add(persistent(st + 'μεν' + e, put_accent(st + 'μενος', 3, ACUTE)),
                    'v-%sppm%s%s-' % ('s' if i < 5 else 'p', g, CASES[i % 5]))
            except Exception:
                pass
    # thematic parts: present subjunctive (δεικνύω, δεικνύῃς …) and the aorist
    for fm, t in verb(st + 'ω', aor=aor, impf=False, mid=True):
        if t[3] == 'a' or (t[3] == 'p' and t[4] in 'so'):
            add(fm, t)
    return out


def _syl(w):
    from greek_accentuation.accentuation import syllabify
    return syllabify(w)


def _long_first(st):
    from morph import strip
    s = _syl(strip(st))
    return len(s) >= 2 and any(d in s[-2] for d in ('ει', 'ευ', 'ου', 'αι', 'οι', 'η', 'ω'))


def aor_pass(lemma, spec):
    """aorist passive (ἐλύθην, ἐγράφην) with its subjunctive, imperative, infinitive and participle, and the future
    passive built on the same stem (λυθήσομαι).  spec: 1st sg. with the unaugmented stem after '/' when the augment is
    not simply ἐ- + consonant: 'ἐλύθην', 'ἤχθην/ἀχθ', 'συν|ελέγην/συλλεγ'"""
    from morph import strip, root_aor, put_accent, nfc, ACUTE
    a, _, st = spec.partition('/')
    plain = strip(a.replace('|', ''))
    if not st:
        if plain.startswith('ἐρρ'):
            st = 'ῥ' + plain[3:-2]
        elif plain.startswith('ἐ') and plain[1:2] not in 'αεηιουω':
            st = plain[1:-2]
    a = a if strip(a).endswith('ην') else a
    out = []
    if not st:                                              # no stem: only the indicative
        aug = strip(a.replace('|', ''))[:-1]
        from morph import rec_aug, syllabify
        pre = a.rpartition('|')[0]
        for pn, e in (('1s', 'ν'), ('2s', 'ς'), ('3s', ''), ('1p', 'μεν'), ('2p', 'τε'), ('3p', 'σαν')):
            out.append((nfc(rec_aug(aug + e, len(syllabify(pre)) if pre else 0)), 'v%s%saip---' % (pn[0], pn[1])))
        return out
    st = strip(st)
    for f, t in root_aor(lemma, '%s/%s/%s' % (a, st + 'η', st + 'ε')):
        if t[4] == 'm' and t[1:3] == '2s' and strip(f).endswith('θηθι'):
            f = f[:-2] + 'τι'                               # λύθητι (but γράφηθι)
        out.append((f, t[:3] + 'a' + t[4] + 'p' + t[6:]))
    futs = future(lemma, put_accent(st + 'ησομαι', 3, ACUTE))
    for f, t in futs:
        out.append((f, t[:5] + 'p' + t[6:]))
    return out


def perf_mid(lemma, spec):
    """perfect / pluperfect / future perfect middle-passive from the 1st sg. perfect: 'λέλυμαι', 'γέγραμμαι',
    'τέταγμαι', 'πέπεισμαι', 'ἤγγελμαι'; a compound marks its prefix: 'ἀπο|λέλυμαι' (pluperfect ἀπ-ελελύμην),
    'ἀφ|ῖγμαι' (the accent does not go back past the reduplication: ἀφῖκται)"""
    import unicodedata as ud
    from morph import (strip, strip_len, recessive, rec_aug, put_accent, persistent, nfc, ACUTE, CIRC, syllabify,
                       END1, END2, PL1, CASES)
    pre, _, body = spec.rpartition('|')
    d = ud.normalize('NFD', pre + body)
    d = d.replace('\u0342', '\u0304\u0342')              # a circumflexed ι α υ is long: keep a macron
    full = strip(nfc(d))
    npre = len(syllabify(strip(pre))) if pre else 0
    out = []

    def add(f, t):
        out.append((nfc(strip_len(f)), t))

    def rec(w, n=None):
        n = npre if n is None else n
        f = rec_aug(w, n) if n else recessive(w)
        syl = syllabify(f)
        if len(syl) >= 2:                                   # ἀφῖκται: long penult + short ultima → circumflex
            pen = ud.normalize('NFD', syl[-2])
            ult = strip(syl[-1])
            short_ult = ult.endswith(('αι', 'οι')) or not any(x in ult for x in ('η', 'ω', 'ει', 'ου', 'αι', 'οι', 'ευ', 'αυ'))
            if '\u0301' in pen and '\u0304' in pen and short_ult:
                f = put_accent(f, 2, CIRC)
        return f
    b = full
    if b.endswith('μμαι'):
        cls, X = 'lab', b[:-4]
        if 'μπ' in strip(lemma):                            # πέπεμμαι < πεπεμπ-μαι: πέπεμψαι, πέπεμπται
            X += 'μ'
            E_fix = True
    elif b.endswith('γμαι'):
        cls, X = 'gut', b[:-4]
    elif b.endswith(('λμαι', 'ρμαι')):
        cls, X = 'liq', b[:-3]
    elif b.endswith('σμαι'):
        cls, X = 'ses', b[:-4]
    else:
        cls, X = 'vow', b[:-3]
    E = {'vow': dict(m='μ', s2='σαι', s3='ται', p2='σθε', inf='σθαι', o2='σο', o3='το', fut='σομαι'),
         'ses': dict(m='σμ', s2='σαι', s3='σται', p2='σθε', inf='σθαι', o2='σο', o3='στο', fut='σομαι'),
         'lab': dict(m='μμ', s2='ψαι', s3='πται', p2='φθε', inf='φθαι', o2='ψο', o3='πτο', fut='ψομαι'),
         'gut': dict(m='γμ', s2='ξαι', s3='κται', p2='χθε', inf='χθαι', o2='ξο', o3='κτο', fut='ξομαι'),
         'liq': dict(m='μ', s2='σαι', s3='ται', p2='θε', inf='θαι', o2='σο', o3='το', fut='')}[cls]
    if cls == 'lab' and 'μπ' in strip(lemma):
        E = dict(E, m='μ')                                  # πέπεμ-μαι, πεπέμ-μεθα, πεπεμ-μένος
    ind = [('1s', E['m'] + 'αι'), ('2s', E['s2']), ('3s', E['s3']), ('1p', E['m'] + 'εθα'), ('2p', E['p2'])]
    if cls == 'vow':
        ind.append(('3p', 'νται'))
    for pn, e in ind:
        add(rec(X + e), 'v%s%srie---' % (pn[0], pn[1]))
    add(rec(X + E['o2']), 'v2srme---')                     # imperative λέλυσο
    # infinitive and participle: accent on the penult (λελύσθαι, πεποιῆσθαι, πεπεῖσθαι, ἐζεῦχθαι; λελυμένος)
    inf = X + E['inf']
    pen = ud.normalize('NFD', syllabify(inf)[-2])
    base = ''.join(c for c in pen if not ud.combining(c) or c == '\u0304')
    long_pen = '\u0304' in pen or any(x in base for x in ('αι', 'ει', 'οι', 'ευ', 'αυ', 'ου', 'η', 'ω')) or \
        any(c in pen for c in '\u0345')
    add(put_accent(inf, 2, CIRC if long_pen else ACUTE), 'v--rne----')
    pt = X + E['m'] + 'εν'
    for g, ends in (('m', END2['m']), ('n', END2['n']), ('f', END1['η'] + PL1)):
        for i, e in enumerate(ends):
            num, case = ('s' if i < 5 else 'p'), CASES[i % 5]
            try:
                add(persistent(pt + e, put_accent(pt + 'ος', 2, ACUTE)), 'v-%srpe%s%s-' % (num, g, case))
            except Exception:
                pass
    # pluperfect: augment ἐ- when the perfect stem begins with a consonant (ἐλελύμην), none with a vowel (ἠγγέλμην)
    bd = strip(body)
    first = ud.normalize('NFD', bd)[0]
    if first in 'αεηιουω':
        plu, npl = X, npre
    else:
        pr = strip(pre)
        if pr and pr[-1] in 'αεο' and pr not in ('περι', 'προ'):
            pr = pr[:-1]
        plu = (pr + 'ε' if pr else 'ἐ') + X[len(strip(pre)):]
        npl = len(syllabify(pr)) if pr else 0
    pl = [('1s', E['m'] + 'ην'), ('2s', E['o2']), ('3s', E['o3']), ('1p', E['m'] + 'εθα'), ('2p', E['p2'])]
    if cls == 'vow':
        pl.append(('3p', 'ντο'))
    for pn, e in pl:
        try:
            add(rec(plu + e, npl), 'v%s%slie---' % (pn[0], pn[1]))
        except Exception:
            pass
    # future perfect (λελύσομαι, γεγράψομαι, τετάξομαι): indicative and infinitive
    if E['fut']:
        for f, t in future(lemma, put_accent(X + E['fut'], 3, ACUTE), mid=False):
            if t[4] in 'in':
                add(f, t[:3] + 't' + t[4] + 'e' + t[6:])
    return out


def perf_act(lemma, spec):
    """perfect and pluperfect active from the 1st sg. perfect: 'λέλυκα', 'πέπομφα', 'γέγραφα', 'ἔγνωκα',
    'ἀπο|λέλυκα' (prefix marked: pluperfect ἀπ-ελελύκη)"""
    import unicodedata as ud
    from morph import strip, strip_len, recessive, rec_aug, put_accent, nfc, ACUTE, CIRC, syllabify, CASES
    pre, _, body = spec.rpartition('|')
    d = ud.normalize('NFD', pre + body).replace('͂', '̄͂')
    full = strip(nfc(d))
    X = full[:-1]                                           # λελυκ-
    npre = len(syllabify(strip(pre))) if pre else 0
    out = []

    def add(f, t):
        out.append((nfc(strip_len(f)), t))

    def rec(w, n=None):
        n = npre if n is None else n
        f = rec_aug(w, n) if n else recessive(w)
        syl = syllabify(f)
        if len(syl) >= 2:
            pen = ud.normalize('NFD', syl[-2])
            ult = strip(syl[-1])
            short_ult = not any(x in ult for x in ('η', 'ω', 'ει', 'ου', 'αι', 'οι', 'ευ', 'αυ')) or ult.endswith('αι')
            if '́' in pen and '̄' in pen and short_ult:
                f = put_accent(f, 2, CIRC)
        return f
    for pn, e in (('1s', 'α'), ('2s', 'ας'), ('3s', 'ε'), ('3s', 'εν'), ('1p', 'αμεν'), ('2p', 'ατε'), ('3p', 'ασι'),
                  ('3p', 'ασιν')):
        add(rec(X + e), 'v%s%sria---' % (pn[0], pn[1]))
    add(put_accent(X + 'εναι', 2, ACUTE), 'v--rna----')    # λελυκέναι
    m = [('ns', 'ώς'), ('gs', 'ότος'), ('ds', 'ότι'), ('as', 'ότα'), ('np', 'ότες'), ('gp', 'ότων'), ('dp', 'όσι'),
         ('dp', 'όσιν'), ('ap', 'ότας')]
    n = [('ns', 'ός'), ('as', 'ός'), ('gs', 'ότος'), ('ds', 'ότι'), ('np', 'ότα'), ('ap', 'ότα'), ('gp', 'ότων'),
         ('dp', 'όσι')]
    f = [('ns', 'υῖα'), ('gs', 'υίας'), ('ds', 'υίᾳ'), ('as', 'υῖαν'), ('np', 'υῖαι'), ('gp', 'υιῶν'),
         ('dp', 'υίαις'), ('ap', 'υίας')]
    for g, ends in (('m', m), ('n', n), ('f', f)):
        for k, e in ends:
            add(strip(X) + e, 'v-%srpa%s%s-' % (k[1], g, k[0]))
    # pluperfect: ἐλελύκη, -ης, -ει(ν), -εμεν, -ετε, -εσαν (1st sg. also -ειν)
    first = ud.normalize('NFD', strip(body))[0]
    if first in 'αεηιουω':
        plu, npl = X, npre
    else:
        pr = strip(pre)
        if pr and pr[-1] in 'αεο' and pr not in ('περι', 'προ'):
            pr = pr[:-1]
        plu = (pr + 'ε' if pr else 'ἐ') + X[len(strip(pre)):]
        npl = len(syllabify(pr)) if pr else 0
    for pn, e in (('1s', 'η'), ('1s', 'ειν'), ('2s', 'ης'), ('3s', 'ει'), ('3s', 'ειν'), ('1p', 'εμεν'), ('2p', 'ετε'),
                  ('3p', 'εσαν')):
        try:
            add(rec(plu + e, npl), 'v%s%slia---' % (pn[0], pn[1]))
        except Exception:
            pass
    return out
