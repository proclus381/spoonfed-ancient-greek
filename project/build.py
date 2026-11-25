# -*- coding: utf-8 -*-
"""Build the companion deck (original sentences, Athenaze I syllabus order).
    python3 build.py              → out/Athenaze_Companion.apkg  (+ out/preview.html, out/cards.tsv)
Cards come from sentences/chNN.txt in chapter order; check2.py works out what is new on each card."""
import glob, hashlib, html, json, os, re, shutil, sqlite3, subprocess, sys, tempfile, zipfile
import unicodedata as ud
import genanki
import check2 as K

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'out')
MEDIA = os.path.join(OUT, 'media')
os.makedirs(MEDIA, exist_ok=True)
FONTS = os.path.join(ROOT, 'fonts')

DECK_NAME = 'Spoonfed Ancient Greek'
DECK_ID = 1846207501
RATE = 135

# ------------------------------------------------------------------ cards
PATHS = sorted(glob.glob(os.path.join(ROOT, 'sentences', 'ch[0-9][0-9].txt')))
CARDS, KNOWN, USES = K.run(PATHS, quiet=True, show=False)
bad = [c for c in CARDS if c['problems']]
if bad:
    for c in bad[:20]:
        print(c['n'], c['gr'], c['problems'])
    sys.exit('fix the problems first')

# ------------------------------------------------------------------ labels
CASEA = {'nom': 'nom.', 'gen': 'gen.', 'dat': 'dat.', 'acc': 'acc.', 'voc': 'voc.'}
NUMA = {'s': 'sg.', 'p': 'pl.', 'd': 'dual'}
GENA = {'m': 'masc.', 'f': 'fem.', 'n': 'neut.'}
PERSON = {'1s': 'I …', '2s': 'you (sg.) …', '3s': 'he / she / it …', '1p': 'we …', '2p': 'you (pl.) …',
          '3p': 'they …'}
TENSE = {'p': 'present', 'i': 'imperfect', 'a': 'aorist', 'A': '2nd aorist', 'R': 'root aorist', 'P': 'aorist passive',
         'f': 'future', 'r': 'perfect', 'l': 'pluperfect', 't': 'future perfect'}
PARTNAME = {'': 'aorist', 'fut': 'future', 'aorp': 'aorist passive', 'pf': 'perfect', 'pfm': 'perfect middle/passive',
            'aor1': 'first aorist (transitive: “I made … stand, set up”)'}


def stem_parts(item):
    lemma, _, part = item[2:].partition('~')
    return lemma, PARTNAME[part]

NOTES = {  # what the back of the card says about a grammar item when it is new
    'Vpai:3s': 'ending <b>-ει</b>: he / she / it … (3rd person singular, present)',
    'εἰμί:pi3s': '<b>ἐστί(ν)</b> “is” — an enclitic: it leans on the word before it (ἄοκνός ἐστιν)',
    '2:nom.s': 'ending <b>-ος</b>: nominative singular — the subject',
    '2:acc.s': 'ending <b>-ον</b>: accusative singular — the direct object; also after πρός “to”, εἰς “into”',
    '2:gen.s': 'ending <b>-ου</b>: genitive singular — “of”; also after ἐκ “out of”',
    '2:dat.s': 'ending <b>-ῳ</b>: dative singular — after ἐν “in”, ὑπό “under”; also “to, for”',
    '2:acc.p': 'ending <b>-ους</b>: accusative plural — the object, more than one',
    '2n:nom.s': 'neuter ending <b>-ον</b>: nominative and accusative singular (τὸ δένδρον)',
    'Vpai:1s': 'ending <b>-ω</b> (-ῶ in verbs in -έω): I …',
    'Vpai:2s': 'ending <b>-εις</b> (-εῖς): you (one person) …',
    'Vpam:2s': 'ending <b>-ε</b>: an order to one person (σκάπτε “dig!”)',
    'Vpamε:2s': 'verbs in -έω: order to one person ends in <b>-ει</b> (πόνει “work!”)',
    'εἰμί:pi1s': '<b>εἰμί</b> “I am” (enclitic: δοῦλός εἰμι)',
    'εἰμί:pi2s': '<b>εἶ</b> “you are”',
    'εἰμί:pm2s': '<b>ἴσθι</b> “be!”',
    '2:voc.s': 'ending <b>-ε</b>: vocative — calling someone (ὦ δοῦλε)',
    '1m:acc.s': 'masculine nouns in -ης, -ας (δεσπότης, Ξανθίας): accusative <b>-ην, -αν</b>',
    '1m:dat.s': 'masculine nouns in -ης, -ας: dative <b>-ῃ, -ᾳ</b> (τῷ δεσπότῃ)',
    '1m:voc.s': 'masculine nouns in -ας, -ης: vocative <b>-α</b> (ὦ Ξανθία, ὦ δέσποτα)',
    '1f:dat.s': 'feminine dative singular <b>-ᾳ, -ῃ</b> (ἐν τῇ σκιᾷ)',
    '1f:acc.s': 'feminine accusative singular <b>-αν, -ην</b> (εἰς τὴν σκιάν)',
    'ἐγώ:acc.s': '<b>με / ἐμέ</b> “me”', 'ἐγώ:dat.s': '<b>μοι / ἐμοί</b> “to me, for me”',
    'ἐγώ:gen.s': '<b>μου / ἐμοῦ</b> “of me, my”', 'σύ:acc.s': '<b>σε</b> “you” (object)',
    'σύ:dat.s': '<b>σοι</b> “to you, for you”', 'σύ:gen.s': '<b>σου</b> “of you, your”',
    'τίς:nom.s.n': '<b>τί;</b> “what?” — also “why?”',
    # ch.13 imperfect
    'Viai:3s': 'imperfect: augment <b>ἐ-</b> + present stem + <b>-ε(ν)</b> (ἔ-παιζε “he was playing”)',
    'Viai:3p': 'imperfect <b>-ον</b>: they were …-ing (ἔπαιζον)',
    'Viai:1s': 'imperfect <b>-ον</b>: I was …-ing (ἔμενον) — the same form as “they …”',
    'Viai:2s': 'imperfect <b>-ες</b>: you (sg.) were …-ing (ἔπραττες)',
    'Viai:1p': 'imperfect <b>-ομεν</b>: we were …-ing (ἐμένομεν)',
    'Viai:2p': 'imperfect <b>-ετε</b>: you (pl.) were …-ing (ἐμένετε)',
    'Vimi:3s': 'imperfect middle <b>-ετο</b> (ἐπορεύετο “he was going”)',
    'Vimi:3p': 'imperfect middle <b>-οντο</b> (ἐβούλοντο “they wanted”)',
    'Vimi:1s': 'imperfect middle <b>-όμην</b> (ἐβουλόμην “I wanted”)',
    'Vimi:2s': 'imperfect middle <b>-ου</b> (ἐβούλου “you wanted”)',
    'Vimi:1p': 'imperfect middle <b>-όμεθα</b> (ἐπορευόμεθα)',
    'Vimi:2p': 'imperfect middle <b>-εσθε</b> (ἐπορεύεσθε)',
    'Viaiε:3s': 'verbs in -έω, imperfect: ε + ε → <b>ει</b> (ἐπόνει “he was working”)',
    'Viaiε:3p': 'verbs in -έω, imperfect: ε + ο → <b>ου</b> (ἐβοήθουν “they were helping”)',
    'Viaiε:1s': 'verbs in -έω, imperfect <b>-ουν</b>: I … (ἐζήτουν “I was looking for”)',
    'Viaiα:3s': 'verbs in -άω, imperfect: α + ε → <b>α</b> (ἐτίμα “he used to honour”)',
    'Viaiα:3p': 'verbs in -άω, imperfect: α + ο → <b>ω</b> (ἐβόων “they were shouting”)',
    'Viaiα:1s': 'verbs in -άω, imperfect <b>-ων</b>: I … (ἐσίγων)',
    'Viaiα:2s': 'verbs in -άω, imperfect <b>-ας</b>: you … (ἑώρας — ὁράω has the augment ἑω-)',
    'Vimiε:3s': 'middle of -έω verbs, imperfect <b>-εῖτο</b> (ἐφοβεῖτο)',
    'Vimiε:3p': 'middle of -έω verbs, imperfect <b>-οῦντο</b> (ἐφοβοῦντο)',
    'Vimiε:1s': 'middle of -έω verbs, imperfect <b>-ούμην</b> (ἐφοβούμην)',
    'Vimiε:2s': 'middle of -έω verbs, imperfect <b>-οῦ</b> (ἐφοβοῦ)',
    'Vimiα:3s': 'middle of -άω verbs, imperfect <b>-ᾶτο</b> (ἐθεᾶτο)',
    'Vimiα:3p': 'middle of -άω verbs, imperfect <b>-ῶντο</b> (ἐθεῶντο)',
    'εἶμι:ii3s': '<b>ᾔει</b> “he was going” — imperfect of εἶμι',
    'εἶμι:ii3p': '<b>ᾖσαν</b> “they were going” — imperfect of εἶμι (not ἦσαν “they were”)',
    # relative pronoun
    'ὅς:nom.s.m': '<b>ὅς, ἥ, ὅ</b> “who, which” — the relative pronoun; its forms look like the article (οὗ, ᾧ, ὅν …)',
    # stems in -εσ-
    '3es:gen.s': 'stems in -εσ- (τὸ τεῖχος, ἡ τριήρης, ἀληθής): genitive <b>-ους</b> (τοῦ τείχους)',
    '3es:dat.s': 'stems in -εσ-: dative <b>-ει</b> (τῷ τείχει, τῇ τριήρει)',
    '3esn:nom.p': 'stems in -εσ-: neuter plural <b>-η</b> (τὰ τείχη)',
    '3es:gen.p': 'stems in -εσ-: genitive plural <b>-ῶν</b> (τῶν τειχῶν; but τῶν τριήρων)',
    '3es:dat.p': 'stems in -εσ-: dative plural <b>-εσι(ν)</b> (τοῖς τείχεσιν)',
    '3es:acc.s': 'stems in -εσ-: masc./fem. accusative <b>-η</b> (τὴν τριήρη)',
    '3es:nom.p': 'stems in -εσ-: masc./fem. plural <b>-εις</b> (αἱ τριήρεις)',
    '3es:acc.p': 'stems in -εσ-: accusative plural <b>-εις</b> too (τὰς τριήρεις)',
    '3esn:nom.s': 'adjectives in -ής: neuter <b>-ές</b> (ἀληθές)',
    # ch.14 comparison
    'Dc': 'comparative <b>-τερος, -τέρα, -τερον</b>: “more …, …-er” (σοφώτερος “wiser”)',
    'Ds': 'superlative <b>-τατος, -τάτη, -τατον</b>: “most …, very …” (ἰσχυρότατος “strongest”)',
    # ch.15 root aorist, -όω verbs, νοῦς
    'VRai:3p': 'root aorist <b>-σαν</b>: ἔβησαν “they went”',
    'VRai:1s': 'root aorist <b>-ν</b>: ἔβην “I went”',
    'VRai:2s': 'root aorist <b>-ς</b>: ἔβης “you went”',
    'VRai:1p': 'root aorist <b>-μεν</b>: ἔβημεν “we went”',
    'VRai:2p': 'root aorist <b>-τε</b>: ἔβητε “you (pl.) went”',
    'VRainf': 'root aorist infinitive <b>-ναι</b> (βῆναι, γνῶναι, στῆναι)',
    'VRam:2s': 'root aorist command <b>-θι</b> (κατάβηθι, γνῶθι, ἀνάστηθι)',
    'VRam:2p': 'root aorist command to several people <b>-τε</b> (ἔκβητε)',
    'VRaptc.mn': 'root aorist participle: βάς, βάντος (γνούς, γνόντος; στάς, στάντος)',
    'VRaptc.f': 'root aorist participle, fem.: βᾶσα (γνοῦσα, στᾶσα)',
    'Vpaiο:3s': 'verbs in -όω: ο + ει → <b>οι</b> (δηλοῖ “he shows”)',
    'Vpaiο:3p': 'verbs in -όω: <b>-οῦσι(ν)</b> (δηλοῦσιν “they show”)',
    'Vpaiο:1s': 'verbs in -όω: <b>-ῶ</b> (δηλῶ “I show”)',
    'Vpaiο:2s': 'verbs in -όω: <b>-οῖς</b> (δηλοῖς “you show”)',
    'Vpaiο:1p': 'verbs in -όω: <b>-οῦμεν</b> (ἀξιοῦμεν)',
    'Vpaiο:2p': 'verbs in -όω: <b>-οῦτε</b> (ἀξιοῦτε)',
    'Viaiο:3s': 'verbs in -όω, imperfect <b>-ου</b> (ἠξίου)',
    'Viaiο:3p': 'verbs in -όω, imperfect <b>-ουν</b> (ἐπλήρουν)',
    'Vpainfο': 'verbs in -όω, infinitive <b>-οῦν</b> (ἐλευθεροῦν)',
    'Vpamο:2s': 'verbs in -όω, command <b>-ου</b> (δήλου)',
    'Vpaptcο.mn': 'verbs in -όω, participle <b>-ῶν, -οῦντος</b> (πληροῦντες)',
    'Vpminfο': 'verbs in -όω, middle infinitive <b>-οῦσθαι</b> (δουλοῦσθαι)',
    '2c:acc.s': 'contracted 2nd declension (νοῦς = νόος): accusative <b>νοῦν</b>',
    '2c:gen.s': 'contracted 2nd declension: genitive <b>νοῦ</b>',
    '2c:dat.s': 'contracted 2nd declension: dative <b>νῷ</b>',
    # ch.16 δύναμαι, κεῖμαι, ἐπίσταμαι: middle endings straight on the stem (no -ο-/-ε-)
    'Vpmiμ:1s': '<b>δύναμαι</b> “I can” — middle endings straight on the stem: -μαι, -σαι, -ται …',
    'Vpmiμ:2s': '<b>-σαι</b>: δύνασαι “you can” (not -ῃ)',
    'Vpmiμ:3s': '<b>-ται</b>: δύναται “he can”, κεῖται “it lies”',
    'Vpmiμ:1p': '<b>-μεθα</b>: δυνάμεθα “we can”',
    'Vpmiμ:2p': '<b>-σθε</b>: δύνασθε “you (pl.) can”',
    'Vpmiμ:3p': '<b>-νται</b>: δύνανται “they can”',
    'Vimiμ:3s': 'imperfect <b>-το</b>: ἐδύνατο (ἠδύνατο) “he could”, ἔκειτο “it lay”',
    'Vimiμ:3p': 'imperfect <b>-ντο</b>: ἐδύναντο “they could”',
    'Vimiμ:1s': 'imperfect <b>-μην</b>: ἐδυνάμην “I could”',
    'Vpmptcμ.mn': 'participle <b>-μενος</b>: δυνάμενος, κείμενος, ἐπιστάμενος',
    # ---- ch.18: δίδωμι, τίθημι
    'δίδωμι:pai3p': 'δίδωμι, present: δίδωμι, δίδως, δίδωσι(ν), δίδομεν, δίδοτε, <b>διδόασι(ν)</b>',
    'δίδωμι:aai3s': 'aorist of δίδωμι: <b>ἔδωκα, ἔδωκας, ἔδωκε(ν)</b>, but plural ἔδομεν, ἔδοτε, ἔδοσαν',
    'δίδωμι:aai3p': 'aorist plural of δίδωμι without κ: ἔδομεν, ἔδοτε, <b>ἔδοσαν</b>',
    'δίδωμι:aam2s': 'aorist command: <b>δός</b> “give!” (plural δότε)',
    'δίδωμι:aainf': 'aorist infinitive <b>δοῦναι</b>',
    'δίδωμι:aaptc.mn': 'aorist participle <b>δούς, δόντος</b> (fem. δοῦσα)',
    'δίδωμι:iai3s': 'imperfect of δίδωμι: ἐδίδουν, ἐδίδους, <b>ἐδίδου</b>, ἐδίδομεν, ἐδίδοτε, ἐδίδοσαν',
    'δίδωμι:ami3s': 'aorist middle <b>ἔδοτο</b> (ἀπέδοτο “he sold”)',
    'ἵστημι:pai3s': 'ἵστημι “I make stand, set up”, present: ἵστημι, ἵστης, <b>ἵστησι(ν)</b>, ἵσταμεν, ἵστατε, ἱστᾶσι(ν) — the middle ἵσταμαι “I stand” goes like δύναμαι',
    'ἵστημι:pai3p': 'ἵστημι, present: ἵστημι, ἵστης, ἵστησι(ν), ἵσταμεν, ἵστατε, <b>ἱστᾶσι(ν)</b>',
    'ἵστημι:pai1s': 'ἵστημι, present: <b>ἵστημι</b>, ἵστης, ἵστησι(ν), ἵσταμεν, ἵστατε, ἱστᾶσι(ν)',
    'ἵστημι:pai2s': 'ἵστημι, present: ἵστημι, <b>ἵστης</b>, ἵστησι(ν), ἵσταμεν, ἵστατε, ἱστᾶσι(ν)',
    'ἵστημι:pai1p': 'ἵστημι, present: ἵστημι, ἵστης, ἵστησι(ν), <b>ἵσταμεν</b>, ἵστατε, ἱστᾶσι(ν)',
    'ἵστημι:pai2p': 'ἵστημι, present: ἵστημι, ἵστης, ἵστησι(ν), ἵσταμεν, <b>ἵστατε</b>, ἱστᾶσι(ν)',
    'ἵστημι:painf': 'present infinitive <b>ἱστάναι</b>',
    'ἵστημι:pam2s': 'command <b>ἵστη</b> “make … stand, stop …!” (plural ἵστατε)',
    'ἵστημι:paptc.mn': 'present participle <b>ἱστάς, ἱστάντος</b> (fem. ἱστᾶσα)',
    'ἵστημι:iai3s': 'imperfect of ἵστημι: ἵστην, ἵστης, <b>ἵστη</b>, ἵσταμεν, ἵστατε, ἵστασαν',
    'ἵστημι:iai3p': 'imperfect of ἵστημι: ἵστην, ἵστης, ἵστη, ἵσταμεν, ἵστατε, <b>ἵστασαν</b>',
    'τίθημι:pai3p': 'τίθημι, present: τίθημι, τίθης, τίθησι(ν), τίθεμεν, τίθετε, <b>τιθέασι(ν)</b>',
    'τίθημι:aai3s': 'aorist of τίθημι: <b>ἔθηκα, ἔθηκας, ἔθηκε(ν)</b>, but plural ἔθεμεν, ἔθετε, ἔθεσαν',
    'τίθημι:aai3p': 'aorist plural of τίθημι without κ: ἔθεμεν, ἔθετε, <b>ἔθεσαν</b>',
    'τίθημι:aam2s': 'aorist command: <b>θές</b> “put!” (plural θέτε)',
    'τίθημι:aainf': 'aorist infinitive <b>θεῖναι</b>',
    'τίθημι:aaptc.mn': 'aorist participle <b>θείς, θέντος</b> (fem. θεῖσα)',
    'τίθημι:iai3s': 'imperfect of τίθημι: ἐτίθην, ἐτίθεις, <b>ἐτίθει</b>, ἐτίθεμεν, ἐτίθετε, ἐτίθεσαν',
    'τίθημι:ami3s': 'aorist middle <b>ἔθετο</b> (νόμον ἔθετο “passed a law”); so ἐθέμην, ἔθου, ἔθεντο; θέσθαι, θέμενος',
    # ---- book 2, ch.17: the future
    'Vfai:3s': 'future: stem + <b>σ</b> + the endings of the present (λύ-σ-ει “he will free”)',
    'Vfai:3p': 'future <b>-σουσι(ν)</b>: they will … (τιμήσουσιν)',
    'Vfai:1s': 'future <b>-σω</b>: I shall … (βοηθήσω)',
    'Vfai:2s': 'future <b>-σεις</b>: you will … (ποιήσεις)',
    'Vfai:1p': 'future <b>-σομεν</b>: we shall … (ποιήσομεν)',
    'Vfai:2p': 'future <b>-σετε</b>: you (pl.) will … (πιστεύσετε)',
    'Vfainf': 'future infinitive <b>-σειν</b> (μέλλω λύσειν “I am going to free”)',
    'Vfaptc.mn': 'future participle <b>-σων, -σοντος</b>: “going to …”, often of purpose (ἦλθε βοηθήσων)',
    'Vfaptc.f': 'future participle, fem. <b>-σουσα</b>',
    'Vfmi:3s': 'future middle <b>-σεται</b> (πορεύσεται “he will travel”)',
    'Vfmi:3p': 'future middle <b>-σονται</b> (θεάσονται)',
    'Vfmi:1s': 'future middle <b>-σομαι</b> (φοβήσομαι “I shall be afraid”)',
    'Vfmi:2s': 'future middle <b>-σῃ</b> (or -σει): you will … (πορεύσῃ)',
    'Vfmi:1p': 'future middle <b>-σόμεθα</b> (πορευσόμεθα)',
    'Vfmi:2p': 'future middle <b>-σεσθε</b> (ἐργάσεσθε)',
    'Vfminf': 'future middle infinitive <b>-σεσθαι</b> (πορεύσεσθαι)',
    'Vfmptc.mn': 'future middle participle <b>-σόμενος</b> (θεασόμενος “in order to watch”)',
    'Vfaiε:1p': 'contract future (stems in λ, μ, ν, ρ and -ίζω): endings of ποιέω — <b>-οῦμεν</b> (μενοῦμεν)',
    'Vfmiε:3s': 'contract future, middle: <b>-εῖται</b> (πεσεῖται “he will fall”)',
    'Vfmiε:3p': 'contract future, middle: <b>-οῦνται</b> (καμοῦνται, μαχοῦνται)',
    'Vfmiε:1p': 'contract future, middle: <b>-ούμεθα</b> (ἀποθανούμεθα)',
    'Vfmiε:1s': 'contract future, middle: <b>-οῦμαι</b> (μαχοῦμαι)',
    'εἰμί:fi3s': '<b>ἔσται</b> “he / it will be” — future of εἰμί: ἔσομαι, ἔσῃ, ἔσται, ἐσόμεθα, ἔσεσθε, ἔσονται',
    'εἶμι:pi1s': '<b>εἶμι</b> “I shall go” — serves as the future of ἔρχομαι: εἶμι, εἶ, εἶσι(ν), ἴμεν, ἴτε, ἴασι(ν)',
    'εἶμι:pptc.mn': '<b>ἰών, ἰόντος</b> “going” — the participle used with ἔρχομαι (so too ἰέναι, ἴθι)',
    'Vpminfμ': 'infinitive <b>-σθαι</b>: δύνασθαι, κεῖσθαι, ἐπίστασθαι',
    # ---- ch.21: the subjunctive
    'Vpas:1p': 'subjunctive: the endings of the present with a long vowel — <b>-ωμεν</b>: “let us …” (σπεύδωμεν). Active: -ω, -ῃς, -ῃ, -ωμεν, -ητε, -ωσι(ν)',
    'Vpas:1s': 'subjunctive <b>-ω</b> (-ῶ in -έω verbs): the same form as the indicative; here after ἵνα “so that I may …”',
    'Vpas:2s': 'subjunctive <b>-ῃς</b> (indicative -εις): ἵνα μανθάνῃς “so that you may learn”',
    'Vpas:3s': 'subjunctive <b>-ῃ</b> (indicative -ει): ἵνα μανθάνῃ “so that he may learn”',
    'Vpas:2p': 'subjunctive <b>-ητε</b> (indicative -ετε): ἵνα γιγνώσκητε “so that you may know”',
    'Vpas:3p': 'subjunctive <b>-ωσι(ν)</b> (indicative -ουσι): ἵνα ἔχωσιν “so that they may have”',
    'Vpms:1p': 'subjunctive middle <b>-ώμεθα</b>: “let us …” (μαχώμεθα). Middle: -ωμαι, -ῃ, -ηται, -ώμεθα, -ησθε, -ωνται',
    'Vpms:3s': 'subjunctive middle <b>-ηται</b> (indicative -εται): ἵνα μὴ ὀργίζηται “so that he won’t be angry”',
    'Vpms:3p': 'subjunctive middle <b>-ωνται</b> (indicative -ονται): ἵνα διαλέγωνται',
    'Vpms:1s': 'subjunctive middle <b>-ωμαι</b>', 'Vpms:2s': 'subjunctive middle <b>-ῃ</b>',
    'Vpms:2p': 'subjunctive middle <b>-ησθε</b>',
    'Vaas:1p': 'aorist subjunctive: aorist stem (no augment) + the same endings — <b>ἀκούσ-ωμεν</b> “let us hear”; so too λάβωμεν, ἔλθωμεν, φύγωμεν',
    'Vaas:1s': 'aorist subjunctive <b>-ω</b>: ποῖ φύγω; “where am I to flee?” (τί εἴπω; τί ποιήσω;)',
    'Vaas:2s': 'aorist subjunctive <b>-ῃς</b>: μὴ ποιήσῃς “don’t do …”',
    'Vaas:3s': 'aorist subjunctive <b>-ῃ</b>: ἵνα μηδεὶς εἰσέλθῃ “so that no one may come in”',
    'Vaas:2p': 'aorist subjunctive <b>-ητε</b>: μὴ θαυμάσητε “do not be surprised”',
    'Vaas:3p': 'aorist subjunctive <b>-ωσι(ν)</b>: ἵνα ἀκούσωσιν “so that they may hear”',
    'Vams:1p': 'aorist subjunctive middle <b>-ώμεθα</b>: δεξώμεθα “let us receive” (γενώμεθα, ἀφικώμεθα)',
    'Vams:1s': 'aorist subjunctive middle <b>-ωμαι</b>: τί γένωμαι; “what is to become of me?”',
    'Vams:2s': 'aorist subjunctive middle <b>-ῃ</b>: μὴ δέξῃ “don’t accept”',
    'Vams:3s': 'aorist subjunctive middle <b>-ηται</b>: ἵνα γένηται “so that he may become”',
    'Vams:2p': 'aorist subjunctive middle <b>-ησθε</b>: μὴ δέξησθε',
    'Vams:3p': 'aorist subjunctive middle <b>-ωνται</b>: ἵνα δέξωνται',
    'VRas:1p': 'root aorist subjunctive: <b>βῶ, βῇς, βῇ, βῶμεν, βῆτε, βῶσι(ν)</b> (ἀναβῶμεν “let us go up”; so στῶ; γνῶ, γνῷς, γνῷ)',
    'VRas:3s': 'root aorist subjunctive: γνῶ, γνῷς, <b>γνῷ</b>, γνῶμεν, γνῶτε, γνῶσι(ν) (βῶ, βῇς, βῇ …)',
    'Vpsα': 'verbs in -άω: the subjunctive looks just like the indicative (τιμῶ, τιμᾷς, τιμᾷ, <b>τιμῶμεν</b>, τιμᾶτε, τιμῶσι)',
    'Vpsο': 'verbs in -όω, subjunctive: δηλῶ, δηλοῖς, δηλοῖ, <b>δηλῶμεν</b>, δηλῶτε, δηλῶσι(ν)',
    'εἰμί:ps1p': 'subjunctive of εἰμί: ὦ, ᾖς, ᾖ, <b>ὦμεν</b>, ἦτε, ὦσι(ν) — just the subjunctive endings',
    'εἰμί:ps1s': 'subjunctive of εἰμί: <b>ὦ</b>, ᾖς, ᾖ, ὦμεν, ἦτε, ὦσι(ν)',
    'εἰμί:ps2s': 'subjunctive of εἰμί: ὦ, <b>ᾖς</b>, ᾖ, ὦμεν, ἦτε, ὦσι(ν)',
    'εἰμί:ps3s': 'subjunctive of εἰμί: ὦ, ᾖς, <b>ᾖ</b>, ὦμεν, ἦτε, ὦσι(ν)',
    'εἰμί:ps2p': 'subjunctive of εἰμί: ὦ, ᾖς, ᾖ, ὦμεν, <b>ἦτε</b>, ὦσι(ν)',
    'εἰμί:ps3p': 'subjunctive of εἰμί: ὦ, ᾖς, ᾖ, ὦμεν, ἦτε, <b>ὦσι(ν)</b>',
    'εἶμι:ps1p': 'subjunctive of εἶμι “go”: ἴω, ἴῃς, ἴῃ, <b>ἴωμεν</b> “let’s go”, ἴητε, ἴωσι(ν)',
    'εἶμι:ps3s': 'subjunctive of εἶμι “go”: ἴω, ἴῃς, <b>ἴῃ</b>, ἴωμεν, ἴητε, ἴωσι(ν)',
    'δίδωμι:aas': 'aorist subjunctive of δίδωμι: <b>δῶ, δῷς, δῷ, δῶμεν, δῶτε, δῶσι(ν)</b>',
    'δίδωμι:pas': 'present subjunctive of δίδωμι: <b>διδῶ, διδῷς, διδῷ, διδῶμεν, διδῶτε, διδῶσι(ν)</b>',
    'δίδωμι:ams': 'aorist subjunctive middle of δίδωμι: <b>δῶμαι, δῷ, δῶται, δώμεθα, δῶσθε, δῶνται</b> (ἀποδῶμαι “sell”)',
    'τίθημι:aas': 'aorist subjunctive of τίθημι: <b>θῶ, θῇς, θῇ, θῶμεν, θῆτε, θῶσι(ν)</b>',
    'τίθημι:pas': 'present subjunctive of τίθημι: <b>τιθῶ, τιθῇς, τιθῇ, τιθῶμεν, τιθῆτε, τιθῶσι(ν)</b>',
    'τίθημι:ams': 'aorist subjunctive middle of τίθημι: <b>θῶμαι, θῇ, θῆται, θώμεθα, θῆσθε, θῶνται</b>',
    'ἵστημι:pas': 'present subjunctive of ἵστημι: <b>ἱστῶ, ἱστῇς, ἱστῇ, ἱστῶμεν, ἱστῆτε, ἱστῶσι(ν)</b>',
    'ἵημι:aas': 'aorist subjunctive of ἵημι: <b>ὧ, ᾗς, ᾗ, ὧμεν, ἧτε, ὧσι(ν)</b> — in compounds ἀφῶ, ἀφῇς, ἀφῇ, ἀφῶμεν …',
    'ἵημι:pas': 'present subjunctive of ἵημι: <b>ἱῶ, ἱῇς, ἱῇ, ἱῶμεν, ἱῆτε, ἱῶσι(ν)</b>',
    # ---- ch.21: ἵημι
    'ἵημι:pai3s': 'ἵημι “I let go, throw, send”, present: ἵημι, ἵης, <b>ἵησι(ν)</b>, ἵεμεν, ἵετε, ἱᾶσι(ν) — like τίθημι',
    'ἵημι:pai3p': 'ἵημι, present: ἵημι, ἵης, ἵησι(ν), ἵεμεν, ἵετε, <b>ἱᾶσι(ν)</b>',
    'ἵημι:pai1s': 'ἵημι, present: <b>ἵημι</b>, ἵης, ἵησι(ν), ἵεμεν, ἵετε, ἱᾶσι(ν)',
    'ἵημι:pai2s': 'ἵημι, present: ἵημι, <b>ἵης</b>, ἵησι(ν), ἵεμεν, ἵετε, ἱᾶσι(ν)',
    'ἵημι:pai1p': 'ἵημι, present: ἵημι, ἵης, ἵησι(ν), <b>ἵεμεν</b>, ἵετε, ἱᾶσι(ν)',
    'ἵημι:pai2p': 'ἵημι, present: ἵημι, ἵης, ἵησι(ν), ἵεμεν, <b>ἵετε</b>, ἱᾶσι(ν)',
    'ἵημι:painf': 'present infinitive <b>ἱέναι</b> (rough breathing: not ἰέναι “to go”)',
    'ἵημι:pam2s': 'command <b>ἵει</b> “throw!, let go!” (plural ἵετε)',
    'ἵημι:paptc.mn': 'present participle <b>ἱείς, ἱέντος</b> (fem. ἱεῖσα)',
    'ἵημι:iai3s': 'imperfect of ἵημι: ἵην, ἵεις, <b>ἵει</b>, ἵεμεν, ἵετε, ἵεσαν',
    'ἵημι:iai3p': 'imperfect of ἵημι: ἵην, ἵεις, ἵει, ἵεμεν, ἵετε, <b>ἵεσαν</b>',
    'ἵημι:pmi3s': 'middle <b>ἵεμαι, ἵεσαι, ἵεται</b> …: “hurry, rush, be eager”',
    'ἵημι:pmptc.mn': 'middle participle <b>ἱέμενος</b> “rushing, eager”',
    'ἵημι:aai3s': 'aorist of ἵημι: <b>ἧκα, ἧκας, ἧκε(ν)</b>, but plural εἷμεν, εἷτε, εἷσαν (ἀφῆκε “he let go”)',
    'ἵημι:aai1s': 'aorist of ἵημι: <b>ἧκα</b>, ἧκας, ἧκε(ν), εἷμεν, εἷτε, εἷσαν (ἀφῆκα)',
    'ἵημι:aai1p': 'aorist plural of ἵημι without κ: <b>εἷμεν</b>, εἷτε, εἷσαν (ἀφεῖμεν)',
    'ἵημι:aai3p': 'aorist plural of ἵημι without κ: εἷμεν, εἷτε, <b>εἷσαν</b> (ἀφεῖσαν)',
    'ἵημι:aainf': 'aorist infinitive <b>εἷναι</b> (ἀφεῖναι “to let go”)',
    'ἵημι:aam2s': 'aorist command <b>ἕς</b> (ἄφες “let go!”; plural ἄφετε)',
    'ἵημι:aam2p': 'aorist command to several people <b>ἕτε</b> (ἄφετε “let go!”)',
    'ἵημι:aaptc.mn': 'aorist participle <b>εἵς, ἕντος</b> (ἀφείς, ἀφέντος; fem. ἀφεῖσα)',
    # ---- ch.22: δείκνυμι and the other verbs in -νυμι (ζεύγνυμι, ῥήγνυμι)
    'δείκνυμι:pai3s': 'verbs in -νυμι, present: δείκνυμι, δείκνυς, <b>δείκνυσι(ν)</b>, δείκνυμεν, δείκνυτε, δεικνύασι(ν) — the middle (δείκνυμαι, δείκνυται …) goes like δύναμαι; future δείξω, aorist ἔδειξα',
    'δείκνυμι:pai3p': 'verbs in -νυμι, present: δείκνυμι, δείκνυς, δείκνυσι(ν), δείκνυμεν, δείκνυτε, <b>δεικνύασι(ν)</b>',
    'δείκνυμι:pai1s': 'verbs in -νυμι, present: <b>δείκνυμι</b>, δείκνυς, δείκνυσι(ν), δείκνυμεν, δείκνυτε, δεικνύασι(ν)',
    'δείκνυμι:pai2s': 'verbs in -νυμι, present: δείκνυμι, <b>δείκνυς</b>, δείκνυσι(ν), δείκνυμεν, δείκνυτε, δεικνύασι(ν)',
    'δείκνυμι:pai1p': 'verbs in -νυμι, present: δείκνυμι, δείκνυς, δείκνυσι(ν), <b>δείκνυμεν</b>, δείκνυτε, δεικνύασι(ν)',
    'δείκνυμι:pai2p': 'verbs in -νυμι, present: δείκνυμι, δείκνυς, δείκνυσι(ν), δείκνυμεν, <b>δείκνυτε</b>, δεικνύασι(ν)',
    'δείκνυμι:painf': 'verbs in -νυμι: present infinitive <b>-νύναι</b> (δεικνύναι)',
    'δείκνυμι:pam2s': 'verbs in -νυμι: command <b>δείκνυ</b> “show!” (plural δείκνυτε)',
    'δείκνυμι:paptc.mn': 'verbs in -νυμι: present participle <b>δεικνύς, δεικνύντος</b> (fem. δεικνῦσα)',
    'δείκνυμι:iai3s': 'verbs in -νυμι, imperfect: ἐδείκνυν, ἐδείκνυς, <b>ἐδείκνυ</b>, ἐδείκνυμεν, ἐδείκνυτε, ἐδείκνυσαν',
    'δείκνυμι:iai3p': 'verbs in -νυμι, imperfect: ἐδείκνυν, ἐδείκνυς, ἐδείκνυ, ἐδείκνυμεν, ἐδείκνυτε, <b>ἐδείκνυσαν</b>',
    # ---- ch.23: φημί
    'φημί:pi1s': 'φημί “I say”, present: <b>φημί</b>, φῄς, φησί(ν), φαμέν, φατέ, φασί(ν) — enclitic except φῄς; with the infinitive',
    'φημί:pi2s': 'φημί, present: φημί, <b>φῄς</b>, φησί(ν), φαμέν, φατέ, φασί(ν)',
    'φημί:pi1p': 'φημί, present: φημί, φῄς, φησί(ν), <b>φαμέν</b>, φατέ, φασί(ν)',
    'φημί:pi2p': 'φημί, present: φημί, φῄς, φησί(ν), φαμέν, <b>φατέ</b>, φασί(ν)',
    'φημί:pi3p': 'φημί, present: φημί, φῄς, φησί(ν), φαμέν, φατέ, <b>φασί(ν)</b>',
    'φημί:ii1s': 'imperfect of φημί: <b>ἔφην</b>, ἔφησθα, ἔφη, ἔφαμεν, ἔφατε, ἔφασαν',
    'φημί:ii2s': 'imperfect of φημί: ἔφην, <b>ἔφησθα</b>, ἔφη, ἔφαμεν, ἔφατε, ἔφασαν',
    'φημί:ii1p': 'imperfect of φημί: ἔφην, ἔφησθα, ἔφη, <b>ἔφαμεν</b>, ἔφατε, ἔφασαν',
    'φημί:ii3p': 'imperfect of φημί: ἔφην, ἔφησθα, ἔφη, ἔφαμεν, ἔφατε, <b>ἔφασαν</b>',
    'φημί:pinf': 'infinitive of φημί: <b>φάναι</b>',
    # ---- ch.24: aorist and future passive
    'VPpi:3s': 'aorist passive: (augment) + stem + <b>-θη</b> + endings like ἔβην: ἐποιήθην, ἐποιήθης, <b>ἐποιήθη</b>, ἐποιήθημεν, ἐποιήθητε, ἐποιήθησαν — “was (done)”; agent ὑπό + gen.',
    'VPpi:3p': 'aorist passive, 3rd plural <b>-θησαν</b>: ἐνικήθησαν “they were defeated”',
    'VPpi:1p': 'aorist passive, 1st plural <b>-θημεν</b>: ἐνικήθημεν “we were defeated”',
    'VPpi:2s': 'aorist passive, 2nd singular <b>-θης</b>: ἐτιμήθης “you were honoured”',
    'VPpi:1s': 'aorist passive, 1st singular <b>-θην</b>: ἐφιλήθην “I was loved”',
    'VPpi:2p': 'aorist passive, 2nd plural <b>-θητε</b>: ἐτιμήθητε “you were honoured”',
    'VPpinf': 'aorist passive infinitive <b>-θῆναι</b>: ληφθῆναι “to be caught”',
    'VPpptc.mn': 'aorist passive participle <b>-θείς, -θέντος</b>: ληφθείς “having been caught” (neuter -θέν)',
    'VPpptc.f': 'aorist passive participle, feminine <b>-θεῖσα, -θείσης</b>: κληθεῖσα “having been called”',
    'VPpm:2s': 'aorist passive command <b>-θητι</b> (πείσθητι “be persuaded, obey”); 2nd aorist -ηθι (γράφηθι); plural -θητε',
    'VPs:3s': 'aorist passive subjunctive <b>-θῶ, -θῇς, -θῇ</b>, -θῶμεν, -θῆτε, -θῶσι(ν): μὴ ληφθῇ “that he may be caught”',
    'VPs:1p': 'aorist passive subjunctive <b>-θῶμεν</b>: ἵνα μὴ ὀφθῶμεν “so that we are not seen”',
    'Vfpi:1p': 'future passive: aorist passive stem + <b>-θήσομαι</b> (middle endings): ληφθησόμεθα “we shall be caught”',
    'Vfpi:3s': 'future passive <b>-θήσεται</b>: ληφθήσεται “he will be caught”',
    'Vfpi:3p': 'future passive <b>-θήσονται</b>: νικηθήσονται “they will be defeated”',
    'Vfpi:1s': 'future passive <b>-θήσομαι</b>: τιμηθήσομαι “I shall be honoured”',
    'Vfpi:2s': 'future passive <b>-θήσῃ / -θήσει</b>: ληφθήσῃ “you will be caught”',
    'Vfpinf': 'future passive infinitive <b>-θήσεσθαι</b>: σωθήσεσθαι “to be going to be saved”',
    'Vfpptc.mn': 'future passive participle <b>-θησόμενος</b>: ὡς τιμηθησόμενος “expecting to be honoured”',
    # ---- ch.25: the optative
    'Voa:3s': 'optative (recognisable by its -οι-): λύοιμι, λύοις, <b>λύοι</b>, λύοιμεν, λύοιτε, λύοιεν — on its own it expresses a wish: “may he …!” (negative μή); the 2nd aorist has the same endings (λάβοι)',
    'Voa:1s': 'optative, 1st singular <b>-οιμι</b>: ἀποθάνοιμι “may I die”', 'Voa:2s': 'optative, 2nd singular <b>-οις</b>: χαίροις “farewell (may you rejoice)”',
    'Voa:1p': 'optative, 1st plural <b>-οιμεν</b>: μὴ ἔχοιμεν “may we not have”', 'Voa:2p': 'optative, 2nd plural <b>-οιτε</b>: μένοιτε “may you stay”',
    'Voa:3p': 'optative, 3rd plural <b>-οιεν</b>: σῴζοιεν “may they save”',
    'Vom:3s': 'optative middle: -οίμην, -οιο, <b>-οιτο</b>, -οίμεθα, -οισθε, -οιντο (μὴ γένοιτο “may it not happen!”)',
    'Vom:3p': 'optative middle, 3rd plural <b>-οιντο</b>: μὴ ὀργίζοιντο', 'Vom:1s': 'optative middle, 1st singular <b>-οίμην</b>: γενοίμην “may I become”',
    'Voη:2s': 'optative of contract verbs (and root aorists): φιλοίην, <b>φιλοίης</b>, φιλοίη, φιλοῖμεν, φιλοῖτε, φιλοῖεν; τιμῴην …; βαίην, γνοίην',
    'Voη:3s': 'optative in -ίη (contract verbs, root aorists): φιλοίην, φιλοίης, <b>φιλοίη</b> …; βαίη, γνοίη',
    'Voη:3p': 'optative in -ῖεν: φιλοῖεν, <b>νικῷεν</b>, βαῖεν', 'Voη:1s': 'optative in -ίην: <b>εὐτυχοίην</b>, τιμῴην, βαίην',
    'Vo1a:3s': 'aorist optative (1st aorist): λύσαιμι, λύσαις (λύσειας), <b>λύσαι / λύσειε(ν)</b>, λύσαιμεν, λύσαιτε, λύσαιεν (λύσειαν)',
    'Vo1a:1s': 'aorist optative, 1st singular <b>-σαιμι</b>: ἀκούσαιμι', 'Vo1a:3p': 'aorist optative, 3rd plural <b>-σαιεν / -σειαν</b>: σώσειαν',
    'Vo1m:3s': 'aorist optative middle: -σαίμην, -σαιο, <b>-σαιτο</b>, -σαίμεθα, -σαισθε, -σαιντο (παύσαιτο)',
    'VPo:3s': 'aorist passive optative: λυθείην, λυθείης, <b>λυθείη</b>, λυθεῖμεν, λυθεῖτε, λυθεῖεν',
    'Vfo': 'future optative (λύσοι, ἔσοιτο, δέξοιτο): only in indirect speech after a past tense, for a future of the direct speech',
    'Voμ': 'optative of δύναμαι, ἐπίσταμαι: δυναίμην, δύναιο, <b>δύναιτο</b> …',
    'εἰμί:po3s': 'optative of εἰμί: εἴην, εἴης, <b>εἴη</b>, εἶμεν, εἶτε, εἶεν', 'εἰμί:po1s': 'optative of εἰμί: <b>εἴην</b>, εἴης, εἴη …',
    'εἰμί:po3p': 'optative of εἰμί: … εἶμεν, εἶτε, <b>εἶεν</b> (also εἴησαν)',
    'εἶμι:po3s': 'optative of εἶμι: ἴοιμι (ἰοίην), ἴοις, <b>ἴοι</b>, ἴοιμεν, ἴοιτε, ἴοιεν',
    'φημί:po3s': 'optative of φημί: φαίην, φαίης, <b>φαίη</b>, φαῖμεν, φαῖτε, φαῖεν',
    'δίδωμι:aao': 'aorist optative of δίδωμι: <b>δοίην, δοίης, δοίη, δοῖμεν, δοῖτε, δοῖεν</b> (τίθημι: θείην; present διδοίην, τιθείην)',
    # ---- ch.26
    'ἔξεστι:pptc.mn': 'participle of ἔξεστι: <b>ἐξόν</b> “it being allowed” (accusative absolute)',
    'δεῖ:pptc.mn': 'participle of δεῖ: <b>δέον</b> “it being necessary” (accusative absolute)',
    # ---- ch.27: perfect middle-passive
    'Vrmi:3s': 'perfect middle-passive: reduplication + stem + endings without a thematic vowel: λέλυμαι, λέλυσαι, <b>λέλυται</b>, λελύμεθα, λέλυσθε, λέλυνται — “has been (done)”, a state now',
    'Vrmi:1s': 'perfect middle-passive, 1st singular <b>-μαι</b>: λέλυμαι “I have been freed”', 'Vrmi:2s': 'perfect middle-passive, 2nd singular <b>-σαι</b>: λέλυσαι',
    'Vrmi:3p': 'perfect middle-passive, 3rd plural <b>-νται</b>: λέλυνται', 'Vrmi:1p': 'perfect middle-passive, 1st plural <b>-μεθα</b>: νενικήμεθα',
    'Vrmi:2p': 'perfect middle-passive, 2nd plural <b>-σθε</b>: τετίμησθε',
    'Vrmiκ:3s': 'perfect middle-passive of consonant stems: the endings change the consonant — γέγραμμαι, γέγραψαι, <b>γέγραπται</b>, γεγράμμεθα, γέγραφθε; τέταγμαι, τέτακται; ἤγγελμαι, ἤγγελται',
    'Vrminf': 'perfect middle-passive infinitive <b>-σθαι</b>, accent on the penult: πεποιῆσθαι, λελύσθαι',
    'Vrminfκ': 'perfect middle-passive infinitive of consonant stems: <b>γεγράφθαι</b>, τετάχθαι, ἠγγέλθαι',
    'Vrmptc': 'perfect middle-passive participle <b>-μένος</b>, accent on the penult: λελυμένος, γεγραμμένος',
    'Vlmi:3s': 'pluperfect middle-passive: augment + perfect stem + secondary endings: ἐλελύμην, ἐλέλυσο, <b>ἐλέλυτο</b>, ἐλελύμεθα, ἐλέλυσθε, ἐλέλυντο — “had been (done)”',
    'Vlmi:3p': 'pluperfect middle-passive, 3rd plural <b>-ντο</b>: ἐλέλυντο', 'Vlmiκ:3s': 'pluperfect middle-passive of consonant stems: ἐγέγραπτο “had been written”',
    'Vt': 'future perfect: perfect stem + -σομαι: λελύσομαι “I shall have been freed” (rare)',
    'Vrai:3s': 'perfect active: reduplication + stem + <b>-κα</b>: λέλυκα, λέλυκας, <b>λέλυκε(ν)</b>, λελύκαμεν, λελύκατε, λελύκασι(ν) — “has (done)”, the result still holds',
    'Vrai:1s': 'perfect active, 1st singular <b>-κα</b>: πεποίηκα “I have done”', 'Vrai:2s': 'perfect active, 2nd singular <b>-κας</b>: πεποίηκας',
    'Vrai:3p': 'perfect active, 3rd plural <b>-κασι(ν)</b>: νενικήκασι(ν)', 'Vrai:1p': 'perfect active, 1st plural <b>-καμεν</b>: νενικήκαμεν',
    'Vrai:2p': 'perfect active, 2nd plural <b>-κατε</b>: πεποιήκατε',
    'Vrainf': 'perfect active infinitive <b>-κέναι</b>, accent on the penult: λελυκέναι, πεποιηκέναι',
    'Vraptc.mn': 'perfect active participle <b>-κώς, -κυῖα, -κός</b> (gen. -κότος): νενικηκώς “having won”',
    'Vraptc.f': 'perfect active participle, feminine <b>-κυῖα</b>: πεπαιδευκυῖα',
    'Vlai:3s': 'pluperfect active: augment + perfect stem + <b>-η, -ης, -ει(ν)</b>, -εμεν, -ετε, -εσαν: <b>ἐπεποιήκει</b> “had done”',
    'Vlai:3p': 'pluperfect active, 3rd plural <b>-εσαν</b>: ἐνενικήκεσαν', 'Vlai:1s': 'pluperfect active, 1st singular <b>-η</b>: ἐπεποιήκη',
    'οἶδα:ri1s': '<b>οἶδα</b> “I know” — a perfect with present meaning (“I have seen” → “I know”): οἶδα, οἶσθα, οἶδε(ν), ἴσμεν, ἴστε, ἴσασι(ν)',
    'οἶδα:ri2s': 'οἶδα, 2nd singular <b>οἶσθα</b> “you know”', 'οἶδα:ri3s': 'οἶδα, 3rd singular <b>οἶδε(ν)</b> “he/she knows”',
    'οἶδα:ri1p': 'οἶδα, 1st plural <b>ἴσμεν</b> “we know” (stem ἰδ-/ἰσ-)', 'οἶδα:ri2p': 'οἶδα, 2nd plural <b>ἴστε</b> “you know” (also the command “know!”)',
    'οἶδα:ri3p': 'οἶδα, 3rd plural <b>ἴσασι(ν)</b> “they know”',
    'οἶδα:li3s': 'pluperfect of οἶδα = “knew”: ᾔδη (ᾔδειν), ᾔδησθα (ᾔδεις), <b>ᾔδει(ν)</b>, ᾖσμεν, ᾖστε, ᾖσαν (ᾔδεσαν)',
    'οἶδα:li1s': 'οἶδα, “I knew”: <b>ᾔδη</b> (ᾔδειν)', 'οἶδα:li3p': 'οἶδα, “they knew”: <b>ᾔδεσαν</b> or ᾖσαν',
    'οἶδα:rinf': 'infinitive of οἶδα: <b>εἰδέναι</b> “to know”',
    'οἶδα:rptc.mn': 'participle of οἶδα: <b>εἰδώς</b>, εἰδυῖα, εἰδός (gen. εἰδότος) “knowing”',
    'οἶδα:rptc.f': 'participle of οἶδα, feminine: <b>εἰδυῖα</b>, -ίας',
    'οἶδα:rm2s': 'command of οἶδα: <b>ἴσθι</b> “know! be sure!”, ἴστε; εὖ ἴσθι ὅτι … “be well assured that …” (ἴσθι is also “be!”)',
    'οἶδα:rs3s': 'subjunctive of οἶδα: εἰδῶ, εἰδῇς, <b>εἰδῇ</b>, εἰδῶμεν, εἰδῆτε, εἰδῶσι(ν)',
    'οἶδα:ro3s': 'optative of οἶδα: εἰδείην, εἰδείης, <b>εἰδείη</b>, εἰδεῖμεν, εἰδεῖτε, εἰδεῖεν',
    'ἕ:dat.s': 'the indirect reflexive pronoun of the 3rd person: (gen.) οὗ, (dat.) <b>οἷ</b>, (acc.) ἕ “him, her” — in a dependent clause or infinitive, it refers back to the subject of the main verb',
    'σφεῖς:dat.p': 'indirect reflexive, plural: σφεῖς, σφῶν, <b>σφίσι(ν)</b>, σφᾶς “they, them” (referring back to the main subject)',
    'Vpam:3s': '3rd-person command, singular <b>-έτω</b>: λεγέτω “let him speak”, φερέτω; ἔστω “let it be”',
    'Vpam:3p': '3rd-person command, plural <b>-όντων</b>: μενόντων “let them stay” (same form as the gen. pl. of the participle)',
    'Vpamα:3p': '3rd-person command of an α-contract verb, plural <b>-ώντων</b>: σιγώντων “let them be quiet” (σιγάτω “let him be quiet”)',
    'Vpmm:3s': '3rd-person command, middle <b>-έσθω</b> (pl. -έσθων): πειθέσθω “let him obey”',
    'Vaam:3s': '3rd-person command, aorist <b>-άτω</b> (pl. -άντων; middle -άσθω, -άσθων): καλεσάτω “let him call”',
    'VAam:3s': '3rd-person command, 2nd aorist <b>-έτω</b>: εἰσελθέτω “let him come in”, λαβέτω',
    'Ndual': 'the dual, for two people or things (pairs especially): 2nd decl. <b>-ω</b> / -οιν (τὼ ἀδελφώ, τοῖν ἀδελφοῖν), 1st decl. -α / -αιν, 3rd decl. <b>-ε</b> / -οιν (τὼ χεῖρε, τοῖν χεροῖν); article τώ, τοῖν for all genders',
    'Vdual': 'dual verb forms: 2nd and 3rd person <b>-τον</b> (παίζετον “the two play”, ἐστόν “the two are”); past 3rd person -την (ἤστην); a dual subject may also take a plural verb',
    'σφεῖς:acc.p': 'indirect reflexive, plural accusative <b>σφᾶς</b> “them”', 'σφεῖς:gen.p': 'indirect reflexive, plural genitive <b>σφῶν</b> “of them”',
}


def key_label(k):
    """short label of a grammar key, used as cloze hint / in the notes"""
    if k in ('Dc', 'Ds'):
        return {'Dc': 'comparative', 'Ds': 'superlative'}[k]
    mo = re.match(r'V(P?)o(1?)([amημ]?)(?::(\w+))?$', k) or (k == 'Vfo' and re.match(r'V(f)o()()()$', k))
    if mo:
        p, one, v, pn = mo.groups()
        vo = {'m': ' (middle)', 'μ': ' (middle)'}.get(v, ' (passive)' if p == 'P' else '')
        tn = ' — future' if p == 'f' else (' — aorist' if one or p == 'P' else '')
        return '%s%s%s — optative' % (PERSON.get(pn, pn) if pn else '', vo, tn)
    if k.startswith('X:'):
        return K.EN.get(k, k[2:]).split(':')[0].split('(')[0].strip()
    if k == 'Vt':
        return 'future perfect'
    m0 = re.match(r'VPs:(\w+)$', k)
    if m0:
        return '%s — aorist passive subjunctive' % PERSON.get(m0.group(1), m0.group(1))
    if re.match(r'Vps[αο]$', k):
        return 'subjunctive (contract verb)'
    if k in ('Ndual', 'Vdual'):
        return 'dual' + (' (verb)' if k == 'Vdual' else '')
    if k.startswith('V'):
        m = re.match(r'V([a-zA-Z])([amp])(inf|ptc|[isom])([εαομ]?)(?::(\w+)|\.(\w+))?$', k)
        if m:
            t, v, md, c, pn, g = m.groups()
            vo = {'a': '', 'm': ', middle', 'p': ', passive'}[v]
            tn = TENSE.get(t, t)
            if md == 'inf':
                return '%s infinitive%s' % (tn, vo)
            if md == 'ptc':
                return '%s participle%s%s' % (tn, vo, ', fem.' if g == 'f' else '')
            if md == 'm':
                if pn and pn.startswith('3'):
                    return '3rd-person command (“let him / let them …”)%s%s' % (vo, '' if t == 'p' else ', ' + tn)
                return 'command to %s%s%s' % ('one person' if pn == '2s' else 'several people', vo,
                                             '' if t == 'p' else ', ' + tn)
            sj = ' — subjunctive' if md == 's' else ''
            return '%s%s%s%s' % (PERSON.get(pn, pn), ' (' + vo[2:] + ')' if vo else '', '' if t == 'p' else ' — ' + tn, sj)
    m = re.match(r'(.+?):(nom|gen|dat|acc|voc)\.([spd])(?:\.([mfn]))?(?::([cs]))?$', k)
    if m:
        lemma, case, num, g, deg = m.groups()
        case = 'nom./acc.' if (g == 'n' or lemma in ('2n', '3n', '3esn')) and case == 'nom' else CASEA[case]
        s = '%s %s' % (case, NUMA[num])
        if g and lemma not in ('ἐγώ', 'σύ'):
            s += ' ' + GENA[g]
        if deg:
            s += {'c': ', comparative', 's': ', superlative'}[deg]
        return s
    m = re.match(r'(.+?):([a-zA-Z])([amp])(inf|ptc|[isom])\.?(\w*)$', k)
    if m and m.group(1) in K.MI_VERBS:
        lemma, t, v, md, rest = m.groups()
        vo = {'a': '', 'm': ', middle', 'p': ', passive'}[v]
        tn = '' if t == 'p' else ' — ' + TENSE.get(t, t)
        if md == 'inf':
            return 'infinitive' + vo + tn
        if md == 'ptc':
            return 'participle' + vo + (', fem.' if rest == 'f' else '') + tn
        return ('command: ' if md == 'm' else '') + PERSON.get(rest[:2], rest) + (' (' + vo[2:] + ')' if vo else '') + tn
    m = re.match(r'(.+?):([a-zA-Z])(inf|ptc|[isom])(\w*)', k)
    if m:
        lemma, t, md, rest = m.groups()
        if md == 'inf':
            return 'infinitive' + ('' if t == 'p' else ' — ' + TENSE.get(t, t))
        tn = '' if t == 'p' else ' — ' + TENSE.get(t, t)
        if md == 'ptc':
            return 'participle' + tn
        return ('command: ' if md == 'm' else '') + PERSON.get(rest[:2], rest) + tn
    return k


def gloss(item, form=''):
    if item in K.XHINT:                  # sense item: a short hint that does not give the word away
        return K.XHINT[item]
    if item.startswith('L:'):
        return K.EN.get(item, '')
    if item.startswith(('C:', 'X:')):
        return K.EN.get(item, '')
    return key_label(item)


def new_line(item, form):
    """one line for the back of the card about the new item"""
    if item.startswith('L:'):
        en = K.EN.get(item, '')
        return '<span class="gr">%s</span> — %s' % (item[2:], html.escape(en)) if en and en != '(name)' else \
            '<span class="gr">%s</span>' % item[2:]
    if item.startswith('C:'):
        return '<span class="gr">%s</span> — %s' % (item[2:], html.escape(K.EN.get(item, '')))
    if item.startswith('X:'):
        return html.escape(K.EN.get(item, ''))
    if item.startswith('S:'):
        lemma, part = stem_parts(item)
        return '<span class="gr">%s</span> — %s of <span class="gr">%s</span> (%s)' % (
            form, part, lemma, html.escape(K.EN.get('L:' + lemma, '')))
    if item in NOTES:
        return NOTES[item]
    lemma = item.split(':', 1)[0]
    if lemma not in ('V', '1f', '1m', '2', '2n', '2c', '3', '3n', '3es', '3esn') and not item.startswith('V'):
        en = K.EN.get('L:' + lemma, '')
        return '<span class="gr">%s</span> (%s) — %s' % (form, lemma, key_label(item))
    return '<span class="gr">%s</span> — %s' % (form, key_label(item))


# ------------------------------------------------------------------ endings to blank
ENDINGS = {
    '2': {'nom.s': ['οσ'], 'gen.s': ['ου'], 'dat.s': ['ω'], 'acc.s': ['ον'], 'voc.s': ['ε'], 'nom.p': ['οι'],
          'gen.p': ['ων'], 'dat.p': ['οισ'], 'acc.p': ['ουσ'], 'voc.p': ['οι']},
    '2n': {'nom.s': ['ον'], 'nom.p': ['α']},
    '1f': {'nom.s': ['η', 'α'], 'gen.s': ['ησ', 'ασ'], 'dat.s': ['η', 'α'], 'acc.s': ['ην', 'αν'],
           'voc.s': ['η', 'α'], 'nom.p': ['αι'], 'gen.p': ['ων'], 'dat.p': ['αισ'], 'acc.p': ['ασ'], 'voc.p': ['αι']},
    '1m': {'gen.s': ['ου'], 'dat.s': ['η', 'α'], 'acc.s': ['ην', 'αν'], 'voc.s': ['α', 'η'], 'nom.p': ['αι'],
           'gen.p': ['ων'], 'dat.p': ['αισ'], 'acc.p': ['ασ'], 'voc.p': ['αι']},
}
VEND = {'1s': ['ω'], '2s': ['εισ'], '3s': ['ει'], '1p': ['ουμεν', 'ωμεν', 'ομεν'], '2p': ['ειτε', 'ατε', 'ετε'],
        '3p': ['ουσιν', 'ωσιν', 'ουσι', 'ωσι']}
VEND_A = {'1s': ['ω'], '2s': ['ασ'], '3s': ['α'], '1p': ['ωμεν'], '2p': ['ατε'], '3p': ['ωσιν', 'ωσι']}
VEND_O = {'1s': ['ω'], '2s': ['οισ'], '3s': ['οι'], '1p': ['ουμεν'], '2p': ['ουτε'], '3p': ['ουσιν', 'ουσι']}
VIMP = {'2s': ['ει', 'ε', 'α', 'ου'], '2p': ['ειτε', 'ατε', 'ετε']}


def ending_of(item, tok):
    """number of letters at the end of the token that make the ending of a grammar item (0 = whole word)"""
    b = K.bare(tok)
    mu = re.match(r'Vpm(?:i|inf|ptc)μ(?::(\w\w))?', item)
    if mu:                                     # δύναμαι, κεῖμαι: endings straight on the stem
        if 'inf' in item:
            e = ['σθαι']
        elif 'ptc' in item:
            k = b.rfind('μεν')
            return len(b) - k if k > 0 else 0
        else:
            e = {'1s': ['μαι'], '2s': ['σαι'], '3s': ['ται'], '1p': ['μεθα'], '2p': ['σθε'], '3p': ['νται']}.get(mu.group(1), [])
        for x in e:
            if b.endswith(x) and len(x) < len(b):
                return len(x)
        return 0
    cands = []
    m = re.match(r'(1f|1m|2n|2):(\w+\.\w)', item)
    if m:
        cands = ENDINGS.get(m.group(1), {}).get(m.group(2), [])
    m = re.match(r'Vp[am]([im])([εαο]?):(\w\w)$', item)
    if m and m.group(1) == 'i':
        cands = {'α': VEND_A, 'ο': VEND_O}.get(m.group(2), VEND).get(m.group(3), [])
    elif m and m.group(1) == 'm':
        cands = VIMP.get(m.group(3), [])
    if re.match(r'Vpa?inf', item):
        cands = ['ειν', 'αν', 'ουν', 'εσθαι', 'ασθαι', 'ουσθαι']
    me = re.match(r'(3esn?):(\w+\.\w)$', item)
    if me:
        cands = {'gen.s': ['ουσ'], 'dat.s': ['ει'], 'acc.s': ['η'], 'nom.p': ['εισ', 'η'], 'acc.p': ['εισ'],
                 'gen.p': ['ων'], 'dat.p': ['εσιν', 'εσι'], 'nom.s': ['εσ']}.get(me.group(2), [])
    m3 = re.match(r'(3n?):(\w+\.\w)$', item)
    if m3:
        cands = {'gen.s': ['οσ', 'ουσ', 'ωσ'], 'dat.s': ['ι', 'ει'], 'acc.s': ['α', 'ν'], 'nom.p': ['εσ', 'α', 'η', 'εισ'],
                 'gen.p': ['ων'], 'dat.p': ['σιν', 'σι', 'ξιν', 'ξι', 'ψιν', 'ψι'], 'acc.p': ['ασ', 'εισ']}.get(m3.group(2), [])
    mm = re.match(r'Vpm([imn])\w*?([εαο]?)(?::(\w\w)|inf)?', item)
    if mm and item.startswith('Vpm'):
        if 'inf' in item:
            cands = ['εσθαι', 'εισθαι', 'ασθαι', 'ουσθαι']
        elif 'ptc' in item:
            cands = ['ομεν', 'ουμεν', 'ωμεν']
            for e in ('ομεν', 'ουμεν', 'ωμεν'):
                k = b.rfind(e)
                if k > 0:
                    return len(b) - k
        else:
            pn = item.split(':')[-1]
            cands = {'1s': ['ομαι', 'ουμαι', 'ωμαι'], '2s': ['η', 'ει', 'α', 'ου', 'ω'],
                     '3s': ['εται', 'ειται', 'αται', 'ουται'], '1p': ['ομεθα', 'ουμεθα', 'ωμεθα'],
                     '2p': ['εσθε', 'εισθε', 'ασθε', 'ουσθε'], '3p': ['ονται', 'ουνται', 'ωνται']}.get(pn, [])
    for e in sorted(cands, key=len, reverse=True):
        if b.endswith(e) and len(e) < len(b):
            return len(e)
    return 0


def split_end(tok, n):
    """split the token into stem + last n letters (combining marks stay with their letter)"""
    if n <= 0:
        return '', tok
    d = ud.normalize('NFD', tok)
    count, i = 0, len(d)
    while i > 0:
        i -= 1
        if not ud.combining(d[i]):
            count += 1
            if count == n:
                break
    return ud.normalize('NFC', d[:i]), ud.normalize('NFC', d[i:])


# ------------------------------------------------------------------ media
GREEK_RX = re.compile('[Ͱ-Ͽἀ-῿]')


def tts_text(s):
    s = re.sub(r'<[^>]+>', '', s)
    for a, b in (('«', ''), ('»', ''), ('“', ''), ('”', ''), ('·', ','), ('·', ','), (';', '?'), (';', '?'),
                 ('—', ','), ('–', ','), ('᾽', ''), ("'", ''), ('’', '')):
        s = s.replace(a, b)
    return s.replace('ζ', 'δζ').replace('Ζ', 'Δζ')


def phonemes(text):
    out = ''
    for part in re.split(r'([,.;?!]+)', text):
        if GREEK_RX.search(part):
            x = subprocess.run(['espeak-ng', '-v', 'grc', '-q', '-x', part], capture_output=True,
                               text=True, check=True).stdout
            x = ' '.join(x.split()).replace('e:', 'eI')
            out += f'[[{x}]]'
        else:
            out += part + ' '
    return out


CLOZE2 = os.environ.get('CLOZE2', '0') == '1'      # Cloze 2 off by default (user's decision 2026-11-24); CLOZE2=1 brings it back
AUDIO_MODE = os.environ.get('AUDIO_MODE', 'espeak')   # 'ext': the ElevenLabs clips (athv_*.mp3), made outside the build
EXT_MANIFEST = {}


def audio_ext(gr):
    from mono import modern
    t = modern(re.sub(r'<[^>]+>', '', gr))
    fn = 'athv_%s.mp3' % hashlib.sha1(t.encode()).hexdigest()[:12]
    EXT_MANIFEST[fn] = t
    return fn


def audio(gr, rate=RATE):
    if AUDIO_MODE == 'ext':
        return audio_ext(gr)
    t = tts_text(gr)
    h = hashlib.sha1(f'v2|{t}|{rate}'.encode()).hexdigest()[:12]
    fn = f'athc_{h}.mp3'
    path = os.path.join(MEDIA, fn)
    if not os.path.exists(path):
        wav = path[:-4] + '.wav'
        subprocess.run(['espeak-ng', '-v', 'grc', '-s', str(rate), '-g', '4', '-w', wav, phonemes(t)], check=True)
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', wav, '-af', 'loudnorm=I=-18:TP=-2',
                        '-ar', '24000', '-ac', '1', '-b:a', '48k', path], check=True)
        os.remove(wav)
    return fn


for f in ('Regular', 'Bold', 'Italic'):
    shutil.copy(os.path.join(FONTS, f'_GentiumPlus-{f}.ttf'), MEDIA)

# ------------------------------------------------------------------ note type
CSS = r"""
@font-face { font-family: 'GPdeck'; src: url('_GentiumPlus-Regular.ttf'); }
@font-face { font-family: 'GPdeck'; src: url('_GentiumPlus-Bold.ttf'); font-weight: bold; }
@font-face { font-family: 'GPdeck'; src: url('_GentiumPlus-Italic.ttf'); font-style: italic; }
.card { font-family: 'GPdeck', 'Gentium Plus', 'Noto Serif', serif; font-size: 20px;
        line-height: 1.45; text-align: center; padding: 6px 4px; }
.gr { font-family: 'GPdeck', 'Gentium Plus', 'Noto Serif', serif; }
.big { font-size: 1.55em; line-height: 1.5; }
.en { font-size: 1em; margin: .65em auto .2em; max-width: 34em; }
.new { color: #b03a2e; font-weight: bold; }
.gloss { font-size: .8em; color: #625a49; margin: .45em auto 0; max-width: 34em; line-height: 1.6; }
.note { font-size: .74em; color: #8c846f; margin: .3em auto 0; max-width: 31em; line-height: 1.45; }
.listen { font-size: .7em; color: #a39a85; letter-spacing: .12em; margin-bottom: .5em; }
.cloze { color: #b03a2e; font-weight: bold; }
.ehint { font-size: .85em; color: #7a7262; margin-top: .7em; font-style: italic; }
.src { font-size: .62em; color: #b0a78f; margin-top: .8em; }
.nightMode .new, .night_mode .new, .nightMode .cloze, .night_mode .cloze { color: #ff9b8c; }
.nightMode .gloss, .night_mode .gloss { color: #c8bfa9; }
.nightMode .note, .night_mode .note { color: #9a927e; }
.nightMode .ehint, .night_mode .ehint { color: #b5ad9c; }
"""

BACK_INFO = """<div class="en">{{English}}</div>
{{#New}}<div class="gloss">{{New}}</div>{{/New}}
{{#Notes}}<div class="note">{{Notes}}</div>{{/Notes}}
{{#Source}}<div class="src">{{Source}}</div>{{/Source}}"""

MODEL = genanki.Model(
    1846207541, 'Spoonfed Ancient Greek',
    fields=[{'name': n} for n in ['Order', 'Greek', 'Audio', 'English', 'New', 'Notes',
                                  'Cloze', 'ClozeAnswer', 'ClozeHint', 'Cloze2', 'Cloze2Answer', 'Cloze2Hint',
                                  'Source', 'Chapter', 'TTS']],
    templates=[
        {'name': '1 Listening',
         'qfmt': '<div class="listen">LISTEN</div>{{Audio}}',
         'afmt': '{{Audio}}<hr id="answer"><div class="gr big">{{Greek}}</div>' + BACK_INFO},
        {'name': '2 Cloze',
         'qfmt': '<div class="gr big">{{Cloze}}</div>{{#ClozeHint}}<div class="ehint">{{ClozeHint}}</div>{{/ClozeHint}}',
         'afmt': '<div class="gr big">{{ClozeAnswer}}</div><hr id="answer">{{Audio}}' + BACK_INFO},
        {'name': '3 Cloze 2',
         'qfmt': '{{#Cloze2}}<div class="gr big">{{Cloze2}}</div>'
                 '{{#Cloze2Hint}}<div class="ehint">{{Cloze2Hint}}</div>{{/Cloze2Hint}}{{/Cloze2}}',
         'afmt': '<div class="gr big">{{Cloze2Answer}}</div><hr id="answer">{{Audio}}' + BACK_INFO},
    ], css=CSS, sort_field_index=0)


def guid(gr):
    return genanki.guid_for('athenaze-companion-v1', OVERRIDE.get(gr, gr))


OVERRIDE = {}          # edited sentence → its original text, so that the note keeps its GUID
p = os.path.join(ROOT, 'guid_overrides.txt')
if os.path.exists(p):
    for line in open(p, encoding='utf-8'):
        if '→' in line:
            new, old = [K.nfc(x.strip()) for x in line.split('→', 1)][::-1]
            OVERRIDE[new] = old


# Cloze choices of the delivered deck: a note keeps its Cloze 1 / Cloze 2 item (or its lack of a Cloze 2) while its
# Greek and its new items are unchanged, so that reordering cards does not change cards users have reviewed.
# cloze_lock.tsv: guid, greek, new (sorted, comma-joined), c1, c2. Every build writes out/cloze_choices.tsv.
LOCK = {}
p = os.path.join(ROOT, 'cloze_lock.tsv')
if os.path.exists(p) and os.environ.get('CLOZE_LOCK', '1') != '0':
    for line in open(p, encoding='utf-8').read().split('\n')[1:]:
        if line.strip():
            g, gr, nw, l1, l2 = line.split('\t')
            LOCK[g] = (K.nfc(gr), nw, l1, l2)
LOCKSTAT = {'locked': 0, 'c1 kept': 0, 'c2 kept': 0, 'c1 changed': 0, 'c2 changed': 0}


def render(gr, toks, marks):
    """marks: {token index: (kind, cut)} kind 'hl' (red) | 'blank' | 'ans'; cut = letters of the ending (0 = word)"""
    out, last = [], 0
    for i, (a, b, t) in enumerate(toks):
        if i in marks and marks[i] == ('blank', 0) and (i - 1) in marks and marks[i - 1] == ('blank', 0):
            last = b                                         # one blank for a whole phrase
            continue
        out.append(html.escape(gr[last:a], quote=False))
        if i in marks:
            kind, cut = marks[i]
            stem, end = split_end(t, cut)
            if kind == 'blank':
                out.append(html.escape(stem) + '<span class="cloze">[…]</span>')
            else:
                out.append(html.escape(stem) + '<span class="new">%s</span>' % html.escape(end))
        else:
            out.append(html.escape(t))
        last = b
    out.append(html.escape(gr[last:], quote=False))
    return ''.join(out)


def cloze_for(c, item):
    """→ (front, answer, hint) for one item of the card"""
    idx = c['items'].get(item, [])
    if not idx:
        return None
    if item.startswith('S:'):
        i = idx[0]
        return (render(c['gr'], c['toks'], {i: ('blank', 0)}), render(c['gr'], c['toks'], {i: ('ans', 0)}),
                '(%s, %s)<br>%s' % (stem_parts(item) + (html.escape(c['en'], quote=False),)))
    if item.startswith(('L:', 'C:')) or item in K.XLEMMA:   # a sense item blanks the whole word, like a new word
        cut = 0
        hint = gloss(item)
        if item.startswith('L:') and (hint == '(name)' or not hint):
            return None
        marks_b = {i: ('blank', 0) for i in idx}
        marks_a = {i: ('ans', 0) for i in idx}
        hint = '(%s)' % hint
    else:
        i = idx[0]
        tok = c['toks'][i][2]
        cut = ending_of(item, tok)
        lemma = c['chosen'][i][0] if c['chosen'][i] else ''
        marks_b = {i: ('blank', cut)}
        marks_a = {i: ('ans', cut)}
        hint = '(%s%s)<br>%s' % (lemma + ', ' if lemma and lemma != 'ὁ' else '', key_label(item), html.escape(c['en'], quote=False))
    return render(c['gr'], c['toks'], marks_b), render(c['gr'], c['toks'], marks_a), hint


# ------------------------------------------------------------------ notes
notes, keys, rows = [], {}, []
first_seen = {}
for n, c in enumerate(CARDS):
    for x in c['items']:
        first_seen.setdefault(x, n)
BASE = 100
seen_before = {}
CHOICES = []
for n, c in enumerate(CARDS):
    new = sorted([x for x in c['new'] if not K.is_bundled(x, c['new'], c['items'])] or c['new'],
                 key=lambda x: (not x.startswith('L:'), not x.startswith('S:'), not x.startswith('C:')))
    hl = {}
    for x in c['new']:
        for i in c['items'].get(x, []):
            cut = 0 if x.startswith(('L:', 'C:', 'S:')) or K.is_bundled(x, c['new'], c['items']) else ending_of(x, c['toks'][i][2])
            hl.setdefault(i, ('hl', cut))
            if cut == 0:
                hl[i] = ('hl', 0)
    greek = render(c['gr'], c['toks'], hl)
    lines = []
    for x in new:
        i = (c['items'].get(x) or [None])[0]
        form = c['toks'][i][2] if i is not None else ''
        lines.append(new_line(x, form))
    # cloze 1: the new item; on practice cards the item met most recently before this card
    def lemma_bound(x):          # a form-key that goes with its own lemma item in this card (εἰμί:pi3s + L:εἰμί)
        return ':' in x and not x.startswith(('L:', 'C:', 'X:', 'S:')) and ('L:' + x.split(':', 1)[0]) in c['items']
    order = sorted((x for x in c['items'] if (not x.startswith('X:') or x in K.XLEMMA) and not lemma_bound(x)),
                   key=lambda x: -first_seen.get(x, 0))
    # a new form of a known pronoun / irregular word (ὅν, μοι …) is clozed as a form: hint = word + case
    c1 = next((x for x in new if (not lemma_bound(x) or ('L:' + x.split(':', 1)[0]) not in c['new'])
               and cloze_for(c, x)), None)
    if c1 is None:
        c1 = next((x for x in order if cloze_for(c, x)), None)
    # cloze 2: another item of the sentence that is still fresh (met in the last 12 cards), on another word
    c2 = next((x for x in order if x != c1 and n - first_seen.get(x, 0) <= 12 and cloze_for(c, x)
               and not (c1 and set(c['items'][x]) & set(c['items'][c1]))), None)
    lk = LOCK.get(guid(c['gr']))
    if lk and lk[0] == c['gr'] and lk[1] == ','.join(sorted(c['new'])):
        LOCKSTAT['locked'] += 1
        l1, l2 = lk[2] or None, lk[3] or None
        if l1 and l1 in c['items'] and cloze_for(c, l1):
            LOCKSTAT['c1 kept' if l1 == c1 else 'c1 changed'] += 1
            c1 = l1
        if l2 is None or (l2 in c['items'] and l2 != c1 and cloze_for(c, l2)
                          and not (c1 and set(c['items'][l2]) & set(c['items'][c1]))):
            LOCKSTAT['c2 kept' if l2 == c2 else 'c2 changed'] += 1
            c2 = l2
    if not CLOZE2:               # the deck is purely n+1: no second cloze (template kept, fields empty -> no card)
        c2 = None
    CHOICES.append((guid(c['gr']), c['gr'], ','.join(sorted(c['new'])), c1 or '', c2 or ''))
    cz = list(cloze_for(c, c1)) if c1 else ['', '', '']
    cz += list(cloze_for(c, c2)) if c2 else ['', '', '']
    src = '' if c['src'] == 'composed' else c['src']
    order_s = '%04d' % (n + 1)
    tags = ['companion', 'ch%02d' % c['chapter'], 'new' if c['new'] else 'practice']
    g = guid(c['gr'])
    note = genanki.Note(model=MODEL, guid=g, tags=tags,
                        fields=[order_s, greek, '[sound:%s]' % audio(c['gr']), html.escape(c['en'], quote=False),
                                '<br>'.join(lines), '', *cz, html.escape(src, quote=False),
                                'Athenaze %d' % c['chapter'] if c['chapter'] <= 31 else 'Supplement (Smyth)',
                                c['gr']])
    notes.append(note)
    keys[g] = {0: BASE + n * 10, 1: BASE + (n + 3) * 10 + 5, 2: BASE + (n + 8) * 10 + 6}
    rows.append(dict(n=n + 1, ch=c['chapter'], gr=greek, en=c['en'], new='<br>'.join(lines),
                     c1=cz[0], h1=cz[2], c2=cz[3], h2=cz[5], src=src))

DESC = """<b>Spoonfed Ancient Greek</b>: Greek sentences that follow the syllabus of <i>Athenaze</i> I–II
(Italian edition, ch. 1–31) and <i>Meletemata</i>, chapter by chapter. Chapter 32 adds grammar from Smyth that the
book does not treat. The sentences are composed for the deck; the classical passages <i>Athenaze</i> quotes are in
their authors' own words, with the reference under the answer.<br><br>
Every sentence brings exactly <b>one</b> new thing, shown in <span style="color:#b03a2e"><b>red</b></span>.
Everything else in it has come before.<br><br>
<b>Listening</b>: hear the sentence, understand it, then check the text and translation.<br>
<b>Cloze</b>: recall the missing word or ending from the hint. It comes a few cards after its listening card.<br><br>
<b>Deck options</b>:
<ul>
<li>New card gather order <i>Deck</i>, sort order <i>Order gathered</i>. Never shuffle.</li>
<li><i>Bury new siblings</i> <b>off</b>.</li>
<li>30–50 new cards a day (15–25 sentences). Experienced readers of Greek, using the deck for listening and speaking, can take many more.</li>
<li>FSRS on, desired retention about 0.90.</li>
</ul>
Audio: ElevenLabs voice <i>Giassiranis Dimitrios</i>, modern pronunciation of Greek.<br>
Licence: CC BY-NC-SA 4.0. More at github.com/proclus381/spoonfed-ancient-greek"""


def write_pkg(path):
    deck = genanki.Deck(DECK_ID, DECK_NAME, description=DESC)
    for nt in notes:
        deck.add_note(nt)
    used = set()
    for nt in notes:
        for f in nt.fields:
            used |= set(re.findall(r'\[sound:([^\]]+)\]', f))
    used |= {f for f in os.listdir(MEDIA) if f.startswith('_')}
    pkg = genanki.Package(deck)
    pkg.media_files = [os.path.join(MEDIA, f) for f in sorted(used) if not f.startswith('athv_')]
    if EXT_MANIFEST:
        with open(os.path.join(OUT, 'audio_manifest.tsv'), 'w', encoding='utf-8') as fh:
            for fn, t in EXT_MANIFEST.items():
                fh.write('%s\t%s\n' % (fn, t))
    pkg.write_to_file(path)
    tmp = tempfile.mkdtemp()
    with zipfile.ZipFile(path) as z:
        z.extractall(tmp)
    db = sqlite3.connect(os.path.join(tmp, 'collection.anki2'))
    rws = db.execute('select c.id, c.ord, n.guid from cards c join notes n on c.nid = n.id').fetchall()
    for pos, (cid, _, _) in enumerate(sorted(rws, key=lambda r: keys[r[2]].get(r[1], keys[r[2]][0])), 1):
        db.execute('update cards set due=? where id=?', (pos, cid))
    db.commit()
    db.close()
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in os.listdir(tmp):
            z.write(os.path.join(tmp, f), f)
    shutil.rmtree(tmp)
    return len(rws)


def preview(path):
    h = ['<html><head><meta charset="utf-8"><style>body{font-family:Gentium Plus,serif;max-width:60em;margin:auto}'
         'td{border-bottom:1px solid #ddd;padding:4px 8px;vertical-align:top}.new{color:#b03a2e;font-weight:bold}'
         '.cloze{color:#b03a2e}.h{color:#888;font-size:.85em}</style></head><body><table>']
    for r in rows:
        h.append('<tr><td>%d<br><span class=h>ch%d</span></td><td style="font-size:1.2em">%s</td><td>%s'
                 '<div class=h>%s</div></td><td>%s<div class=h>%s</div>%s<div class=h>%s</div></td></tr>' %
                 (r['n'], r['ch'], r['gr'], html.escape(r['en']), r['new'], r['c1'], r['h1'], r['c2'], r['h2']))
    h.append('</table></body></html>')
    open(path, 'w', encoding='utf-8').write('\n'.join(h))


if __name__ == '__main__':
    last = CARDS[-1]['chapter']
    name = 'Athenaze_Companion_ch01-%02d%s.apkg' % (last, '_humanvoice' if AUDIO_MODE == 'ext' else '')
    for f in os.listdir(OUT):
        if f.endswith('.apkg') and (('_humanvoice' in f) == (AUDIO_MODE == 'ext')):
            os.remove(os.path.join(OUT, f))
    n_cards = write_pkg(os.path.join(OUT, name))
    preview(os.path.join(OUT, 'preview.html'))
    with open(os.path.join(OUT, 'cards.tsv'), 'w', encoding='utf-8') as f:
        f.write('n\tchapter\tgreek\tenglish\tnew\n')
        for c in CARDS:
            f.write('%d\t%d\t%s\t%s\t%s\n' % (c['n'], c['chapter'], c['gr'], c['en'], ', '.join(c['new'])))
    with open(os.path.join(OUT, 'cloze_choices.tsv'), 'w', encoding='utf-8') as f:
        f.write('guid\tgreek\tnew\tc1\tc2\n')
        for r in CHOICES:
            f.write('\t'.join(r) + '\n')
    print('cloze lock:', ', '.join('%s %d' % kv for kv in LOCKSTAT.items()),
          '(changed = the lock overrides what this order would pick)')
    print('notes', len(notes), 'cards', n_cards, '->', name)
