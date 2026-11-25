# Word order by information structure: a plan (after Dik 1995 and Mastronarde 2013)

Design notes from building the deck. Files named here that are not in the repository were working files.

Status: applied to the whole deck, 2026-11-24. The results are in §6.

## Sources

- H. Dik, *Word Order in Ancient Greek: A Pragmatic Account of Word Order Variation in Herodotus* (Amsterdam 1995).
- D. Mastronarde, *Word Order in Ancient Greek (especially Attic Prose)*, Ancient Greek Tutorials (2013).

Both are paraphrased below, not quoted.

## 1. What they say that bears on the deck

1. **The clause pattern is SETTING – TOPIC – FOCUS – VERB – REST.**
   - Dik's template is P1 (Topic), P0 (Focus, immediately before the verb), V, X. Setting material (time,
     place, participial or temporal clauses) can come before it. Mastronarde gives the same order.
   - Each clause has normally one Topic (the point of orientation) and one Focus (the most salient new
     information).
   - Everything after the verb carries no pragmatic function. It is either given and predictable, or new
     but unimportant.
2. **Whether a referent is given does not decide where it goes; its function in the clause does.** A
   referent can be Topic, Focus or neither.
   - Dik's examples from Herodotus: Candaules, the topic as the story switches to him, is clause-initial
     (ὁ δὲ Κανδαύλης …).
   - Gyges, given and wholly predictable, comes last (ἐθηεῖτο ὁ Γύγης).
3. **A stated subject goes before the verb when it is a Topic:**
   - a topic shift or a contrast (ὁ μὲν … ὁ δέ, X δέ …);
   - resumption after a digression;
   - an important new participant who will be followed up ("forward topicality").
4. **It goes after the verb when it has no pragmatic function:**
   - a continuous, predictable participant who is mentioned anyway;
   - a new but minor participant, as in catalogues.
5. **A verb comes first in two cases:**
   - when the verb is the Focus, which is common in running narrative, where the event is the news;
   - when the verb is the Topic:
     - it repeats or follows from the previous clause;
     - or it is a presentative (ἦν, ἦλθε, ἀφικνεῖται, ἐγένετο) that serves as a "dummy topic" for
       introducing a participant. Plain ἀνήρ / γυνή follow such verbs.
6. **Speech verbs introducing direct speech regularly put the verb before the subject** (λέγει ὁ X).
   - An answer is ὁ δὲ εἶπε.
   - A speech is closed with ὁ μὲν ταῦτα ἔλεγε.
7. **μέν … δέ:** contrastive Topics come first and contrastive Foci follow. Predictable material is gapped.
8. **Frequencies are by-products, not norms.** Dik refuses to call any S/O/V order "unmarked" on the
   strength of counts.
   - With στρατεύομαι, subject–verb is the commonest order only because the subject is usually the Topic
     and the verb is usually the Focus.
   - Dover had already concluded that S/O/V statistics yield no syntactic rule.
9. **The One Lexical Argument Constraint** (Du Bois, cited by Dik): natural discourse avoids naming both
   the subject and the object as full noun phrases in one clause.
   - In Du Bois's spoken data under 3% of transitive clauses do.
   - Dik finds such clauses at seams of the narrative, where two storylines meet.
10. **Dover's "preferential" words gravitate to the start of the clause, because they are likely Topic or
    Focus:**
    - interrogatives, negatives, demonstratives, connective adverbs, emphatic pronouns;
    - νῦν / τότε, αὐτός, ἄλλος, πᾶς, πολύς, εἷς.
11. **Mastronarde's local rules:**
    - vocatives come right after the first word or short phrase;
    - unemphatic pronouns (μοι, σε, oblique αὐτοῦ / αὐτῷ / αὐτόν) come second in the colon;
    - demonstratives open the colon;
    - δεῖ precedes its infinitive;
    - the question word comes first;
    - a nominative participle before the verb gives background, after it elaborates;
    - argument–verb is the unmarked order, verb–argument when the verb weighs more;
    - adjunct–argument–verb when both are present;
    - a heavy constituent tends to go late.

## 2. Where our method falls short

- **We calibrated global marginal rates:**
  - subject left out about 48%;
  - a stated subject after the verb about 55%;
  - copula left out 50–60%;
  - vocative start / inside / end.

  Both books treat such rates as by-products. A chapter can hit every rate with individual cards in the
  wrong order, which was ruled out. Examples:
  - generic statements with the subject after the verb, as in Τὰς πόλεις σῴζει ἡ ὁμόνοια (ch. 14, round 1,
    still in the working tree);
  - an object fronted only to put the subject after the verb.
- **Our measures pool unlike contexts.** Speech tags, presentatives, μέν/δέ topics, subordinate clauses and
  plain statements all fall into one subject-position figure. The deck's mix of contexts is not the
  corpus's mix: far more isolated transitive statements. So even the right rate hides the wrong behaviour.
- **The deck breaks the One Lexical Argument Constraint massively.** Here are the 3rd-person clauses with a
  noun object that also have a noun subject:

  | chapters | share | count |
  |---|---|---|
  | ch. 1–10 | 29% | 73 of 256 |
  | ch. 11–16, after round 1 | 39% | 77 of 196 |
  | ch. 17–32, untouched | 84% | 424 of 503 |

  This is the clearest single sign of "sentences made to be complete" rather than snippets of running
  Greek. The corpus figure still has to be measured (step A below).
- **Our omission measure counts some neuter objects as subjects.** The checker picks the nominative in
  Τὸ μάθημα μανθάνει. `deck_exact.py` now also prints a figure that does not count them.

## 2a. Newness and emphasis are simulated inside the card

Being new in the deck says nothing about being new in the text.
- The word order follows the information status that the sentence itself presents.
- Every emphasis made by position has to make sense within the card.

1. **The sentence shows what is given and what is new.**
   - The article presents a referent as identifiable, i.e. given or inferable: τὸ μάθημα is "his lesson".
   - So do αὐτοῦ, a known character's name, and a referent just mentioned in the card.
   - A noun without the article, or with τις, presents something new.
   - The English must agree ("the / his" against "a").
2. **Each card answers an implied question, and its order must fit a context the card makes plausible.**
   - The default context is the story going on: "what happens next?" In it:
     - the event is the news;
     - a continuing subject is left out;
     - the verb carries the focus;
     - definite or predictable complements follow the verb (Ἔλαβε τὸν σάκκον);
     - a new, anarthrous complement may stand before it (Λίθον ἔβαλεν).
3. **A marked position needs a reason inside the card.**
   - A definite constituent put before the verb, or before a stated subject, picks it out against
     alternatives: Τὸ μάθημα μανθάνει ὁ παῖς means it is his lesson, not something else, that the boy
     studies.
   - That reading is right only when the card contains or evokes those alternatives:
     - μέν … δέ;
     - οὐ X ἀλλὰ Y;
     - a second clause;
     - a question being answered;
     - a topic carried over from the card's first clause (… τὴν Δήμητρα οὖν φιλεῖ ὁ αὐτουργός).
   - Otherwise the neutral order is used.
   - When the Greek is marked, the English shows it.
4. **What the verb predicts never takes the focus position.** That covers:
   - objects implied by the verb: τὸ μάθημα μανθάνειν, λόγον λέγειν, τὴν ναῦν κυβερνᾶν;
   - referents just mentioned.
5. **A stated subject comes first as a topic:**
   - at the start of a scene;
   - on a shift (ὁ δέ);
   - in a contrast;
   - in a generic statement.

   It comes after the verb when it is predictable or minor, with a presentative verb (Ἥκει ὁ ἰατρός), or in
   a speech tag. Never front a definite object merely to move the subject after the verb.

## 3. The approach: annotate the information structure, derive the order, calibrate by class

### A. Measure the corpus by class, not overall (new `tools/phase3/style4.py`)

The source is the Attic corpus already in `corpus/`, with Athenaze (private) as a cross-check. Automatic
proxies:

- **givenness:** the subject's lemma occurs in the previous one or two sentences;
- **topic marking:** subject + δέ / μέν, and ὁ δέ / ὁ μέν;
- **verb class:**
  - a speech verb before direct speech;
  - presentational: εἰμί existential, γίγνομαι, ἥκω, ἔρχομαι, ἀφικνέομαι, πάρειμι, φαίνομαι;
  - any other verb;
- **clause:** main or subordinate;
- **objects:** whether a noun object is present (the One Lexical Argument Constraint share);
- **Dover's words:** where they stand.

The output is tables, for each class:
- how often the subject is left out, stated before the verb, or stated after it;
- how often the subject and the object are both nouns.

A hand-checked sample of about 150 clauses estimates the proxies' error, as the treebank calibration did
before.

### B. Annotate every card's implied context (a reviewable table: `project/review/infostructure_chNN.tsv`)

Fields per card:
- **topic:** continuing (subject left out) / shift / contrast / resumed / new major participant / generic /
  presentative / none;
- **focus:** the new item / the verb / an object / an adverbial / complex;
- **speech tag:** yes or no.

Each card is judged as an utterance in its chapter's story, following §2a. The deck item does not decide the
annotation. The proposer fills in defaults from the sentence's own signals:

- **Article, τις, αὐτοῦ and the English "the / a"** give each noun's simulated status: given, inferable or
  new.
- **The default context is "what happens next?"**:
  - a continuing subject is left out;
  - the focus falls on the verb, or on a new (anarthrous) complement;
  - given or predictable complements follow the verb.
- **Generic statements and scene openings** put the subject first, as the topic (Ὁ πένης οὐδὲν ἔχει).
- **Presentative verbs:** verb first, then the participant (Ἥκει ὁ ἰατρός).
- **Speech verb + direct speech:** verb before subject; ὁ δὲ εἶπε / ἔφη for answers.
- **μέν … δέ:** two-clause cards only. Contrastive topics first, contrastive foci next, gapping where natural.
  This keeps the rule that connectives come only with the sentence they connect.
- **Marked orders** (a definite constituent focused or contrasted) are chosen only where the card supplies
  the contrast, and the English then shows it.

### C. Derive the order from the annotation

- Apply SETTING – TOPIC – FOCUS – VERB – REST, plus Mastronarde's local rules.
- Mark every card whose current order differs from the one derived.
- Flag these automatically for review:
  - **A definite object or dative first, with the stated subject after the verb.** This reads as a contrast.
    - There are 21 such cards in ch. 1–16; most come from my own "after" moves in the snippet pass (Τὸν σῖτον
      φέρει ὁ ἡμίονος, Τὸν δῆμον ἔπειθεν ὁ ῥήτωρ).
    - A few are justified by the card: 160 τὴν Δήμητρα οὖν φιλεῖ, 220 τὸν δὲ κλῆρον, 1649 Τῷ δεκάτῳ ἔτει.
  - **A definite object before the verb with no contrast in the card.** About 63 in ch. 1–16, reviewed one
    by one; Τὸ μάθημα μανθάνει is one of them.
  - **A complement predictable from the verb** in the focus position.
  - **A generic statement** with its subject after the verb.
  - **Greek and English disagreeing** on definiteness or emphasis.
- Change only where the derived order reads better. Deviations are allowed with a note, e.g. for a
  hyperbaton or a set phrase.

### D. Keep the One Lexical Argument Constraint

- A card names both subject and object as nouns only when:
  - the subject is a topic shift or a new major participant;
  - and the object is the focus or the item.
- Otherwise the subject is left out, or the object is a pronoun or left implicit.
- Aim at the corpus share measured in A.

### E. Calibrate by class

- **Compare by class.** For each class in A, compare the deck's distribution from B and C with the corpus's.
  Example: of given, non-contrastive stated subjects, how many follow the verb.
- **Compare the mix.** How many cards are continuing / shift / generic …? The mix is what produces the
  global omission rate.
- **Fix cards, not counts.** A deviation sends us back to the cards of that class, never to count-balancing.
- **Keep the old global figures only as a final check**, with a tolerance:
  - subject left out about 48%;
  - stated subject after the verb about 55%;
  - copula left out 50–60%.

## 4. What happens to the work already done

- **ch. 1–10 and 24 (pilot, committed) and ch. 4–9 (committed):**
  - Annotate and audit.
  - Most subject omissions are continuing-topic cases and stand.
  - Review the 258 ch. 1–16 cards with a stated subject after the verb.
  - First the 21 cards with a fronted definite object and the subject after the verb, then the other flags in
    §3C.
  - Generic statements get the subject first.
  - Cut the cards that have both a noun subject and a noun object.
- **ch. 11–16 round 1 (applied, uncommitted):** a working draft. Re-run it through B–E; most omissions
  stay.
- **ch. 17–32:** the new method from the start. The One Lexical Argument Constraint is the main issue
  there.

Unchanged:
- one new item per card;
- GUIDs;
- book-clause checks;
- no lone connectives;
- copula omission;
- vocative position, now read as "after the first word or phrase".

## 5. Steps

1. `style4.py`: corpus tables by class, with the validation sample. Report the tables.
2. Annotation proposer: defaults per card from the item type, verb class and previous cards; TSV for review.
3. Order generator from the annotations, reusing `mkops.py`, accents and hints. Lists the cards whose
   order differs.
4. Audit ch. 1–16, then rewrite ch. 17–32. Checker, GUID, regress and book checks after each batch.
5. Deck-wide comparison by class; rebuild; audio cost.

## 6. Results (applied 2026-11-24)

### What was done

- **ch. 1–10 and 24** (the snippet pilot) and **ch. 4–9** (the snippet pass): audited by these rules.
- **ch. 11–16:** the snippet draft, then an audit.
- **ch. 17–23 and 25–32:** decided card by card.
- **The record of each card's choice** is in the decision files `work/phase3/infostructure/dec_*.txt`.
  - The choices are: out, after, before, nocop, or a hand-written sentence with its reason.
  - The choices are made over `is_propose.py`'s options and flags, and applied as `table_*.tsv` with
    `apply.sh`.
  - The decision files stand in for the planned `infostructure_chNN.tsv` annotation tables.
- **Cards changed** since the snippet pilot (snippet pass of ch. 4–16 plus this pass): 1,411 of 3,657.

  | ch. 1–10 | ch. 11–16 | ch. 17–23 | ch. 24 | ch. 25–32 |
  |---|---|---|---|---|
  | 343 | 335 | 413 | 5 | 315 |

  Every card kept its GUID and its new item. The checker reports 0 problems.

### How the cards were decided (§2a)

- **Subject left out** when it continues from the context or is incidental. This is usually the case when
  the card's new item is the verb (a tense, a form) or a complement.
- **Verb first:**
  - events and arrivals (Ἐν τῷ ἀβάτῳ καθεύδουσιν οἱ ἱκέται);
  - presentatives, with a new participant after the verb (Ἐγένετο καρτερὰ μάχη; Νυκτὸς φαίνονται πολλοὶ
    ἀστέρες);
  - resultative perfects (Γέγραπται ἡ ἐπιστολή);
  - wishes (Σώσειεν ὁ θεὸς τὴν πόλιν);
  - tags before direct speech (Ἔφη ὁ γέρων …).
- **Subject first:**
  - in generic statements (Ἡ ὁμόνοια τὰς πόλεις σῴζει);
  - for a subject the card introduces as its topic;
  - in contrasts. Where two clauses contrast two subjects, μέν … δέ was added (Ὁ μὲν δεσπότης βαδίζει, ὁ δὲ
    Ξανθίας ἀκολουθεῖ).
- **Object first, subject after the verb** (O…V…S): none left in the deck.
- **A definite object never opens a subjectless clause** unless the card gives the reason:
  - πᾶς or a demonstrative;
  - a gnome (Τὸν θάνατον οὐδεὶς ἐκφεύγει);
  - a set phrase;
  - a topic carried over (Μόλις τὸν σάκκον ἐκφέρει· τοσοῦτος γάρ ἐστιν).

  Τὸ μάθημα μανθάνει is now Μανθάνει τὸ μάθημα.
- **Vocatives** come after the first word or phrase (Ποῖ, ὦ ξένε, πορεύσῃ αὔριον;), or at the start of
  invocations (Ὦ θεοί, κλύετέ μου).
- **Unemphatic pronoun** in second place (Συλλαμβάνει αὐτῇ ἡ δούλη).
- **Copula** left out in evaluative and gnomic predications, kept in neutral physical descriptions.
- **Connective particles** only with the utterance they connect; dialogue particles got the line they answer.
- **ἐγώ / σύ / ἡμεῖς** where the card contrasts persons (Ἡ κόρη ἣν σὺ φιλεῖς οὐ φιλεῖ σε).
- **Book text is a copyright question only**.
  - A card is never left in a worse order because its best version shares words with the books.
  - Every book-related refusal of every pass, ch. 1–32, was checked: the first word-order pass, the snippet
    pilot, the snippet pass and this pass. The first word-order pass dropped no proposal silently: each was
    applied, rejected by hand or rewritten by hand, and its book rejections are recorded in `dec_*.txt`.
  - 23 cards now have the order those refusals had set aside (`table_book_restore.tsv`, `table_book_restore2.tsv`).
  - In two of them (446, 1512), the better verb-first order alone would have been a 4-word book clause. Naming the
    subject after the verb sets the card apart, and also says who acts, since the card before is about someone
    else.
  - The other refused orders were weighed against the card as it stands and its neighbours, and kept where the
    card is as good or better:
    - a topic coming back or shifting (36, 250, 282);
    - a new participant who must be named (382, 550, 662, 729, 1129, 2886, 2928);
    - contrastive topics (455, 578);
    - subject–object–verb with a known object (381);
    - adjunct–verb (186, 190, 446's old form);
    - card 531, whose current order is as good as the refused one.
  - Card 686 took back its original subject, because putting the verb first would have formed the ch. 11 set
    phrase κόπτει τὴν θύραν.
  - Where a card would really reproduce a book sentence, the remedy is a word changed or added. `check_table.py`
    now fails only on a 4+-word clause verbatim in the books, and says so.
  - Seven composed cards contain a 4-word clause the books also have:
    - set phrases the deck teaches (ὑπὸ τὸ ζυγόν, τίνα σε δεῖ καλεῖν, δός μοι τὴν χεῖρα, τί πάσχει);
    - three everyday clauses (βαδίζει πρὸς τὸν ἀγρόν, ὁ δὲ δοῦλος καθεύδει, ποῦ ἐστιν ὁ κύων).

    None is a copyright issue.
  - Composed cards sharing a run of 4+ words with the books (`tools/phase1/bookoverlap.py`, for information):
    133 before the snippet pass, 110 now.

### The deck against the corpus

`tools/phase3/style4.py` measures every side with the same analyser:
- sentences of 3–12 words;
- main clauses with an ordinary verb (not a speech or presentative verb).

| measure | ch. 1–10 | ch. 11–16 | ch. 17–32 | Attic prose | Athenaze |
|---|---|---|---|---|---|
| 3rd-person clauses | 123 | 220 | 747 | 2,465 | 232 |
| subject left out (strict) | 63% | 64% | 67% | 70% | 63% |
| unmarked art. + noun subject after the verb | 37% of 19 | 47% of 45 | 44% of 117 | 48% of 40 (new) / 43% of 21 (given) | 38% / 50% |
| O…V…S (definite object first, subject after the verb) | 0 | 0 | 0 | 0 | 0 |
| definite object opening a subjectless clause | 6% | 0% | 4% | 3% | 5% |
| noun object with a noun subject | 21% | 24% | 15% | 8% | 11% |
| definite object before the verb | 50% | 28% | 26% | 43% | 52% |

Whole deck (`work/phase3/snippet/deck_exact.py`):

| measure | deck | target |
|---|---|---|
| present-tense predications without the copula | 55% of 264 | 50–60% |
| vocative start / inside / end | 11 / 24 / 65% | Attic 11–28 / 19–27 / 53–68% |

The copula measure counts only present-tense predications, since a past ἦν cannot be left out.

### Explained deviations

- **Noun subject plus noun object, 15–24%** (corpus 8–11%).
  - Many cards introduce a subject noun as the new item, or state a generic truth. There the subject is the
    topic and has to be named.
  - Continuing subjects with a noun object were left out wherever the card allowed it.
- **Definite objects before the verb, 26–28% in ch. 11–32** (corpus 43–52%).
  - In many cards the new item is the verb, so the verb carries the focus and the given object follows it.
  - Where a subject or a setting precedes, object–verb stays.
  - Forcing object–verb would put a predictable object in the focus slot, which was ruled out.
- **Presentative verbs:** the deck puts the subject after the verb in 60–100% (5–15 clauses).
  - Attic has 17–22%, but in only 9–18 clauses, and copular γίγνομαι dominates there.
  - Dik's presentatives (ἦν, ἦλθε, ἀφικνεῖται) put a new participant after the verb.
- **Speech verbs:** with direct speech the deck is verb-first throughout. The subject-first speech clauses have
  infinitive complements (Ὁ στρατηγὸς ἔφη ἕτοιμος εἶναι), or introduce the speaker as the card's new word.
- **1st/2nd-person pronoun subjects, 5%** (Attic about 9%). They were added only where the card contrasts
  persons. Most 1st/2nd-person cards are single short utterances with nothing to contrast.

### Not done from §3

- **The hand-checked sample of 150 corpus clauses.** The "given" proxy (the subject's lemma in the two
  sentences before) separates little: 43% after the verb when given, 48% when new. So the pass relied on
  judgment card by card, with the class tables as the check.
- **Separate `infostructure_chNN.tsv` tables.** The decision files record the same choices.


## 7. The paradigm cards (2026-11-25)

The 1,078 cards of the paradigm completion (`PARADIGM_COVERAGE.md`) had been written from a few frames. Measured
with the same tools, their order did not meet §2a: objects first with no reason in the card, subjects first by
default, vocatives opening the card. They were reordered by the rules of §2a and §6
(`work/phase3/infostructure/newcards.py` proposes, `newcards_apply.py` applies; every proposal was read).

- **Subject:**
  - kept first when it holds the card's new item, in generic statements and in speech tags;
  - left out when it continues from the cards before or stands beside a noun object;
  - otherwise placed after the verb.

  3rd-person imperatives and the dual cards keep their subject.
- **Definite object or dative before the verb** with no stated subject before it: moved after the verb. An
  anarthrous complement stays before the verb (Σῖτον παρέχει τῇ κόρῃ). The rule leaves alone:
  - πᾶς and demonstratives;
  - μέν / δέ;
  - relative clauses;
  - prepositional settings.
- **Vocative:**
  - after the first word or phrase (Ἡ κόρη, ὦ δέσποινα, ἐν τῷ ἀγρῷ ἐστιν; Διὰ τί, ὦ κακὲ δοῦλε, οὐ πονεῖς;);
  - at the end of a short utterance (Σίγα, ὦ βοῶν; Χαίρετε, ὦ φίλοι);
  - first only in invocations of gods and prayers.
- 294 cards changed. Every card kept its new item and its GUID. Checker 0 problems. No clause of 4+ words is
  verbatim in the books (`check_table.py`, all 1,078 cards).

| measure (`style4.py`, new cards) | before | after | old cards | Attic prose |
|---|---|---|---|---|
| art. + noun subject after the verb | 20% of 35 | 50% of 32 | 49% | 43–48% |
| definite object before the verb | 76% | 43% | 31% | 43–52% |
| definite object opening a subjectless clause | 19% | 6% (πᾶς, demonstratives) | 4% | 2–4% |
| noun object with a noun subject | 20% | 19% | 16% | 8–11% |
| vocative start / inside / end | 63 / 1 / 36% | 4 / 11 / 85% | 11 / 26 / 62% | 11–28 / 19–27 / 53–68% |

Explained deviations:
- **Vocatives at the end, 85%.** Most of these cards are a short command or question plus the address
  (Παύεσθε, ὦ μαχόμενοι).
- **Noun subject plus noun object, 19%,** as in the rest of the deck (§6): the subject is named where it holds the
  card's item or is the topic of a generic statement.
