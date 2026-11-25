# An n+1 sentence deck for Ancient Greek (Anki)

A sentence deck that follows the syllabus of **Athenaze I–II (Italian edition,
ch. 1–31) and Meletemata**, chapter by chapter. Chapter 32 is a supplement of grammar from Smyth's *Greek Grammar*
that the book does not treat.

- **4,735 notes, 9,470 cards** (a listening card and a cloze card per note).
- **Purely n+1:** every card brings exactly one new thing — a word, an ending or form, a verb stem, a set phrase, a
  construction, a later sense of a word. Everything else in the sentence you have seen before.
- **Every form.** Every cell of every inflection scheme in Smyth and in Wiktionary's Ancient Greek grammar
  tables has a card: every verb ending, and every case, number and gender of every noun, adjective, pronoun and
  participle type. Within a chapter, the forms of one paradigm come one after the other. The dual is kept bare:
  one card per dual ending.
- **Natural Greek.** The sentences are composed for the deck. Their word order follows what each card presents as
  given or new (after Dik and Mastronarde), checked against Attic prose. The exception is the classical passages
  that Athenaze itself quotes, which are given in the authors' own words.
- **No text from Athenaze or Meletemata is in the deck.** The books gave only the order of what is taught.

## Download

From the [Releases](../../releases) page:

| File | What it is |
|---|---|
| `SAG_synthetic.apkg` | the deck with low quality synthetic (eSpeak) audio in reconstructed pronunciation  |
| `SAG_generated.apkg` | the deck with high quality Elevenlabs-generated audio in Modern Greek pronunciation |
| `SAG-deck-skill.zip` | the deck's tools as a Claude skill (see *Tools*) |

Import the apkg in Anki (File → Import). Updates import over the old version, and your review history is kept.

## 1. Before you start: for absolute beginners

The deck teaches the language sentence by sentence. It assumes you can read the script and know what grammar words
mean.

1. **The alphabet and the sounds.**
   - Learn to read every letter, the breathings (ἁ / ἀ), the iota subscript (ᾳ) and the diphthongs, until you can
     read a line aloud without stopping.
   - Watch Luke Ranieri's beginner series *Ancient Greek in Action*, in order:
     - [the playlist, in ascending order](https://www.youtube.com/playlist?list=PLU1WuLg45Six4gYLaBrTAIvfjXWKJ1EkN);
     - [his channel, ScorpioMartianus](https://www.youtube.com/c/ScorpioMartianus/playlists).

     He teaches in Greek, from zero, with pictures and gestures. That is the best first contact with the sounds
     and the alphabet.
   - A note on pronunciation: his videos use a reconstructed ancient pronunciation. The deck's audio reads Greek
     in the Modern Greek way. Pick one for your own reading aloud and keep to it; listening to both does no harm.
2. **Accents, roughly.**
   - Know that there are three (acute, grave, circumflex). Know that the grave stands for an acute before another
     word.
   - Know that accents sometimes tell two forms apart. You do not need the rules yet.
3. **Grammar words.**
   - Be sure what these mean: case (nominative, genitive, dative, accusative, vocative), number (singular, plural,
     dual), gender, person, tense, mood, voice (active, middle, passive), participle, infinitive.
   - Any short introduction to grammar terms will do.
4. **The article.** Learn the table of ὁ, ἡ, τό by heart. It is the key to every noun ending, and the deck uses it
   from the first card without teaching it separately.
5. **Get the book.**
   - The deck follows *Athenaze* (Italian edition). Reading their chapters alongside is the
     intended use.
   - Any edition helps, since the chapter content is close. The deck never copies their text.

## 2. How to use the deck for the best results

**Anki settings**

- **New cards in deck order.** Under *New cards*, set *Gather order: Deck* and *Sort order: Order gathered*. The
  n+1 design depends on the order: a card is only easy because the ones before it came first. Never shuffle the
  new cards.
- **15–25 new notes a day** is a good pace: about 30–50 new cards with both card types, and roughly an hour a day
  once the reviews build up. Keep the pace steady rather than high.
- Use **FSRS** (Settings → FSRS) with a desired retention of about 0.90.
- **Don't bury the siblings by hand.** The listening card and the cloze card train different skills.

**Doing a card**

- **Listening card:**
  1. Play the audio and understand the sentence before you look.
  2. Say the meaning aloud, in English or in your head.
  3. Then check the Greek and the English.
  4. Repeat the Greek aloud once, imitating the audio.
- **Cloze card:**
  1. Read the whole sentence.
  2. Produce the missing word, or its ending, from the hint.
  3. Say the whole sentence aloud.

  Grade honestly: "Again" if you didn't comprehend the audio or the answer for the cloze was wrong.
- **When a new form arrives in a run of its paradigm** (σοφοῦ, σοφῷ, σοφῶν …), notice the pattern. Write the
  paradigm out once by hand when its run is over.

**On the side**

- **Read the book chapter by chapter.** When the deck reaches a chapter, read its reading in Athenaze aloud, twice. It will feel easy: that is the point.
- **Listen a lot.**
  - Keep watching Ranieri's *Ancient Greek in Action* and his other Greek videos.
  - Replay the deck's audio of a chapter you have finished while walking or commuting.
- **Look things up in Smyth** when a form or construction puzzles you. The deck's ch. 32 cards cite his
  paragraphs.
- **Write a little.** Each week, write five short sentences of your own with the week's new words and forms.
- **Don't cram.** Doing the reviews every day matters more than how many new cards you add.

## Audio

- **The eSpeak apkg** has its audio inside.
- **The human-voice apkg** Elevenlabs generated with

## Tools

The scripts that built and checked the deck are included:

| Script | What it does |
|---|---|
| `project/check2.py` | the n+1 checker: for every card, the items it brings and the problems (two new items, nothing new, unknown forms, items before their chapter). `tools/chk.sh` runs it on the whole deck. |
| `project/schemes.py` | sorts each noun, adjective and participle into its inflection scheme (Smyth §), so the checker keys every cell |
| `project/morph.py`, `morph2.py`, `parts.py` | the paradigm generator the checker analyses forms with |
| `tools/deck_edit.py` | edits the deck safely: INSERT, REPLACE (keeps the note's GUID), MOVE, EXTRAS (hints), DELETE |
| `tools/guid_check.py`, `tools/regress_notes.py`, `tools/items_dump.py` | GUID safety and per-note regression |
| `work/phase3/paradigms/catalog.py` | every grammatical cell the syllabus can produce, and whether a card teaches it |
| `work/phase3/paradigms/plan2.py`, `known_at.py`, `mk_inserts.py` | where a missing cell's card goes, what vocabulary it may use, and the insert operations |
| `work/phase3/paradigms/group.py` | puts a paradigm's cards next to each other within a chapter |
| `work/phase3/paradigms/dualgen.py` | verb dual forms by rule |
| `tools/phase3/style4.py`, `work/phase3/infostructure/*.py` | the word-order checks (subject and object position, the One Lexical Argument Constraint, vocatives) and the reorder proposer |
| `project/build.py` | builds the apkgs (genanki) |

Setup:

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cd project && ../.venv/bin/python check2.py -q --cover $(ls sentences/ch[0-9][0-9].txt | sort)
```

**As a Claude skill:**
1. Unzip `SAG-deck-skill.zip` into `~/.claude/skills/`.
2. Claude Code then knows how to check, extend and rebuild the deck with these tools: ask it to add a card,
   check a chapter, find untaught forms or fix word order.

## Credits and licences

- **Grammar:** H. W. Smyth, *Greek Grammar* (1920), and Wiktionary's *Appendix: Ancient Greek grammar tables*,
  for the inflection schemes.
- **Quotations:** the classical passages are in the authors' own words, after the Perseus and eulogikon
  editions.
- **Treebank lexicon:** `project/tb/lexicon.json` is derived from the Perseus Ancient Greek Dependency Treebank
  (CC BY-SA 3.0) and the PROIEL treebank (CC BY-NC-SA 3.0), and is shared under CC BY-NC-SA 3.0.
- **Fonts:** Gentium Plus (SIL Open Font Licence).
- **Not affiliated** with the publishers of Athenaze or Meletemata.
