# -*- coding: utf-8 -*-
"""Regular principal parts for the syllabus shorthand  `v reg [pre=κατα]`  (book 2).
ποιέω → ἐποίησα, ποιήσω, πεποίηκα, πεποίημαι, ἐποιήθην;  πιστεύω, λύω, παύω, θαυμάζω, νομίζω, φυλάττω likewise."""
import unicodedata as ud
from morph import nfc, strip, augment

SMOOTH, ROUGH = '̓', '̔'
VOW = 'αεηιουω'
ELIDE = {'ἀνα': 'ἀν', 'ἀπο': 'ἀπ', 'δια': 'δι', 'ἐπι': 'ἐπ', 'κατα': 'κατ', 'μετα': 'μετ', 'παρα': 'παρ',
         'ὑπο': 'ὑπ', 'ἀντι': 'ἀντ', 'ἀμφι': 'ἀμφ', 'ἐκ': 'ἐξ', 'ἐμ': 'ἐν', 'ἐγ': 'ἐν', 'ἐλ': 'ἐν',
         'συμ': 'συν', 'συγ': 'συν', 'συλ': 'συν', 'συ': 'συν', 'ἐπανα': 'ἐπαν', 'συνα': 'συν',
         'προσανα': 'προσαν', 'ἐξανα': 'ἐξαν', 'παρακατα': 'παρακατ', 'ἀντικατα': 'ἀντικατ',
         'ἐγκατα': 'ἐγκατ', 'συγκατα': 'συγκατ', 'ἐπικατα': 'ἐπικατ', 'ὑπεκ': 'ὑπεξ', 'προσεπι': 'προσεπ',
         'διεκ': 'διεξ', 'ἀντεπι': 'ἀντεπ', 'συνεπι': 'συνεπ', 'ἐπεκ': 'ἐπεξ', 'συναπο': 'συναπ',
         'συνδια': 'συνδι', 'ἐναπο': 'ἐναπ', 'ἀντιπαρα': 'ἀντιπαρ', 'προκατα': 'προκατ'}


def bare_breath(w):
    d = ud.normalize('NFD', w)
    return nfc(''.join(c for c in d if c not in (SMOOTH, ROUGH)))


def add_breath(w, rough=False):
    """breathing on a vowel-initial stem (on the 2nd vowel of a diphthong)"""
    if not w or w[0] not in VOW:
        return w
    i = 1 if len(w) > 1 and w[:2] in ('αι', 'ει', 'οι', 'αυ', 'ευ', 'ου', 'ηυ', 'υι') else 0
    return nfc(w[:i + 1] + (ROUGH if rough else SMOOTH) + w[i + 1:])


def split(lemma, pre):
    """(prefix as in the lemma, elided prefix for the augment, base stem with breathing) — all unaccented"""
    s = strip(lemma)
    if not pre:
        return '', '', s
    pre = strip(pre)
    assert s.startswith(pre), (lemma, pre)
    base = s[len(pre):]
    rough = pre[-1] in 'φθχ'
    return pre, ELIDE.get(pre, pre), add_breath(base, rough)


def redup(base):
    """reduplicated perfect stem start: λυ → λελυ, γραφ → γεγραφ, φιλη → πεφιλη, στρατευ → ἐστρατευ, ἀγαπη → ἠγαπη"""
    b = bare_breath(base)
    if base[0] in VOW or base != b:
        return augment(base)
    c = b[0]
    two = b[:2]
    if c in 'ζξψρ' or (b[1] not in VOW + 'λρ' and two not in ('μν',) or two in ('γν', 'γλ', 'βλ')) and two not in ('θν', 'κτ'[:0]):
        if c == 'ρ':
            return 'ἐρ' + b
        return 'ἐ' + b
    c2 = {'φ': 'π', 'θ': 'τ', 'χ': 'κ'}.get(c, c)
    return c2 + 'ε' + b


def regular_parts(lemma, pre=None):
    """→ dict of specs (aor, fut, pf, pfm, aorp) in the syllabus notation, or {} if the lemma's class is unknown"""
    pfx, pel, base = split(lemma, pre)
    dep = base.endswith('ομαι')
    st = base[:-4] if dep else base[:-1]
    b = bare_breath(st)
    stems = None                                   # (aorist/future stem, perfect active stem, perf. mid. stem, aor. pass. stem)
    fut_contract = False
    if b.endswith(('ε', 'α', 'ο')) and len(b) > 1:
        v = b[-1]
        lv = {'ε': 'η', 'ο': 'ω'}.get(v) or ('α' if b[-2] in 'ειρ' else 'η')
        s0 = st[:-1] + lv
        stems = (s0 + 'σ', s0 + 'κ', s0, s0 + 'θ')
    elif b.endswith(('ευ', 'αυ', 'ου')) or b.endswith('υ') or b.endswith('ι'):
        stems = (st + 'σ', st + 'κ', st, st + 'θ')
    elif b.endswith(('αζ', 'ιζ')):
        s0 = st[:-1]
        stems = (s0 + 'σ', s0 + 'κ', s0 + 'σ', s0 + 'σθ')
        fut_contract = b.endswith('ιζ')
    elif b.endswith('ττ'):
        s0 = st[:-2]
        stems = (s0 + 'ξ', s0 + 'χ', s0 + 'γ', s0 + 'χθ')
    else:
        return {}
    sa, sr, sm, sp = stems

    def aug(stem):
        a = augment(stem)
        return (pel + '|' + bare_breath(a)) if pfx else a
    full = lambda stem: pfx + bare_breath(stem) if pfx else stem
    o = {}
    o['aor'] = aug(sa) + ('αμην' if dep else 'α') + '/' + full(sa)
    if fut_contract:
        o['fut'] = full(sa[:-1]) + ('οῦμαι' if dep else 'ῶ')
    else:
        o['fut'] = full(sa) + ('ομαι' if dep else 'ω')
    rd = redup(st[:0] + sm)                        # reduplication of the stem
    rdk = redup(sr)
    pre_r = (pel if rd[0] in 'ἐἠὠᾐᾠηω' or bare_breath(rd)[0] in VOW else pfx)
    if not dep:
        o['pf'] = (pre_r + '|' + bare_breath(rdk) if pfx else rdk) + 'α'
    o['pfm'] = (pre_r + '|' + bare_breath(rd) if pfx else rd) + 'μαι'
    o['aorp'] = aug(sp) + 'ην' + '/' + full(sp)
    return o


if __name__ == '__main__':
    import sys
    for w in sys.argv[1:]:
        l, _, p = w.partition('/')
        print(l, regular_parts(l, p or None))
