# -*- coding: utf-8 -*-
"""Small Attic paradigm generator (regular 1st/2nd declension nouns and adjectives, thematic and
contract verbs: present, imperfect, aorist from given principal parts). Returns {form: [(lemma, tag9)]}.
Accents: greek_accentuation (recessive / persistent) + the rules it lacks (oxytone gen/dat, 1st decl. gen pl,
contraction). Forms it gets wrong simply do not match and are added by hand in forms_extra.txt."""
import re, unicodedata as ud
from collections import defaultdict
from greek_accentuation.accentuation import recessive, persistent, syllabify, onset_nucleus_coda
from greek_accentuation.characters import strip_accents, add_diacritic

ACUTE, GRAVE, CIRC = '́', '̀', '͂'


def nfc(s): return ud.normalize('NFC', s)


def strip(w):
    return nfc(strip_accents(nfc(w)))


def strip_len(w):
    d = ud.normalize('NFD', w)
    return nfc(d.replace('̄', '').replace('̆', ''))


def acc_pos(w):
    """index (from the end, 1 = ultima) of the accented syllable and the accent kind"""
    syl = syllabify(w)
    for i, s in enumerate(reversed(syl), 1):
        d = ud.normalize('NFD', s)
        if ACUTE in d or GRAVE in d:
            return i, ACUTE
        if CIRC in d:
            return i, CIRC
    return None, None


def put_accent(w, pos, kind):
    """put accent `kind` on syllable `pos` (from the end) of word w (existing accents removed)"""
    syl = syllabify(strip(w))
    i = len(syl) - pos
    d = ud.normalize('NFD', syl[i])
    vow = [j for j, ch in enumerate(d) if not ud.combining(ch) and ch.lower() in 'αεηιουω']
    if not vow:
        return nfc(''.join(syl))
    j = vow[-1]
    if len(vow) >= 2 and d[vow[-1]] in 'ιυ' and vow[-2] == vow[-1] - 1 - sum(1 for c in d[vow[-2] + 1:vow[-1]] if ud.combining(c)) \
            and '\u0308' not in d[vow[-2]:vow[-1] + 3]:
        j = vow[-1]                      # diphthong: accent on its second vowel
    elif len(vow) >= 2:
        j = vow[-1]
    k = j + 1
    while k < len(d) and ud.combining(d[k]) and d[k] in '\u0313\u0314\u0308\u0304':
        k += 1
    d = d[:k] + kind + d[k:]
    syl[i] = nfc(d)
    return nfc(''.join(syl))


def perispomenon_ultima(w):
    return put_accent(w, 1, CIRC)


# ---------------------------------------------------------------- nouns / adjectives
CASES = ['n', 'g', 'd', 'a', 'v']
END2 = {'m': ['ος', 'ου', 'ῳ', 'ον', 'ε', 'οι', 'ων', 'οις', 'ους', 'οι'],
        'n': ['ον', 'ου', 'ῳ', 'ον', 'ον', 'α', 'ων', 'οις', 'α', 'α']}
END1 = {'η': ['η', 'ης', 'ῃ', 'ην', 'η'], 'ᾱ': ['ᾱ', 'ᾱς', 'ᾳ', 'ᾱν', 'ᾱ'], 'α': ['α', 'ης', 'ῃ', 'αν', 'α'],
        'ης': ['ης', 'ου', 'ῃ', 'ην', 'η'], 'ας': ['ᾱς', 'ου', 'ᾳ', 'ᾱν', 'ᾱ'], 'της': ['ης', 'ου', 'ῃ', 'ην', 'α\u0306']}
PL1 = ['αι', 'ων', 'αις', 'ᾱς', 'αι']


def _decline(lemma, stem, ends, gender, oxy_circ, gen_pl_circ=False, pos='n'):
    out = []
    for i, e in enumerate(ends):
        num = 's' if i < 5 else 'p'
        case = CASES[i % 5]
        f = stem + e
        try:
            w = persistent(f, lemma)
        except Exception:
            continue
        if oxy_circ and case in 'gd':
            w = perispomenon_ultima(w)
        if gen_pl_circ and case == 'g' and num == 'p':
            w = perispomenon_ultima(w)
        out.append((strip_len(w), '%s-%s---%s%s-' % (pos, num, gender, case)))
    return out


def noun12(lemma, gender=None, long=False, short=False, sa=False):
    if long or short:
        pos, kind = acc_pos(lemma)
        mk = mark_len(strip(lemma), '\u0304' if long else '\u0306')
        lemma = put_accent(mk, pos, kind)
    s = strip(lemma)
    oxy = acc_pos(lemma)[0] == 1
    if s.endswith('ος'):
        g = gender or 'm'
        return _decline(lemma, s[:-2], END2['m'], g, oxy)
    if s.endswith('ον'):
        return _decline(lemma, s[:-2], END2['n'], 'n', oxy)
    if s.endswith('της') and (gender or 'm') == 'm':
        return _decline(lemma, s[:-2], END1['της'] + PL1, 'm', oxy, True)
    if s.endswith('ης') and (gender or 'm') == 'm':
        return _decline(lemma, s[:-2], END1['ης'] + PL1, 'm', oxy, True)
    if s.endswith('ας') and (gender or 'm') == 'm':
        return _decline(lemma, s[:-2], END1['ας'] + PL1, 'm', oxy, True)
    if s.endswith('η'):
        return _decline(lemma, s[:-1], END1['η'] + PL1, 'f', oxy, True)
    if s.endswith('α') and sa:                         # ἀλήθεια, πεῖρα: short α in nom./acc./voc. sg., long in gen./dat.
        return _decline(lemma, s[:-1], ['α\u0306', 'ᾱς', 'ᾳ', 'α\u0306ν', 'α\u0306'] + PL1, 'f', oxy, True)
    if s.endswith('α'):
        pure = s[-2:-1] in 'ειραο'
        return _decline(lemma, s[:-1], (END1['ᾱ'] if pure else END1['α']) + PL1, 'f', oxy, True)
    return []


def adj212(lemma, two_endings=False):
    s = strip(lemma)
    if not s.endswith('ος'):
        return []
    stem = s[:-2]
    oxy = acc_pos(lemma)[0] == 1
    out = _decline(lemma, stem, END2['m'], 'm', oxy, pos='a')
    out += _decline(lemma, stem, END2['n'], 'n', oxy, pos='a')
    if two_endings:
        out += [(w, t[:6] + 'f' + t[7:]) for w, t in _decline(lemma, stem, END2['m'], 'm', oxy, pos='a')]
    else:
        fe = END1['ᾱ'] if stem[-1:] in 'ειρ' else END1['η']
        fem = _decline(lemma, stem, fe + PL1, 'f', oxy, pos='a')
        # adjectives: fem gen pl takes the masculine accent (no -ῶν rule)
        out += fem
    return out


# ---------------------------------------------------------------- verbs
PRES_A = [('1s', 'ω'), ('2s', 'εις'), ('3s', 'ει'), ('1p', 'ομεν'), ('2p', 'ετε'), ('3p', 'ουσι'), ('3p', 'ουσιν')]
PRES_M = [('1s', 'ομαι'), ('2s', 'ῃ'), ('2s', 'ει'), ('3s', 'εται'), ('1p', 'ομεθα'), ('2p', 'εσθε'), ('3p', 'ονται')]
IMPF_A = [('1s', 'ον'), ('2s', 'ες'), ('3s', 'ε'), ('3s', 'εν'), ('1p', 'ομεν'), ('2p', 'ετε'), ('3p', 'ον')]
IMPF_M = [('1s', 'ομην'), ('2s', 'ου'), ('3s', 'ετο'), ('1p', 'ομεθα'), ('2p', 'εσθε'), ('3p', 'οντο')]
IMP_A = [('2s', 'ε'), ('2p', 'ετε'), ('3s', 'ετω'), ('3p', 'οντων')]
IMP_M = [('2s', 'ου'), ('2p', 'εσθε'), ('3s', 'εσθω'), ('3p', 'εσθων')]
AOR_A = [('1s', 'α'), ('2s', 'ας'), ('3s', 'ε'), ('3s', 'εν'), ('1p', 'αμεν'), ('2p', 'ατε'), ('3p', 'αν')]
AOR_M = [('1s', 'αμην'), ('2s', 'ω'), ('3s', 'ατο'), ('1p', 'αμεθα'), ('2p', 'ασθε'), ('3p', 'αντο')]
AOR_IMP_A = [('2s', 'ον'), ('2p', 'ατε'), ('3s', 'ατω'), ('3p', 'αντων')]
AOR_IMP_M = [('2s', 'αι'), ('2p', 'ασθε'), ('3s', 'ασθω'), ('3p', 'ασθων')]
OPT_A = [('1s', 'οιμι'), ('2s', 'οις'), ('3s', 'οι'), ('1p', 'οιμεν'), ('2p', 'οιτε'), ('3p', 'οιεν')]
OPT_M = [('1s', 'οιμην'), ('2s', 'οιο'), ('3s', 'οιτο'), ('1p', 'οιμεθα'), ('2p', 'οισθε'), ('3p', 'οιντο')]
OPT_CA_EO = [('1s', 'οίην'), ('2s', 'οίης'), ('3s', 'οίη'), ('1p', 'οῖμεν'), ('2p', 'οῖτε'), ('3p', 'οῖεν')]
OPT_CA_A = [('1s', 'ῴην'), ('2s', 'ῴης'), ('3s', 'ῴη'), ('1p', 'ῷμεν'), ('2p', 'ῷτε'), ('3p', 'ῷεν')]
OPT_CM_EO = [('1s', 'οίμην'), ('2s', 'οῖο'), ('3s', 'οῖτο'), ('1p', 'οίμεθα'), ('2p', 'οῖσθε'), ('3p', 'οῖντο')]
OPT_CM_A = [('1s', 'ῴμην'), ('2s', 'ῷο'), ('3s', 'ῷτο'), ('1p', 'ῴμεθα'), ('2p', 'ῷσθε'), ('3p', 'ῷντο')]
OPT1_A = [('1s', 'αιμι'), ('2s', 'αις'), ('2s', 'ειας'), ('3s', 'αι'), ('3s', 'ειε'), ('3s', 'ειεν'), ('1p', 'αιμεν'),
          ('2p', 'αιτε'), ('3p', 'αιεν'), ('3p', 'ειαν')]
OPT1_M = [('1s', 'αιμην'), ('2s', 'αιο'), ('3s', 'αιτο'), ('1p', 'αιμεθα'), ('2p', 'αισθε'), ('3p', 'αιντο')]
OPT_R = [('1s', 'ίην'), ('2s', 'ίης'), ('3s', 'ίη'), ('1p', 'ῖμεν'), ('2p', 'ῖτε'), ('3p', 'ῖεν')]


def rec_opt(w):
    """recessive accent for the optative: final -οι / -αι count as long (λύοι, παιδεύοι, κελεύσαι)"""
    return recessive(w, False)


SUBJ_A = [('1s', 'ω'), ('2s', 'ῃς'), ('3s', 'ῃ'), ('1p', 'ωμεν'), ('2p', 'ητε'), ('3p', 'ωσι'), ('3p', 'ωσιν')]
SUBJ_M = [('1s', 'ωμαι'), ('2s', 'ῃ'), ('3s', 'ηται'), ('1p', 'ωμεθα'), ('2p', 'ησθε'), ('3p', 'ωνται')]
CONTRACT = {
    'ε': {'ε': 'ει', 'ει': 'ει', 'ο': 'ου', 'ου': 'ου', 'ω': 'ω', 'ῃ': 'ῃ', 'οι': 'οι', 'η': 'η'},
    'α': {'ε': 'α', 'ει': 'ᾳ', 'ῃ': 'ᾳ', 'ο': 'ω', 'ου': 'ω', 'ω': 'ω', 'οι': 'ῳ', 'η': 'α'},
    'ο': {'ε': 'ου', 'ει': 'οι', 'ῃ': 'οι', 'ο': 'ου', 'ου': 'ου', 'ω': 'ω', 'οι': 'οι', 'η': 'ω'},
}
PTC_A = ['ων', 'οντος', 'οντι', 'οντα', 'ων', 'οντες', 'οντων', 'ουσι', 'οντας', 'οντες']
PTC_AN = ['ον', 'οντος', 'οντι', 'ον', 'ον', 'οντα', 'οντων', 'ουσι', 'οντα', 'οντα']
PTC_AF = ['ουσα', 'ουσης', 'ουσῃ', 'ουσαν', 'ουσα', 'ουσαι', 'ουσων', 'ουσαις', 'ουσᾱς', 'ουσαι']


def augment(stem):
    stem = strip_len(stem)                                   # ᾰ̓γ → ἀγ (length marks only matter for accents)
    s = strip(stem)
    d = ud.normalize('NFD', stem)
    breath = '̔' if '̔' in d[:3] else '̓'
    plain = ''.join(c for c in d if c not in '̓̔')
    plain = nfc(plain)
    if plain[:1] in 'ρ':
        return 'ἐρ' + plain
    for a, b in (('αι', 'ῃ'), ('οι', 'ῳ'), ('αυ', 'ηυ'), ('ευ', 'ηυ'), ('ει', 'ει'), ('ου', 'ου'),
                 ('α', 'η'), ('ε', 'η'), ('ο', 'ω'), ('ι', 'ι'), ('υ', 'υ'), ('η', 'η'), ('ω', 'ω')):
        if plain.startswith(a):
            nb = ud.normalize('NFD', b)
            if len(b) == 2:                                   # diphthong: breathing on the 2nd vowel
                first = b[0] + b[1] + breath
            else:                                             # vowel (+ iota subscript)
                first = nb[0] + breath + nb[1:]
            return nfc(first + plain[len(a):])
    return 'ἐ' + plain


def _contracted(stem_v, form_uncontracted, cls, accented=False):
    """accent the uncontracted form recessively (or take it as accented), then contract stem vowel + ending vowel"""
    try:
        u = form_uncontracted if accented else recessive(form_uncontracted)
    except Exception:
        return None
    syl = syllabify(strip(u))
    pos, kind = acc_pos(u)
    # locate the syllable whose nucleus is the stem vowel (the last syllable of the stem part)
    n_stem = len(syllabify(strip(stem_v)))
    i = n_stem - 1
    if i + 1 >= len(syl):
        return None
    o1, n1, c1 = onset_nucleus_coda(syl[i])
    o2, n2, c2 = onset_nucleus_coda(syl[i + 1])
    if c1 or o2:
        return None
    v2 = strip(n2)
    cv = CONTRACT[cls].get(v2)
    if cv is None:
        return None
    new = syl[:i] + [o1 + cv + c2] + syl[i + 2:]
    w = ''.join(new)
    acc_index_from_start = len(syl) - pos
    if acc_index_from_start == i:
        return put_accent(w, len(new) - i, CIRC)
    if acc_index_from_start == i + 1:
        return put_accent(w, len(new) - i, ACUTE)
    if acc_index_from_start < i:
        return put_accent(w, len(new) - acc_index_from_start, kind)
    return put_accent(w, len(new) - (acc_index_from_start - 1), kind)


def mark_len(stem, mark):
    """put a breve / macron on the first α, ι, υ of the stem (before its breathing), for the accent rules"""
    d = ud.normalize('NFD', stem)
    for i, ch in enumerate(d):
        if ch in 'αιυ' and not (i + 1 < len(d) and d[i + 1] in 'ιυ' and ch == 'α'):
            return nfc(d[:i + 1] + mark + d[i + 1:])
    return stem


def rec_aug(word, pre_len=0):
    """recessive accent that may not go back past the augment of a compound (pre_len = syllables of the prefix):
    παρ|ειχον → παρεῖχον, δι|ηλθον → διῆλθον, ὑπ|ειξαν → ὑπεῖξαν"""
    f = recessive(word)
    if pre_len:
        syl = syllabify(strip(f))
        pos = acc_pos(f)[0]
        if len(syl) - pos < pre_len:
            nuc = strip(onset_nucleus_coda(syl[pre_len])[1])
            ult = strip(onset_nucleus_coda(syl[-1])[1])
            circ = (len(nuc) == 2 or nuc in 'ηωῃῳ') and pre_len == len(syl) - 2 and ult in ('ε', 'ο', 'α')
            f = put_accent(f, len(syl) - pre_len, CIRC if circ else ACUTE)
    return f


def verb(lemma, aor=None, aor2=None, aor_mid=None, impf=True, short=False, long=False, mid=False, auto_pass=True):
    """lemma: -ω / -ομαι / -έω / -άω / -όω (+ -έομαι …).  aor: 1st aorist 1sg ind (ἔλυσα) or its
    unaugmented stem after '/': 'ἔλυσα/λυσ'; aor2: 'ἔβαλον/βαλ'; aor_mid: 'ἐγενόμην/γεν' (2nd aor. middle)."""
    out = []
    s = strip(lemma)
    dep = s.endswith('ομαι')
    stem = s[:-4] if dep else s[:-1]
    cls = stem[-1] if stem[-1:] in 'εαο' and len(stem) > 1 and stem[-2:-1] not in 'αεηιουω' or (stem[-1:] in 'εαο' and stem[-2:] in ('ιε', 'ια', 'ρα', 'υε')) else ''
    cls = stem[-1] if stem[-1:] in 'εαο' else ''
    if short or long:
        stem = mark_len(stem, '\u0306' if short else '\u0304')

    def add(form, tag):
        if form:
            out.append((nfc(strip_len(form)), tag))

    def fin(st, ends, tense, mood, voice, aug=False):
        for pn, e in ends:
            if cls and tense == 'i' and e == 'εν':
                continue
            base = (augment(st) if aug else st)
            if cls and tense in 'pi':
                add(_contracted(base, base + e, cls), 'v%s%s%s%s%s---' % (pn[0], pn[1], tense, mood, voice))
            else:
                try:
                    add(recessive(base + e), 'v%s%s%s%s%s---' % (pn[0], pn[1], tense, mood, voice))
                except Exception:
                    pass
    def fin_aug(aug_stem, ends, voice):
        pre, _, rest = aug_stem.rpartition('|')        # 'παρ|ειχ': the accent may not go back past the augment
        full = pre + rest
        aug_i = len(syllabify(pre)) if pre else 0
        for pn, e in ends:
            if cls and e == 'εν':
                continue
            f = _contracted(full, full + e, cls) if cls else rec_aug(full + e, aug_i)
            add(f, 'v%s%sii%s---' % (pn[0], pn[1], voice))
    voices = ['m'] if dep else (['a', 'm'] if mid else ['a'])
    # the present system of every active verb also has middle-passive forms (λύεται “is being freed”)
    for v in (voices if dep or mid or not auto_pass else ['a', 'm']):
        fin(stem, PRES_A if v == 'a' else PRES_M, 'p', 'i', v)
        fin(stem, IMP_A if v == 'a' else IMP_M, 'p', 'm', v)
        fin(stem, SUBJ_A if v == 'a' else SUBJ_M, 'p', 's', v)
        if cls:                                      # φιλοίην, τιμῴην, δηλοίην; φιλοῖτο, τιμῷτο
            ends = (OPT_CA_A if cls == 'α' else OPT_CA_EO) if v == 'a' else (OPT_CM_A if cls == 'α' else OPT_CM_EO)
            for pn, e in ends:
                add(strip(stem[:-1]) + e, 'v%s%spo%s---' % (pn[0], pn[1], v))
        else:
            for pn, e in (OPT_A if v == 'a' else OPT_M):
                try:
                    add(rec_opt(stem + e), 'v%s%spo%s---' % (pn[0], pn[1], v))
                except Exception:
                    pass
        if impf is True:
            fin(stem, IMPF_A if v == 'a' else IMPF_M, 'i', 'i', v, aug=True)
        elif impf:                                   # given augmented stem, e.g. 'ἑωρα' for ὁράω
            fin_aug(impf, IMPF_A if v == 'a' else IMPF_M, v)
        inf = stem + ('ειν' if v == 'a' else 'εσθαι')
        if cls:
            if v == 'a':
                add(put_accent(stem[:-1] + {'ε': 'ειν', 'α': 'αν', 'ο': 'ουν'}[cls], 1, CIRC), 'v--pna----')
            else:
                add(_contracted(stem, stem + 'εσθαι', cls), 'v--pnm----')
        else:
            add(recessive(inf), 'v--pn%s----' % v)
        # participles
        if v == 'a':
            for ends, g in ((PTC_A, 'm'), (PTC_AN, 'n'), (PTC_AF, 'f')):
                for i, e in enumerate(ends):
                    num, case = ('s' if i < 5 else 'p'), CASES[i % 5]
                    if cls:
                        try:
                            u = persistent(stem + e, recessive(stem + 'ων'))
                            if g == 'f' and case == 'g' and num == 'p':
                                u = perispomenon_ultima(u)
                            f = _contracted(stem, u, cls, accented=True)
                        except Exception:
                            f = None
                    else:
                        try:
                            f = persistent(stem + e, recessive(stem + 'ων'))
                            if g == 'f' and case == 'g' and num == 'p':
                                f = perispomenon_ultima(f)
                        except Exception:
                            f = None
                    add(f, 'v-%spp%sa%s%s-' % (num, 'a', g, case) if False else 'v-%sppa%s%s-' % (num, g, case))
        else:
            for g, ends in (('m', END2['m']), ('n', END2['n']), ('f', END1['η'] + PL1)):
                for i, e in enumerate(ends):
                    num, case = ('s' if i < 5 else 'p'), CASES[i % 5]
                    base = stem + 'ομεν'
                    if cls:
                        mlem = _contracted(stem, stem + 'ομενος', cls)
                        f = persistent(strip(mlem)[:-2] + e, mlem) if mlem else None
                    else:
                        try:
                            f = persistent(base + e, recessive(base + 'ος'))
                        except Exception:
                            f = None
                    add(f, 'v-%sppm%s%s-' % (num, g, case))
    if aor:
        a1, _, a1s = aor.partition('/')
        pre1, _, a1 = a1.rpartition('|')                 # 'ὑπ|εῖξα': prefix before the augment
        a1 = pre1 + a1
        pl1 = len(syllabify(pre1)) if pre1 else 0
        a1s = a1s or strip(a1)[1:-1]
        aug = strip(a1)[:-4] if strip(a1).endswith('αμην') else strip(a1)[:-1]
        for v in voices:
            for pn, e in (AOR_A if v == 'a' else AOR_M):
                try:
                    add(rec_aug(aug + e, pl1), 'v%s%sai%s---' % (pn[0], pn[1], v))
                except Exception:
                    pass
            for pn, e in (AOR_IMP_A if v == 'a' else AOR_IMP_M):
                try:
                    add(recessive(a1s + e), 'v%s%sam%s---' % (pn[0], pn[1], v))
                except Exception:
                    pass
            for pn, e in (SUBJ_A if v == 'a' else SUBJ_M):
                try:
                    add(recessive(a1s + e), 'v%s%sas%s---' % (pn[0], pn[1], v))
                except Exception:
                    pass
            for pn, e in (OPT1_A if v == 'a' else OPT1_M):
                try:
                    add(rec_opt(a1s + e), 'v%s%sao%s---' % (pn[0], pn[1], v))
                except Exception:
                    pass
            try:
                if v == 'a':
                    syl = syllabify(strip(a1s + 'αι'))
                    nuc = strip(onset_nucleus_coda(syl[-2])[1])
                    longv = len(nuc) == 2 or nuc in 'ηω' or (nuc in 'ιυ' and not strip(lemma).endswith('ζω'))
                    add(put_accent(strip(a1s + 'αι'), 2, CIRC if longv else ACUTE), 'v--ana----')
                else:
                    add(recessive(a1s + 'ασθαι'), 'v--anm----')
            except Exception:
                pass
            if v == 'a':
                for ends, g in ((['ᾱς', 'αντος', 'αντι', 'αντα', 'ᾱς', 'αντες', 'αντων', 'ᾱσι', 'αντας', 'αντες'], 'm'),
                                (['α\u0306ν', 'αντος', 'αντι', 'α\u0306ν', 'α\u0306ν', 'αντα', 'αντων', 'ᾱσι', 'αντα', 'αντα'], 'n'),
                                (['ασα', 'ασης', 'ασῃ', 'ασαν', 'ασα', 'ασαι', 'ασων', 'ασαις', 'ασᾱς', 'ασαι'], 'f')):
                    for i, e in enumerate(ends):
                        num, case = ('s' if i < 5 else 'p'), CASES[i % 5]
                        try:
                            f = persistent(a1s + e, recessive(a1s + 'ᾱς'))
                            if g == 'f' and case == 'g' and num == 'p':
                                f = perispomenon_ultima(f)
                            if g == 'n' and i in (0, 3, 4):           # λῦσαν, ποιῆσαν, μεῖναν
                                sy = syllabify(strip(a1s + 'αν'))
                                nu = strip(onset_nucleus_coda(sy[-2])[1])
                                lv = len(nu) == 2 or nu in 'ηω' or (nu in 'ιυ' and not strip(lemma).endswith('ζω'))
                                f = put_accent(strip(a1s + 'αν'), 2, CIRC if lv else ACUTE)
                            add(f, 'v-%sapa%s%s-' % (num, g, case))
                        except Exception:
                            pass
            else:
                for g, ends in (('m', END2['m']), ('n', END2['n']), ('f', END1['η'] + PL1)):
                    for i, e in enumerate(ends):
                        num, case = ('s' if i < 5 else 'p'), CASES[i % 5]
                        try:
                            add(persistent(a1s + 'αμεν' + e, recessive(a1s + 'αμενος')), 'v-%sapm%s%s-' % (num, g, case))
                        except Exception:
                            pass
    for spec, voice in ((aor2, 'a'), (aor_mid, 'm')):
        if not spec:
            continue
        a2, _, a2s = spec.partition('/')
        pre2, _, a2 = a2.rpartition('|')
        a2 = pre2 + a2
        pl2 = len(syllabify(pre2)) if pre2 else 0
        aug = strip(a2)[:-2] if voice == 'a' else strip(a2)[:-4]
        a2s = a2s or aug[1:]
        for pn, e in (IMPF_A if voice == 'a' else IMPF_M):
            try:
                add(rec_aug(aug + e, pl2), 'v%s%sAi%s---' % (pn[0], pn[1], voice))
            except Exception:
                pass
        for pn, e in (IMP_A if voice == 'a' else IMP_M):
            try:
                f = recessive(mark_len(a2s, '\u0306') + e)      # 2nd aorist stems have short α ι υ
                if voice == 'a' and pn == '2s' and strip(a2s) in ('λαβ', 'εἰπ', 'ἐλθ', 'εὑρ', 'ἰδ'):
                    f = put_accent(strip(a2s + e), 1, ACUTE)      # λαβέ, εἰπέ, ἐλθέ, εὑρέ, ἰδέ
                if voice == 'm' and pn == '2s':
                    f = put_accent(strip(a2s + e), 1, CIRC)      # βαλοῦ, γενοῦ
                add(f, 'v%s%sAm%s---' % (pn[0], pn[1], voice))
            except Exception:
                pass
        for pn, e in (SUBJ_A if voice == 'a' else SUBJ_M):
            try:
                add(recessive(mark_len(a2s, '\u0306') + e), 'v%s%sAs%s---' % (pn[0], pn[1], voice))
            except Exception:
                pass
        for pn, e in (OPT_A if voice == 'a' else OPT_M):
            try:
                add(rec_opt(mark_len(a2s, '\u0306') + e), 'v%s%sAo%s---' % (pn[0], pn[1], voice))
            except Exception:
                pass
        if voice == 'a':
            add(put_accent(strip(a2s) + 'ειν', 1, CIRC), 'v--Ana----')
            for ends, g in ((PTC_A, 'm'), (PTC_AN, 'n'), (PTC_AF, 'f')):
                for i, e in enumerate(ends):
                    num, case = ('s' if i < 5 else 'p'), CASES[i % 5]
                    try:
                        lem = put_accent(strip(a2s) + ('ουσα' if g == 'f' else 'ων'), 2 if g == 'f' else 1,
                                         CIRC if g == 'f' else ACUTE)
                        f = persistent(a2s + e, lem)
                        if g != 'f' and (case in 'gd' or i in (5, 6, 8, 9)):
                            f = put_accent(strip(a2s + e), 2, CIRC if i == 7 else ACUTE)
                        if g != 'f' and i in (0, 3, 4) and e in ('ον',):
                            f = put_accent(strip(a2s + e), 1, ACUTE)
                        if g == 'f' and case == 'g' and num == 'p':
                            f = perispomenon_ultima(f)
                        add(f, 'v-%sApa%s%s-' % (num, g, case))
                    except Exception:
                        pass
        else:
            add(put_accent(strip(a2s) + 'εσθαι', 2, ACUTE), 'v--Anm----')       # γενέσθαι
            for g, ends in (('m', END2['m']), ('n', END2['n']), ('f', END1['η'] + PL1)):
                for i, e in enumerate(ends):
                    num, case = ('s' if i < 5 else 'p'), CASES[i % 5]
                    try:
                        add(persistent(a2s + 'ομεν' + e, put_accent(strip(a2s) + 'ομενος', 3, ACUTE)),
                            'v-%sApm%s%s-' % (num, g, case))
                    except Exception:
                        pass
    return out


def index(entries):
    """entries: list of (lemma, kind, opts) → {form: [(lemma, tag)]}"""
    idx = defaultdict(list)
    for lemma, kind, opts in entries:
        if kind == 'v':
            forms = verb(lemma, **opts)
        elif kind == 'adj':
            forms = adj212(lemma, **opts)
        elif kind == 'n':
            forms = noun12(lemma, **opts)
        elif kind == 'n3':
            forms = noun3(lemma, **opts)
        elif kind == 'nes':
            forms = noun_es(lemma)
        elif kind == 'adjes':
            forms = adj_es(lemma)
        elif kind == 'adjdeg':
            forms = adj_degree(lemma, **opts)
        elif kind == 'raor':
            forms = root_aor(lemma, opts['spec'])
        elif kind == 'fut':
            import morph2
            forms = morph2.future(lemma, **opts)
        elif kind == 'neus':
            import morph2
            forms = morph2.noun_eus(lemma)
        elif kind == 'adjus':
            import morph2
            forms = morph2.adj_us(lemma)
        elif kind == 'nis':
            import morph2
            forms = morph2.noun_is(lemma, **opts)
        elif kind == 'cmpd':
            import morph2
            forms = morph2.compound(opts['pre'], opts['base_forms'])
        elif kind == 'adj3':
            forms = adj3(lemma, opts['neut'], opts['gen'])
        elif kind == 'numi':
            import morph2
            forms = morph2.numi(lemma, **opts)
        elif kind == 'aorp':
            import morph2
            forms = morph2.aor_pass(lemma, opts['spec'])
        elif kind == 'pfm':
            import morph2
            forms = morph2.perf_mid(lemma, opts['spec'])
        elif kind == 'pf':
            import morph2
            forms = morph2.perf_act(lemma, opts['spec'])
        else:
            forms = []
        for f, t in forms:
            if (lemma, t) not in idx[f]:
                idx[f].append((lemma, t))
    return idx


if __name__ == '__main__':
    import sys
    for w in sys.argv[1:]:
        k = 'v' if strip(w).endswith(('ω', 'ομαι')) else 'n'
        for f, t in (verb(w) if k == 'v' else noun12(w)):
            print(f, t)


# ---------------------------------------------------------------- 3rd declension
def _sigma(stem):
    """stem + -σι(ν): dentals drop, ντ drops with lengthening, κ/γ/χ → ξ, π/β/φ → ψ, ν drops"""
    s = strip(stem)
    if s.endswith('γγ'):
        return s[:-1] + 'ξι'                           # σάλπιγξι, σύριγξι
    if s.endswith('κτ'):
        return s[:-2] + 'ξι'
    for a, b in (('οντ', 'ου'), ('αντ', 'α'), ('εντ', 'ει'), ('ντ', ''), ('τ', ''), ('δ', ''), ('θ', ''),
                 ('ν', '')):
        if s.endswith(a):
            return s[:-len(a)] + b + 'σι'
    for a, b in (('κ', 'ξι'), ('γ', 'ξι'), ('χ', 'ξι'), ('π', 'ψι'), ('β', 'ψι'), ('φ', 'ψι')):
        if s.endswith(a):
            return s[:-1] + b
    return s + 'σι'


def noun3(lemma, gen, gender='m', acc=None, voc=None, pos='n'):
    """3rd declension from nominative + genitive singular (λαμπάς, λαμπάδος)."""
    out = []
    gs = strip(gen)
    stem = gs[:-2] if gs.endswith('ος') else gs[:-2]
    mono = len(syllabify(strip(lemma))) == 1
    neut = gender == 'n'

    def acc_(f, case_num):
        if mono and case_num in ('gs', 'ds', 'gp', 'dp'):
            w = put_accent(f, 1, CIRC if case_num == 'gp' else ACUTE)
            return w
        if mono and len(syllabify(strip_len(strip(f)))) == 2:
            nuc = strip(onset_nucleus_coda(syllabify(strip_len(strip(f)))[0])[1])
            longv = len(nuc) == 2 or nuc in 'ηω' or CIRC in ud.normalize('NFD', lemma)
            return put_accent(strip_len(f), 2, CIRC if longv else ACUTE)
        try:
            return persistent(f, lemma if mono else gen)
        except Exception:
            return None

    SA = 'α\u0306'                                      # short α: the accent rules need to know
    forms = {'ns': lemma, 'gs': stem + 'ος', 'ds': stem + 'ι'}
    if neut:
        forms.update(ass=lemma, np=stem + SA, ap=stem + SA)
    else:
        forms.update(ass=acc or stem + SA, np=stem + 'ες', ap=stem + SA + 'ς')
    forms.update(gp=stem + 'ων', dp=_sigma(stem))
    for k, f in forms.items():
        if k in ('ns',) or (neut and k == 'ass') or (k == 'ass' and acc):
            w = f
        else:
            w = acc_(f, k)
        if not w:
            continue
        case = {'n': 'n', 'g': 'g', 'd': 'd', 'a': 'a'}[k[0]]
        num = 's' if k.endswith('s') else 'p'
        w = strip_len(w)
        out.append((nfc(w), '%s-%s---%s%s-' % (pos, num, gender if gender != 'c' else 'm', case)))
        if k == 'dp':
            out.append((nfc(w) + 'ν', '%s-p---%sd-' % (pos, gender if gender != 'c' else 'm')))
        if gender == 'c':
            out.append((nfc(w), '%s-%s---f%s-' % (pos, num, case)))
    out.append((nfc(voc or lemma), '%s-s---%sv-' % (pos, 'm' if gender == 'c' else gender)))
    return out


def adj3(lemma, neut, gen):
    """2nd class adjectives in -ων, -ον (σώφρων, σῶφρον, σώφρονος)"""
    out = [(f, 'a' + t[1:]) for f, t in noun3(lemma, gen, 'c', pos='a')]
    out += [(f, 'a' + t[1:]) for f, t in noun3(neut, gen, 'n', pos='a')]
    b = ''.join(c for c in ud.normalize('NFD', lemma) if not ud.combining(c))
    if b.endswith(('ιων', 'ττων')) or b in ('μειζων', 'χειρων', 'αμεινων', 'ραων', 'ῥαων'):
        st = lemma[:-2]                              # βελτίω, βελτίους (from -ονα, -ονες, -ονας)
        for f, tags in ((st + 'ω', ('a-s---ma-', 'a-s---fa-', 'a-p---nn-', 'a-p---na-')),
                        (st + 'ους', ('a-p---mn-', 'a-p---fn-', 'a-p---ma-', 'a-p---fa-'))):
            out += [(nfc(f), t) for t in tags]
    return out


def noun_es(lemma):
    """3rd declension neuters in -ος (τὸ τεῖχος, τοῦ τείχους)"""
    s = strip(lemma)
    stem = s[:-2]
    out = []
    forms = [('ns', lemma), ('as', lemma), ('vs', lemma), ('gs', stem + 'ους'), ('ds', stem + 'ει'), ('np', stem + 'η'),
             ('ap', stem + 'η'), ('gp', stem + 'ων'), ('dp', stem + 'εσι'), ('dp', stem + 'εσιν')]
    for k, f in forms:
        if k in ('ns', 'as', 'vs'):
            w = lemma
        elif k == 'gp':
            w = perispomenon_ultima(f)
        else:
            try:
                w = persistent(f, lemma)
            except Exception:
                continue
        case = {'n': 'n', 'a': 'a', 'v': 'v', 'g': 'g', 'd': 'd'}[k[0]]
        out.append((nfc(strip_len(w)), 'n-%s---n%s-' % (k[1], case)))
    return out


def adj_es(lemma):
    """adjectives in -ής, -ές with stems in -εσ- (ἀληθής, ἀληθές; gen. ἀληθοῦς)"""
    s = strip(lemma)
    stem = s[:-2]
    mf = [('ns', 'ής'), ('gs', 'οῦς'), ('ds', 'εῖ'), ('as', 'ῆ'),
          ('np', 'εῖς'), ('gp', 'ῶν'), ('dp', 'έσι'), ('dp', 'έσιν'), ('ap', 'εῖς'), ('vp', 'εῖς')]
    nt = [('ns', 'ές'), ('gs', 'οῦς'), ('ds', 'εῖ'), ('as', 'ές'), ('vs', 'ές'),
          ('np', 'ῆ'), ('gp', 'ῶν'), ('dp', 'έσι'), ('dp', 'έσιν'), ('ap', 'ῆ'), ('vp', 'ῆ')]
    out = []
    if not ud.normalize('NFD', lemma).rstrip('ς').endswith(ACUTE):      # πλήρης, πλῆρες: accent stays on the stem
        mf = [('ns', 'ης'), ('gs', 'ους'), ('ds', 'ει'), ('as', 'η'), ('np', 'εις'), ('gp', 'ων'),
              ('dp', 'εσι'), ('dp', 'εσιν'), ('ap', 'εις'), ('vp', 'εις')]
        nt = [('ns', 'ες'), ('gs', 'ους'), ('ds', 'ει'), ('as', 'ες'), ('vs', 'ες'), ('np', 'η'), ('gp', 'ων'),
              ('dp', 'εσι'), ('dp', 'εσιν'), ('ap', 'η'), ('vp', 'η')]
        for g, ends in (('m', mf), ('f', mf), ('n', nt)):
            for k, e in ends:
                out.append((nfc(strip_len(persistent(stem + e, lemma))), 'a-%s---%s%s-' % (k[1], g, k[0])))
        return out
    for g, ends in (('m', mf), ('f', mf), ('n', nt)):
        for k, e in ends:
            out.append((nfc(stem + e), 'a-%s---%s%s-' % (k[1], g, k[0])))
    return out


def adj_degree(lemma, cmp=None, sup=None):
    """regular comparison: forms of the comparative / superlative (σοφώτερος, σοφώτατος) tagged as forms of the
    positive (lemma) with degree c / s"""
    out = []
    for form, deg in ((cmp, 'c'), (sup, 's')):
        if form:
            out += [(f, t[:8] + deg) for f, t in adj212(form)]
    return out


def root_aor(lemma, spec):
    """root (athematic) aorist: spec 'ἔβην/βη/βα' = augmented 1st sg. / long stem / short stem; compounds with the
    prefix before the augment marked: 'ἀν|έβην/ἀναβη/ἀναβα'.   ἔβην … ἔβησαν, βῆναι, βῆθι, βάς βᾶσα βάν"""
    a, long_stem, short_stem = spec.split('/')
    pre, _, a = a.rpartition('|')
    a = pre + a
    pl = len(syllabify(pre)) if pre else 0
    aug = strip(a)[:-1]
    out = []
    for pn, e in (('1s', 'ν'), ('2s', 'ς'), ('3s', ''), ('1p', 'μεν'), ('2p', 'τε'), ('3p', 'σαν')):
        out.append((nfc(rec_aug(aug + e, pl)), 'v%s%sRia---' % (pn[0], pn[1])))
    out.append((nfc(put_accent(strip(long_stem) + 'ναι', 2, CIRC)), 'v--Rna----'))
    for pn, e in (('2s', 'θι'), ('2p', 'τε')):
        out.append((nfc(recessive(long_stem + e)), 'v%s%sRma---' % (pn[0], pn[1])))
    ls = strip(long_stem)                            # subjunctive: βῶ βῇς βῇ βῶμεν βῆτε βῶσι; γνῶ γνῷς γνῷ … γνῶτε
    if ls[-1] in 'ηω':
        o = ls[-1] == 'ω'
        for pn, e in (('1s', 'ῶ'), ('2s', 'ῷς' if o else 'ῇς'), ('3s', 'ῷ' if o else 'ῇ'), ('1p', 'ῶμεν'),
                      ('2p', 'ῶτε' if o else 'ῆτε'), ('3p', 'ῶσι'), ('3p', 'ῶσιν')):
            out.append((nfc(ls[:-1] + e), 'v%s%sRsa---' % (pn[0], pn[1])))
    else:
        for pn, e in SUBJ_A:
            try:
                out.append((nfc(strip_len(recessive(ls + e))), 'v%s%sRsa---' % (pn[0], pn[1])))
            except Exception:
                pass
    for pn, e in OPT_R:                              # βαίην, γνοίην, σταίην; (aorist passive) λυθείην
        out.append((nfc(strip(short_stem) + e), 'v%s%sRoa---' % (pn[0], pn[1])))
    # participle: the accent stays on the stem vowel (βάς, βάντος, βᾶσα; ἀναβάς)
    st = strip(short_stem)
    v = st[-1]
    base = st[:-1]
    lv = {'α': 'ᾱ', 'ο': 'ου', 'υ': 'ῡ', 'ε': 'ει'}[v]
    n_syl = len(syllabify(st))                       # the accented syllable, counted from the start
    def acc(form, circ_ok=True):
        syl = syllabify(form)
        pos_from_end = len(syl) - n_syl + 1
        d = ud.normalize('NFD', form)
        long_v = '\u0304' in d or 'ου' in syl[n_syl - 1] or 'ει' in syl[n_syl - 1]
        ult = strip_len(syl[-1])
        short_ult = not any(x in ult for x in ('ω', 'η', 'ου', 'αι' if False else 'ῃ')) and ult not in ('ᾱς',)
        if pos_from_end == 2 and long_v and circ_ok and short_ult:
            return put_accent(form, 2, CIRC)
        return put_accent(form, pos_from_end, ACUTE)
    m_ends = [('ns', lv + 'ς'), ('gs', v + 'ντος'), ('ds', v + 'ντι'), ('as', v + 'ντα'), ('vs', lv + 'ς'),
              ('np', v + 'ντες'), ('gp', v + 'ντων'), ('dp', lv + 'σι'), ('dp', lv + 'σιν'), ('ap', v + 'ντας'),
              ('vp', v + 'ντες')]
    n_ends = [('ns', v + 'ν'), ('gs', v + 'ντος'), ('ds', v + 'ντι'), ('as', v + 'ν'), ('vs', v + 'ν'),
              ('np', v + 'ντα'), ('gp', v + 'ντων'), ('dp', lv + 'σι'), ('dp', lv + 'σιν'), ('ap', v + 'ντα'),
              ('vp', v + 'ντα')]
    f_ends = [('ns', lv + 'σα'), ('gs', lv + 'σης'), ('ds', lv + 'σῃ'), ('as', lv + 'σαν'), ('vs', lv + 'σα'),
              ('np', lv + 'σαι'), ('gp', lv + 'σων'), ('dp', lv + 'σαις'), ('ap', lv + 'σας'), ('vp', lv + 'σαι')]
    for g, ends in (('m', m_ends), ('n', n_ends), ('f', f_ends)):
        for k, e in ends:
            form = base + e
            if g == 'f' and k == 'gp':
                f = perispomenon_ultima(form)
            elif g == 'f' and k in ('gs', 'ds', 'ap', 'dp'):
                f = put_accent(form, len(syllabify(form)) - n_syl + 1, ACUTE)
            else:
                f = acc(form)
            out.append((nfc(strip_len(f)), 'v-%sRpa%s%s-' % (k[1], g, k[0])))
    return out
