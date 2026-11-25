"""Verb dual forms by rule (Smyth §§ 462–466) from the generated plural / 3rd singular forms of a verb.

usage: dualgen.py LEMMA …        (repository root) → lines for project/forms_dual.txt on stdout
2nd dual = 2nd pl. with -τε → -τον, -σθε → -σθον. 3rd dual = the 2nd dual in primary tenses and the subjunctive;
in secondary tenses and the optative -την / -σθην with the accent on the penult (the ultima is long). Imperative:
2nd dual from the 2nd pl., 3rd dual = 3rd sg. + ν (λυέτω → λυέτων, λυέσθω → λυέσθων)."""
import os
import re
import sys
import unicodedata as ud

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
os.chdir(os.path.join(ROOT, 'project'))
sys.path.insert(0, os.getcwd())
import check2 as K  # noqa: E402

ACC = {'́', '̀', '͂'}
VOW = set('αεηιουω')


def strip_acc(w):
    d = ud.normalize('NFD', w)
    return ud.normalize('NFC', ''.join(c for c in d if c not in ACC))


def acute_last_syllable(base):
    """acute on the last vowel (group) of base: ἐλυσα → ἐλυσά, ἐποιει → ἐποιεί"""
    d = list(ud.normalize('NFD', strip_acc(base)))
    letters = [i for i, c in enumerate(d) if not ud.combining(c)]
    idx = [i for i in letters if d[i].lower() in VOW]
    if not idx:
        return base
    last = idx[-1]
    j = letters.index(last)
    if j > 0 and d[letters[j - 1]].lower() in VOW and (d[letters[j - 1]].lower() + d[last].lower()) in (
            'αι', 'ει', 'οι', 'υι', 'αυ', 'ευ', 'ου', 'ηυ'):
        pass                                     # the accent goes on the second letter of the diphthong anyway
    k = last + 1
    while k < len(d) and ud.combining(d[k]):
        k += 1
    d.insert(k, '́')
    return ud.normalize('NFC', ''.join(d))


out = {}
for lemma in sys.argv[1:]:
    lf = {}
    for f, al in list(K.GEN.items()) + [(f, [tuple(a) for a in al if len(a) == 2]) for f, al in K.EXTRA.items()]:
        for l, t in al:
            if l == lemma and not K.bare(f).startswith('δυναμ'):     # (the generator's bogus δυναμῶ …)
                lf.setdefault(t[:9], []).append(f)
    for t, fs in lf.items():
        if t[0] != 'v':
            continue
        person, num, tense, mood, voice = t[1], t[2], t[3], t[4], t[5]
        for f in fs:
            if num == 'p' and person == '2' and mood in 'isom':
                m = re.search(r'(σθε|φθε|χθε|λθε|τε)$', f)
                if not m:
                    continue
                d2 = f[:m.start()] + m.group(1)[:-1] + 'ον'
                out.setdefault(d2, set()).add('%s v2d%s%s%s---' % (lemma, tense, mood, voice))
                if mood == 'm':
                    continue
                secondary = mood == 'o' or mood == 'i' and tense in 'iaARPl'
                if secondary:
                    d3 = acute_last_syllable(f[:m.start()]) + m.group(1)[:-1] + 'ην'
                else:
                    d3 = d2
                out.setdefault(d3, set()).add('%s v3d%s%s%s---' % (lemma, tense, mood, voice))
            if num == 's' and person == '3' and mood == 'm' and re.search(r'(σθω|τω)$', f):
                out.setdefault(f + 'ν', set()).add('%s v3d%s%s%s---' % (lemma, tense, mood, voice))
for f in sorted(out):
    print('%s = %s' % (f, ' | '.join(sorted(out[f]))))
