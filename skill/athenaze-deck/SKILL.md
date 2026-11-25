---
name: athenaze-deck
description: Check, extend and rebuild the Athenaze Companion Anki deck (n+1 Ancient Greek sentences). Use when asked to add or rewrite cards, check a chapter for n+1 problems, find grammatical forms no card teaches, fix word order, or build the apkg.
---

# Athenaze Companion deck tools

The deck lives in `toolkit/` (or in a clone of the repository): `project/sentences/chNN.txt`, one card per line:
`Greek | English | source | extras`. The extras are:
- hints `@form[=lemma][:feat.feat]` (features: nom gen dat acc voc, s p d, m f n, 1s…3p 2d 3d, pres impf aor fut
  pf plpf, ind subj opt imp inf ptc);
- manual items `+X:…`.

Set up once: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt` (greek-accentuation, genanki).

## The rules every card keeps

1. **Exactly one new item per card.** An item is one of:
   - a word `L:lemma`;
   - a grammar cell (`Vpai:3s`; `3κ:gen.s`; `Aοη:dat.p.f`; `Pας:gen.s.mn`; lemma-specific `πατήρ:dat.p.m`);
   - a set phrase `C:…`;
   - a construction `X:…`;
   - a principal-part stem `S:…`.

   Everything else in the sentence must be known by then.
2. **No practice cards:** a card with nothing new is a problem.
3. **Composed sentences.** No text from the textbooks (copyright). Classical quotations only in the author's own
   words.
4. **GUIDs stay stable.** Edit with `tools/deck_edit.py` only. REPLACE keeps the note's GUID; never renumber.
5. **Word order** (docs/WORD_ORDER_PLAN.md):
   - a continuing subject is left out, or follows the verb when minor;
   - a subject stays first only when it is the card's topic (it holds the new item, or the statement is generic);
   - definite objects follow the verb unless the card gives a reason (πᾶς, a demonstrative, μέν / δέ);
   - vocatives go after the first word or phrase;
   - no definite object first with the subject after the verb.

## Workflows

**Check the deck** (0 problems is the target):

    tools/chk.sh            # or: cd project && ../.venv/bin/python check2.py -q --cover $(ls sentences/ch[0-9][0-9].txt | sort)

Problem lines end with `<-- 2 NEW`, `nothing new`, `unknown form …`, `too early: …`, `hint matches no analysis`.

**Add cards for missing forms:**

1. Dump the items:

       .venv/bin/python tools/items_dump.py                  # work/tmp/items.json

2. List what no card teaches yet:

       cd project && ../.venv/bin/python ../work/phase3/paradigms/catalog.py ../work/tmp/catalog.tsv

3. Plan where each cell's card goes and which words are candidates:

       .venv/bin/python work/phase3/paradigms/plan2.py $PWD/work/tmp/catalog.tsv $PWD/work/tmp/plan.tsv

4. Look up what vocabulary a new card may use at its place, and look at the cards around it:

       python3 work/phase3/paradigms/known_at.py N           # vocabulary known before card N
       python3 work/phase3/paradigms/show.py A B             # cards A..B with their new items

5. Write `NEW.tsv` rows `anchor<TAB>Greek<TAB>English[<TAB>extras]`. The anchor is a card number or that card's
   Greek. Add hints for every form whose case, gender or person is ambiguous.
6. Turn the rows into insert operations, apply them, and check:

       python3 work/phase3/paradigms/mk_inserts.py NEW.tsv ops.txt && python3 tools/deck_edit.py ops.txt && tools/chk.sh

7. Fix any problem and run step 6 again (`git checkout project/sentences/` reverts the files).
8. Confirm the GUIDs:

       .venv/bin/python tools/guid_check.py

**Group a chapter's paradigm cards:**

    .venv/bin/python work/phase3/paradigms/group.py $PWD/ops.txt && python3 tools/deck_edit.py ops.txt

**Word-order quality control:**
- Measures:
  - `.venv/bin/python tools/phase3/style4.py - - -`, the deck by clause class;
  - `work/phase3/infostructure/objpos.py 1 32`, fronted definite objects;
  - `is_propose.py 1 32 OUT.tsv`, the subject options and flags.
- `newcards.py` proposes reorders by the rules above, and `newcards_apply.py` writes the REPLACE ops. Read every
  proposal before applying it.

**Build:**

    cd project && ../.venv/bin/python build.py                  # eSpeak audio (needs espeak-ng with grc, ffmpeg)
    AUDIO_MODE=ext ../.venv/bin/python build.py                 # human-voice deck (audio via audio_kit/)

## Files to know

- `project/check2.py` is the checker. `project/schemes.py` holds the inflection schemes (Smyth §).
- `project/forms_extra.txt` holds hand-made analyses. They override the generator, so give every reading of a
  form there.
- `project/forms_dual.txt` holds dual forms. They are added to a form's other readings.
- `project/syllabus/chNN.txt`: the words and items of each chapter.
- `docs/PARADIGM_COVERAGE.md` and `docs/WORD_ORDER_PLAN.md`: the design and the measures.
