# Build, audio and release

## Build

- **`project/build.py`** (genanki) reads `sentences/ch*.txt` in order, runs the checker to get each card's
  items, and writes the outputs to `project/out/`:
  - `Athenaze_Companion_ch01-32.apkg` (named after the last chapter; ch. 32 is the Smyth supplement), with
    eSpeak audio. Set `AUDIO_MODE` unset or to `espeak`; about
    5 minutes.
  - `Athenaze_Companion_ch01-32_humanvoice.apkg`, with `AUDIO_MODE=ext`. Audio files are *not* inside: the
    user's audio kit installs them into Anki's media folder.
  - `audio_manifest.tsv` (filename, text to speak), `cards.tsv` (checker table) and `preview.html`.
- **Paths:**
  - `FONTS` points to `/home/claude/build/out/media`. The three Gentium Plus TTFs are now in
    `project/fonts/`; point `FONTS` there.
  - The eSpeak path needs `espeak-ng` with the `grc` voice, plus `ffmpeg`.
- **Note type:** three templates (Listening, Cloze, "3 Cloze 2"). Since 2026-11-24 the build leaves the Cloze 2
  fields empty, so Anki makes no Cloze 2 cards; the template stays, so the note type is unchanged. `CLOZE2=1`
  brings them back.
- **`DESC` in `build.py`** is the deck description shown in Anki. It says the sentences are composed, except
  the classical passages that Athenaze itself quotes. Keep it true if that changes.
- **After every rebuild,** copy `out/cards.tsv` to `cards_current.tsv` as the new regression baseline.

## GUIDs

`guid(gr) = genanki.guid_for('athenaze-companion-v1', OVERRIDE.get(gr, gr))`.
- `guid_overrides.txt` holds lines of the form `original Greek → current Greek`, and `apply.py` appends to
  it.
- A note keeps its GUID as long as its current Greek maps back to the original text through this file.
- Never edit sentence files by hand without adding an override line. Use `apply.py`.
- Reordering cards does not change GUIDs. It does change the "Order gathered" position for new cards.

## Cloze lock

- `project/cloze_lock.tsv` (`guid, greek, new, c1, c2`) holds each note's Cloze 1 / Cloze 2 item in the delivered
  deck. The build keeps those choices while a note's Greek and new items are unchanged, so moving cards does not
  change cards users have reviewed. It prints how many choices it kept and how many it overrode.
- Every build writes `out/cloze_choices.tsv` in the same format. After a release, copy it to
  `cloze_lock.tsv` so the next update keeps that release's choices. `CLOZE_LOCK=0` builds without the lock.

## Audio (ai33.pro → ElevenLabs)

- **The kit is in `audio_kit/`;** the user runs it on their own machine. Usage:
  - `python3 generate.py credits | test | all | retry | install`;
  - `--voice <id>`, `--speed 0.9`;
  - the key goes in `key.txt` next to the script, or in the `AI33_KEY` environment variable;
  - the API base is `AI33_API`, by default `https://api.ai33.pro`.
- **Audio filenames:** `athv_<sha1(mono.modern(text))[:12]>.mp3`. `mono.modern()` normalises the text for
  Modern-Greek reading. `generate.py` skips existing files, so only changed sentences cost credits.
- **Open problem:** the last run returned `tts_reference_audio_error`. The likely cause is the default voice
  `elevenlabs_HXOQciguVdtIpvH2gB8g` becoming unavailable upstream; the ai33 site now redirects to a
  rebranded service, openspeaker.ai. Steps:
  - ask the user whether `audio/_errors.tsv` lists every sentence or only some;
  - test a line in the provider's web UI;
  - if the voice is gone, let the user choose: re-voice everything with a new voice (about 207,000
    characters) or mix voices;
  - keep the voice id in one place (`DEFAULT_VOICE` in `generate.py`).
- **After phase 4,** report to the user: the number of new clips and characters (compare the new
  `audio_manifest.tsv` with the previous one), and the change in Cloze 2 count.

## Release to the user

- **Send** the zip of `audio_kit/` with the updated manifest and humanvoice apkg, plus the eSpeak apkg if
  they want it.
- **The user's update steps:**
  1. Copy the old `audio` folder into the new kit.
  2. Run `python3 generate.py all`, then `install`.
  3. Import the apkg: notes update in place by GUID.
  4. Run Tools → Empty Cards: this removes the old Cloze 2 cards.
  5. Import does not delete notes. The practice notes of earlier versions are no longer in the deck: in the
     Browser search `"deck:Athenaze Companion" tag:practice` and delete what it finds (after the import,
     every note still in the deck carries the tag `new`).
  6. Optional, after a reorder: new cards already in the queue keep their old position. To follow the new
     order: Browse the deck's new cards, sort by the sort field, select all, Cards → Reposition (start 0, step 1,
     shift positions).
- **Recommended deck settings,** for the description: bury new siblings OFF; new card order "Order
  gathered"; 20–30 new cards a day; FSRS on.
