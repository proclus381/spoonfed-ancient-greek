# Paradigm coverage: one card per cell of every inflection scheme

Design notes from building the deck. Files named here that are not in the repository were working files.

Status 2026-11-25. Goal: a card for every possible grammatical form, checked against Smyth and Wiktionary's *Appendix:Ancient Greek grammar tables*. Also: cards that introduce forms
of one inflection scheme within a chapter should stand next to each other. The dual is kept bare.

## Result

- 4,735 notes (3,657 before), 9,470 cards; checker 0 problems in ch. 1–32. All 3,657 earlier notes keep their
  GUIDs.
- **1,078 new notes:**
  - 213 verb forms (batches 1–3, ch. 6–31);
  - 853 noun, adjective, pronoun, numeral and participle cells (batches 4–10, with the last verb forms of
    εἰμί, φημί, οἶδα, δεῖ, χρή);
  - 7 cards for the dual endings, plus 5 for the verb dual endings.
- 425 cards were moved within their chapter, so a scheme's cells stand together
  (`docs/paradigm_grouping_moves.tsv`).
- The new cards were reordered by the word-order scheme afterwards (`WORD_ORDER_PLAN.md` §7).
- The checker's coverage list (`not yet used`) still names the syllabus files' old, coarser keys (2:nom.s, 3:gen.s
  …). The per-cell keys have replaced them, so that list is no longer a gap report; use `catalog.py`.
- Every key the checker can produce for a syllabus word, and for the ch. 32 supplement words, is now taught,
  except the cells listed under *Not taught* below (`work/phase3/paradigms/catalog.py`).

## How the checker keys the cells (`project/check2.py`, `project/schemes.py`)

- **Nouns, adjectives, participles.**
  - Each word falls into a scheme by its own generated forms (nom., gen., acc., voc. sg.). The schemes and their
    Smyth paragraphs are listed in `schemes.py`:
    - 1st declension: -ᾱς, -ης (voc. -η), -της (voc. -ᾰ), -ᾱ / -ᾰ gen. -ᾱς, -ᾰ gen. -ης, -η;
    - 2nd declension: masc. and fem. in -ος, neuter, contracted, Attic, and the εὔνους type;
    - 3rd declension: velar, labial, dental (acc. -α / acc. -ν), the ντ-stems in -ας / -ων / -ους, -μα, other
      neuters in -τ-, nasal (vowel kept / alternating), liquid, syncopated -ηρ, -ως gen. -ωος, -ῡς gen. -ῠος,
      -ις and -υς gen. -εως, -εύς, -αῦς, -ώ, αἰδώς, σ-stems (-ης, -κλῆς, neuter -ος, neuter -ας);
    - adjectives: -ος -η -ον, -ος -ᾱ -ον, two endings, contracted, Attic, -ύς -εῖα -ύ, -ων -ον, comparatives in
      -ων, -ής -ές, -ᾱς -αινα -ᾰν, -εις -εσσα -εν, consonant stems;
    - participles: -ων, -ῶν -οῦσα, -ῶν -ῶσα, -ᾱς, -εις, -ους, -ύς, -ώς -υῖα, -ώς -ῶσα (ἑστώς), -μενος.
  - A key is `scheme:case.number(.genders)`, e.g. `3κ:gen.s` (φύλακος), `Aυς:dat.p.f` (βαθείαις),
    `Pας:gen.s.mn` (λύσαντος).
  - Genders that share a form in every word of a scheme are one cell: `Aοη:gen.s.mn` (σοφοῦ), `A2:dat.s.mfn`.
  - Each case is a cell of its own, also where its form equals another's:
    - the neuter accusative (τὸ δένδρον as object);
    - the vocative plural (ὦ ἄνδρες).

    The analysis reads both (`syncretic()` in `check2.py`). After ὦ it takes the vocative. Without ὦ, or a hint, it
    never takes the vocative. A neuter's vocative is its nominative.
  - The nominative singular (masc. for adjectives and participles) is the word's citation form, not a separate
    item. A participle's first form brings its declension cell with it (one item).
- **Irregular words** keep one key per lemma and cell: pronouns, numerals, πατήρ, ἀνήρ, γυνή, πόλις, βασιλεύς,
  ναῦς, βοῦς, πῦρ … (`SPECIFIC`). Their cells were filled in the same way.
- **Verbs:** the keys are unchanged (tense, voice, mood, class, person); batches 1–3 filled their gaps.
- **The dual, kept bare**: one item per ending, from ch. 30, whatever the paradigm:
  - nouns, adjectives, participles and pronouns: -ω, -ᾱ, -ε, -ει, -οιν, -αιν;
  - the personal pronouns: νώ σφώ, νῷν σφῷν;
  - verbs: -τον, -την, -σθον, -σθην, -των, -σθων.

  Dual forms are recognised everywhere through `project/forms_dual.txt`, which adds readings and replaces none.
  Its verb forms are made by rule from the plural (`work/phase3/paradigms/dualgen.py`).
- `ATH_COARSE=1` gives back the old, coarser keys, for comparison.

## Added to the syllabus (ch. 32, Smyth supplement)

The schemes the syllabus had no word for:

| Word | Scheme | Smyth |
|---|---|---|
| ὀδούς | ντ-stem in -ούς | §258 |
| γραῦς | -αῦς | §275 |
| πειθώ | -ώ | §279 |
| αἰδώς | αἰδώς | §266 |
| Περικλῆς (a name) | -κλῆς | §265 |
| εὔνους | contracted, two endings | §290 |
| χαρίεις | -εις -εσσα -εν | §299 |

The cells of ἵλεως (Attic declension, ch. 2 word) are in ch. 32 too.

## Not taught (deliberately)

- **Vocatives the generator gives wrongly as equal to the nominative:** γίγας, γέρων, ῥήτωρ, ἔρις, βότρυς,
  ἀμείνων. The real forms (γίγαν, γέρον, ῥῆτορ …) are taught where the scheme has them.
- **Rare vocatives:** of 3rd-declension nasal oxytones (ὦ χειμών), of consonant-stem adjectives (ἄχειρ), and the voc. pl.
  of ὀδούς. Also the voc. sg. and pl. of ἵλεως.
- **Compounds of εἰμί** (πάρειμι, ἄπειμι, ἔξεστι): their forms are εἰμί's with a prefix. Their own keys are taught
  where the book uses them.
- **Schemes covered by one lemma-specific word:** ἄστυ (-υ gen. -εως), βοῦς (-οῦς), κανοῦν (contracted
  neuter), κρέας (neuter -ας).
- **The article:** it carries no key. Its forms come with the noun cells from ch. 1.
- **The future optative, future perfect and optative of the -μαι athematic verbs:** each is a single item, as
  before.
- **Generator artifacts:** δύναμαι conjugated as a contract verb (δυναμῶ …), and ἄγω's aorist middle as a key of
  its own.

## Tools

| Path | What it does |
|---|---|
| `work/phase3/paradigms/catalog.py` | every key the generator and `forms_extra.txt` can produce, taught or not |
| `plan2.py` | where an untaught cell's card goes |
| `known_at.py`, `show.py` | the vocabulary known before a card; cards with their new items |
| `ambig.py` | cell introductions on case-ambiguous forms, to review |
| `mk_inserts.py` | `NEW.tsv` → `deck_edit.py` INSERT operations |
| `group.py` | the grouping moves |
| `new_b1.tsv` … `new_b11.tsv` | the batches as inserted |
| `work/phase3/paradigms/wikt_tables.py` | parses the Wiktionary appendix (downloaded raw wikitext in `corpus/wiktionary_tables_20261124/`) |
