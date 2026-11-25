"""Inflection schemes of nouns, adjectives and participles, after the tables of Smyth (§211–310, §286–301) and
Wiktionary's Appendix:Ancient_Greek_grammar_tables. check2.py uses them for one grammar key per cell:
scheme:case.number(.gender), e.g. 3κ:gen.s (φύλακος), Aυς:dat.p.f (βαθείαις), Pας:gen.s.m (λύσαντος).

A word's scheme comes from its own generated forms (nom. / gen. / acc. / voc. sg.), so a new syllabus word falls
into its table without a list. Lemma-specific words (check2.SPECIFIC: pronouns, πόλις, πατήρ …) keep their own
keys and are not classed here."""
import re
import unicodedata as ud

NOUN_SCHEMES = {   # code: (Smyth §, the table it stands for, an example)
    '1ας': ('§222', '1st decl. masc. in -ᾱς', 'νεανίας'),
    '1ης': ('§222', '1st decl. masc. in -ης, voc. -η', 'Ἀτρείδης'),
    '1της': ('§222', '1st decl. masc. in -της / compounds, voc. -ᾰ', 'στρατιώτης'),
    '1α': ('§216', '1st decl. fem. in -ᾱ / -ᾰ, gen. -ᾱς', 'χώρα, ἀλήθεια'),
    '1αη': ('§216', '1st decl. fem. in -ᾰ, gen. -ης', 'θάλαττα'),
    '1η': ('§216', '1st decl. fem. in -η', 'τιμή'),
    '2': ('§230', '2nd decl. masc. in -ος', 'ἄνθρωπος'),
    '2f': ('§230', '2nd decl. fem. in -ος', 'ὁδός'),
    '2n': ('§230', '2nd decl. neuter in -ον', 'δῶρον'),
    '2c': ('§235', '2nd decl. contracted masc. -οῦς', 'νοῦς, πλοῦς'),
    '2cn': ('§235', '2nd decl. contracted neuter -οῦν', 'ὀστοῦν'),
    '2att': ('§237', 'Attic 2nd decl. -ώς', 'λεώς'),
    '3κ': ('§256', 'velar stem (κ γ χ), nom. -ξ', 'φύλαξ'),
    '3π': ('§256', 'labial stem (π β φ), nom. -ψ', 'κλώψ'),
    '3τ': ('§257', 'dental stem (τ δ θ), acc. -α', 'ἐλπίς, τάπης'),
    '3τν': ('§257', 'dental stem, barytone -ις / -υς, acc. -ν', 'χάρις, ὄρνις'),
    '3αντ': ('§258', 'ντ-stem, nom. -ᾱς', 'γίγας'),
    '3οντ': ('§258', 'ντ-stem, nom. -ων, voc. -ον', 'γέρων'),
    '3ουντ': ('§258', 'ντ-stem, nom. -ούς', 'ὀδούς'),
    '3ματ': ('§258', 'neuter τ-stem in -μα', 'σῶμα'),
    '3τn': ('§258', 'other neuter τ-stems', 'φῶς, τέρας'),
    '3ν': ('§259', 'nasal stem, vowel unchanged', 'Ἕλλην, χειμών, ἀκτίς'),
    '3ν2': ('§259', 'nasal stem, η/ε or ω/ο alternating', 'ποιμήν, ἡγεμών, γείτων'),
    '3ρ': ('§259', 'liquid stem (ρ)', 'ῥήτωρ, κλητήρ'),
    '3ηρ': ('§262', 'syncopated -ηρ stems', 'πατήρ, ἀνήρ'),
    '3ωος': ('§267', 'vowel stem -ως, gen. -ωος', 'ἥρως'),
    '3υος': ('§268', 'vowel stem -ῡς, gen. -ῠος', 'ἰχθύς'),
    '3ις': ('§268', 'vowel stem -ις, gen. -εως', 'πόλις, δύναμις'),
    '3υς': ('§268', 'vowel stem -υς, gen. -εως', 'πῆχυς, πέλεκυς'),
    '3υn': ('§268', 'neuter -υ, gen. -εως', 'ἄστυ'),
    '3ευς': ('§275', 'diphthong stem -εύς', 'βασιλεύς'),
    '3ους': ('§275', 'diphthong stem -οῦς', 'βοῦς'),
    '3αυς': ('§275', 'diphthong stem -αῦς', 'γραῦς, ναῦς'),
    '3ω': ('§279', 'stem in -οι, nom. -ώ', 'ἠχώ, πειθώ'),
    '3ωςο': ('§266', 'σ-stem -ώς, gen. -οῦς', 'αἰδώς'),
    '3εσ': ('§263', 'σ-stem masc./fem. -ης, gen. -ους', 'τριήρης, Σωκράτης'),
    '3κλης': ('§265', 'σ-stem -κλῆς', 'Περικλῆς'),
    '3εσn': ('§263', 'σ-stem neuter -ος, gen. -ους', 'γένος, τεῖχος'),
    '3ασn': ('§264', 'σ-stem neuter -ας, gen. -ως', 'γέρας, κρέας'),
}
ADJ_SCHEMES = {
    'Aοη': ('§287', '-ος -η -ον', 'σοφός'),
    'Aοα': ('§287', '-ος -ᾱ -ον', 'ἄξιος, δίκαιος'),
    'A2': ('§288', '-ος -ον, two endings', 'ἄφθονος, ἀδύνατος'),
    'Aους': ('§290', 'contracted -οῦς -ῆ / -ᾶ -οῦν', 'χρυσοῦς, ἀργυροῦς'),
    'A2c': ('§290', 'contracted two endings -ους -ουν', 'εὔνους'),
    'Aως': ('§289', 'Attic -ως -ων', 'ἵλεως'),
    'Aυς': ('§297', '-ύς -εῖα -ύ', 'βαθύς, ἡδύς'),
    'Aων': ('§292', '-ων -ον', 'εὐδαίμων, σώφρων'),
    'Aιων': ('§293', 'comparative -ων -ον', 'βελτίων'),
    'Aης': ('§292', '-ής -ές', 'ἀληθής'),
    'Aας': ('§298', '-ᾱς -αινα -ᾰν', 'μέλας, τάλας'),
    'Aεις': ('§299', '-εις -εσσα -εν', 'χαρίεις'),
    'A3': ('§292', 'consonant stems, two endings', 'ἄχαρις, ἄχειρ'),
}
PTC_SCHEMES = {
    'Pων': ('§301', '-ων -ουσα -ον', 'λύων, λιπών, ὤν, ἑκών'),
    'Pεων': ('§310', 'contract -ῶν -οῦσα -οῦν', 'ποιῶν, δηλῶν, μενῶν'),
    'Pαων': ('§310', 'contract -ῶν -ῶσα -ῶν', 'τιμῶν'),
    'Pας': ('§301', '-ᾱς -ᾱσα -ᾰν', 'λύσας, στάς'),
    'Pεις': ('§301', '-εις -εισα -εν', 'λυθείς, τιθείς'),
    'Pους': ('§301', '-ους -ουσα -ον', 'διδούς'),
    'Pυς': ('§301', '-ύς -ῦσα -ύν', 'δεικνύς'),
    'Pως': ('§301', '-ώς -υῖα -ός', 'λελυκώς, εἰδώς'),
    'Pωσ': ('§309', '-ώς -ῶσα -ός', 'ἑστώς'),
    'Pμεν': ('§302', '-μενος -μένη -μενον', 'λυόμενος'),
}

VEL, LAB, DEN = set('κγχ'), set('πβφ'), set('τδθ')
# words without generated forms (the treebank supplies them) or with a paradigm the rules misread
OVERRIDE = {'ἵλεως': 'Aως', 'χάρις': '3τν', 'εἰκός': '3τn', 'ἕως': '2att', 'Ἐρινύς': '3υος',
            'χρώς': '3τ', 'φιλότης': '3τ', 'Ἀχαρνεύς': '3ευς', 'ἥμισυς': 'Aυς', 'πολύμητις': 'A3', 'Ἰάς': 'A3',
            'ἡμιθνής': 'A3', 'τριακοντούτης': 'Aης', 'πύλαι': '1η', 'πύλη': '1η', 'Θερμοπύλαι': '1η', 'Ἀθῆναι': '1η',
            'Μυκῆναι': '1η', 'Μακεδών': '3ν2', 'Φοῖνιξ': '3κ', 'Φοίνικες': '3κ', 'στάδιον': '2', 'Διονύσια': '2n',
            'γραῦς': '3αυς', 'Περικλῆς': '3κλης', 'πειθώ': '3ω', 'αἰδώς': '3ωςο', 'ὀδούς': '3ουντ', 'εὔνους': 'A2c',
            'χαρίεις': 'Aεις'}


def noun_scheme(F, d, gender):
    """F(case, num) → a bare (accentless) form of the word or ''; d = check2.decl() class"""
    N, G, A, V = F('n', 's'), F('g', 's'), F('a', 's'), F('v', 's')
    if not (N or G or A or V or F('n', 'p') or F('g', 'p') or F('d', 'p') or F('a', 'p')):
        return None                                    # no forms of its own: by the citation form
    if d == '1f':
        if not (N or G or A):
            return plural_scheme(F, gender)
        if N.endswith('η') or A.endswith('ην'):
            return '1η'
        return '1αη' if G.endswith('ησ') else '1α'
    if d == '1m':
        if N.endswith('ασ'):
            return '1ας'
        return '1της' if V.endswith('α') else '1ης'
    if d == '2':
        return '2f' if gender == 'f' else '2'
    if d == '2n':
        return '2n'
    if d == '2c':
        return '2cn' if gender == 'n' else '2c'
    if N.endswith('ωσ') and G.endswith('ω'):
        return '2att'                                  # λεώς, λεώ; ταώς; ἕως
    if N.endswith('ουσ') and G.endswith('ου'):
        return '2c'                                    # Ἀλκίνους, ἐπίπλους
    if gender == 'n' and N.endswith('οσ') and G.endswith('ουσ'):
        d = '3esn'                                     # πάθος, πάθους
    if not N and not G:
        return plural_scheme(F, gender)
    if d in ('3es', '3esn'):
        if gender == 'n':
            return '3ασn' if N.endswith('ασ') else '3εσn'
        return '3κλης' if N.endswith('κλησ') else '3εσ'
    if not G:
        return None
    if G.endswith('εωσ'):
        if N.endswith('ευσ'):
            return '3ευς'
        if gender == 'n':
            return '3υn'
        return '3ις' if N.endswith('ισ') else '3υς'
    if G.endswith('ουσ') and N.endswith('ω'):
        return '3ω'
    if G.endswith('ουσ') and N.endswith('ωσ'):
        return '3ωςο'
    if G.endswith('ωοσ'):
        return '3ωος'
    if G.endswith('υοσ') and N.endswith('υσ'):
        return '3υος'
    if G.endswith('ωσ') and N.endswith('ων'):
        return '2att'
    if not G.endswith('οσ'):
        return None
    st = G[:-2]
    last = st[-1:]
    if last in VEL or st.endswith('κτ'):
        return '3κ'                                    # ἄναξ, ἄνακτος: nom. and dat. pl. in -ξ like φύλαξ
    if last in LAB:
        return '3π'
    if last in DEN:
        if st.endswith('ντ'):
            if N.endswith('ουσ'):
                return '3ουντ'
            return '3αντ' if N.endswith('ασ') else '3οντ'
        if gender == 'n':
            return '3ματ' if st.endswith('ματ') else '3τn'
        return '3τν' if A.endswith('ν') else '3τ'
    if last == 'ν':
        if N.endswith('ην') and st.endswith('εν') or N.endswith('ων') and st.endswith('ον'):
            return '3ν2'
        return '3ν'
    if last == 'ρ':
        if N.endswith('ηρ') and not st.endswith(('ηρ', 'ερ')):
            return '3ηρ'
        return '3ρ'
    return None


def plural_scheme(F, gender):
    """plural-only nouns (Ἀθῆναι, Δελφοί, Ἕλληνες, τὰ Ὀλύμπια …)"""
    Np, Gp, Dp = F('n', 'p'), F('g', 'p'), F('d', 'p')
    if Np.endswith('αι'):
        return '1η'                                    # Ἀθῆναι, Θερμοπύλαι: the plural of τιμή
    if Np.endswith('οι') or Dp.endswith('οισ') and gender != 'n':
        return '2'
    if gender == 'n':
        if Dp.endswith('οισ') or Np.endswith('α') and not Np.endswith('εα') and not Dp:
            return '2n'
        return '3εσn' if Np.endswith('εα') or Np.endswith('η') else '3τn'
    if Np.endswith('εισ'):
        return '3ις'
    if Gp.endswith('ων'):
        return noun_scheme(lambda c, n: {('g', 's'): Gp[:-2] + 'οσ'}.get((c, n), ''), '3', gender)
    return None


COMPAR = {'χείρων', 'ἀμείνων', 'μείων', 'πλείων', 'ἥττων', 'κρείττων', 'ἐλάττων', 'θάττων', 'μείζων', 'ῥᾴων'}


def adj_scheme(F, lemma, deg):
    """F(case, num, gender) → bare form of this degree; deg: '-' positive, 'c', 's'"""
    Nm, Nf, Nn, Gm = F('n', 's', 'm'), F('n', 's', 'f'), F('n', 's', 'n'), F('g', 's', 'm')
    if Nm.endswith('οσ') and Nn.endswith('ο') and not Nn.endswith('ον'):
        return 'Aπρ'                               # ἐκεῖνος, -η, -ο: pronominal neuter
    if Nm.endswith('οσ') or deg in 'cs' and Nm.endswith(('τεροσ', 'τατοσ', 'ιστοσ')):
        if not Nf or Nf == Nm:
            return 'A2'
        return 'Aοη' if Nf.endswith('η') else 'Aοα'
    if Nm.endswith('ουσ') and Nn.endswith('ουν') and Gm.endswith('ου'):
        return 'A2c' if not Nf or Nf == Nm else 'Aους'     # εὔνους, -ουν; χρυσοῦς, -ῆ, -οῦν
    if Nm.endswith('ωσ') and (Gm.endswith('ω') or Nn.endswith('ων')):
        return 'Aως'
    if Nm.endswith('υσ') and Nf.endswith('εια'):
        return 'Aυς'
    if Nm.endswith('ων') and Gm.endswith('ονοσ'):
        return 'Aιων' if deg == 'c' or lemma in COMPAR or Nm.endswith(('ιων', 'ττων', 'ζων')) else 'Aων'
    if Nm.endswith('ων') and Nf.endswith('ουσα'):
        return 'Pων'                               # ἑκών, ἄκων: participle endings
    if Nm.endswith('ησ') and Gm.endswith('ουσ'):
        return 'Aης'
    if Nm.endswith('ασ') and Nf.endswith('αινα'):
        return 'Aας'
    if Nm.endswith('εισ') and Nf.endswith('εσσα'):
        return 'Aεις'
    if Gm.endswith('οσ'):
        return 'A3'                                # ἄχαρις, -ιτος; ἄχειρ, -ος: consonant stems
    return None


def lemma_scheme(lemma, pos, gender, bare):
    """fallback for a word without generated forms (its forms come from the treebank): by the citation form"""
    b = bare(lemma)
    if pos == 'a':
        if b.endswith(('οι', 'οσ')):
            return 'Aοα' if b[:-2][-1:] in 'ειρ' else 'Aοη'
        return {'υσ': 'Aυς', 'ησ': 'Aης', 'ων': 'Aων'}.get(b[-2:])
    if b.endswith('οσ'):
        return '2f' if gender == 'f' else '2'
    if b.endswith('ον') and gender == 'n':
        return '2n'
    if b.endswith('η'):
        return '1η'
    if b.endswith('α') and gender == 'f':
        return '1α' if b[-2:-1] in 'ειρ' else '1αη'
    if b.endswith('ευσ'):
        return '3ευς'
    if b.endswith('μα') and gender == 'n':
        return '3ματ'
    return None


def ptc_scheme(nom_m, nom_f, voice, nom_m_accented=''):
    """the participle's nom. sg. masc. and fem. (bare) and the voice code → a PTC_SCHEMES code"""
    if nom_m.endswith('μενοσ'):
        return 'Pμεν'
    if nom_f.endswith('υια'):
        return 'Pως'
    if nom_m.endswith('ωσ') and nom_f.endswith('ωσα'):
        return 'Pωσ'
    if nom_m.endswith('ωσ'):
        return 'Pως'
    if nom_m.endswith('ων'):
        if nom_f.endswith('ωσα'):
            return 'Pαων'
        if '\u0342' in ud.normalize('NFD', nom_m_accented)[-3:] and nom_f.endswith('ουσα'):
            return 'Pεων'
        return 'Pων'
    if nom_m.endswith('ασ'):
        return 'Pας'
    if nom_m.endswith('εισ'):
        return 'Pεις'
    if nom_m.endswith('ουσ'):
        return 'Pους'
    if nom_m.endswith('υσ'):
        return 'Pυς'
    return None


# Which genders share one form in a cell (Smyth's tables): the key names them together (Aοη:gen.s.mn = σοφοῦ).
_O = {('g', 's'): 'mn', ('d', 's'): 'mn', ('g', 'p'): 'mfn', ('d', 'p'): 'mn'}      # σοφός, ἄξιος, -μενος
_T = {('g', 's'): 'mn', ('d', 's'): 'mn', ('g', 'p'): 'mn', ('d', 'p'): 'mn'}       # βαθύς, πᾶς-type, participles
_TWO2 = {('g', 's'): 'mfn', ('d', 's'): 'mfn', ('g', 'p'): 'mfn', ('d', 'p'): 'mfn', ('a', 's'): 'mfn'}  # ἀδύνατος
_TWO3 = {('g', 's'): 'mfn', ('d', 's'): 'mfn', ('g', 'p'): 'mfn', ('d', 'p'): 'mfn'}  # εὐδαίμων, ἀληθής
SYNC = {}
for _k in ('Aοη', 'Aοα', 'Aους', 'Aπρ', 'Pμεν'):
    SYNC[_k] = _O
for _k in ('Aυς', 'Aας', 'Aεις') + tuple(PTC_SCHEMES):
    SYNC.setdefault(_k, _T)
SYNC['A2'] = _TWO2
SYNC['A2c'] = _TWO2
for _k in ('Aων', 'Aιων', 'Aης', 'A3', 'Aως'):
    SYNC[_k] = _TWO3
TWO_ENDINGS = {'A2', 'A2c', 'Aων', 'Aιων', 'Aης', 'A3', 'Aως'}


def genders(sc, case, num, g):
    """the gender label of a scheme cell (case, num: one-letter codes)"""
    lab = SYNC.get(sc, {}).get((case, num))
    if lab and g in lab:
        return lab
    if sc in TWO_ENDINGS and g in 'mf':
        return 'mf'
    return g


# lemma-specific words (pronouns, numerals …): the same patterns
_MF = {('g', 's'): 'mfn', ('d', 's'): 'mfn', ('g', 'p'): 'mfn', ('d', 'p'): 'mfn'}
LEMMA_SYNC = {}
for _l in ('αὐτός', 'οὗτος', 'τοιοῦτος', 'τοσοῦτος', 'τηλικοῦτος', 'ἄλλος', 'ὅς', 'ὅσπερ', 'ἑαυτόν', 'ἐμαυτόν',
           'σεαυτόν', 'σαυτόν', 'ἀλλήλων', 'ἐκεῖνος', 'ὅστις'):
    LEMMA_SYNC[_l] = _O
for _l in ('εἷς', 'οὐδείς', 'μηδείς', 'πᾶς', 'ἅπας', 'σύμπας'):
    LEMMA_SYNC[_l] = _T
MF_LEMMAS = {'τίς', 'τις', 'τρεῖς', 'τέτταρες', 'πλείων'}    # masc. = fem. throughout
for _l in MF_LEMMAS:
    LEMMA_SYNC[_l] = _MF


def lemma_genders(lemma, case, num, g):
    if lemma not in LEMMA_SYNC:
        return None
    lab = LEMMA_SYNC[lemma].get((case, num))
    if lab and g in lab:
        return lab
    if lemma in MF_LEMMAS and g in 'mf':
        return 'mf'
    return g
