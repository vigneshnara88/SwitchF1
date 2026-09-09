# Alignment, omissions and multiple switches: boundary v3

The score asks whether **the corresponding directed language changes survive in
recognized text**. It does not compare raw word numbers or require the words
beside a switch to be transcribed exactly.

## Follow a simple omission

Every word below has a declared language. `ennaku` is Tamil written in Latin
letters; the evaluator consumes that explicit label.

```text
Reference:  hello/en my/en name/en is/en sam/en | ennaku/ta
Output:     hello/en my/en name/en   —     —   | ennaku/ta
```

V2 required aligned output support for `sam` and `ennaku`, so it rejected the
switch. V3 moves the left support back to `name`, the nearest surviving word in
the same original English stretch. It finds one English → Tamil event between
`name` and `ennaku`: TP=1, FP=0, FN=0, F1=100%. WER counts two deletions.

With `hello/en ennaku/ta name/en sam/en`, ordinary lexical alignment places the
Tamil token against an English reference word and deletes the final Tamil token.
Neither predicted transition preserves the supported reference switch:
TP=0, FP=2, FN=1, F1=0%. Merely containing both languages is not sufficient.

## Follow several switches

```text
Reference: hello/en friend/en | ennaku/ta venum/ta | coffee/en today/en
Output:    hello/en    —      |     —     venum/ta |     —     today/en
```

Each original reference language stretch has a survivor. Match English → Tamil
and Tamil → English separately: TP=2, FP=0, FN=0. The middle `venum` token supports
two **different** transitions; no predicted event is reused.

- Delete all Tamil words: no predicted switches, TP=0, FP=0, FN=2.
- Omit the final English stretch: TP=1, FP=0, FN=1, F1=66.7%.
- Preserve the reference and add a Tamil tail: TP=2, FP=1, FN=0, F1=80%.
- Insert a Tamil → English detour before the real Tamil stretch: TP=2, FP=2,
  FN=0, F1=66.7%.
- Repeat this entire passage three times: six predicted events, only two matches;
  TP=2, FP=4, FN=0, F1=50%.

A completely absent language run cannot be skipped to create a replacement
reference event. With reference `a/en b/ta c/en d/ta e/en f/ta` and output
`a/en b/ta e/en f/ta`, only the outer two events match. The middle predicted
Tamil → English event spans three original reference boundaries; the conservative
rule cannot assign it to one locally. TP=2, FP=1, FN=3, F1=50%. A collapsed
language-sequence score would give a different, less location-sensitive answer.

## The matching rule, in order

1. Align token text using unit-cost Levenshtein distance, NFC and lowercase.
   Backtracking ties prefer diagonal, deletion, insertion. Language labels do
   not choose or optimize the alignment.
2. Count every directed language change on both sides, ignoring explicitly
   neutral tokens under a fixed annotation policy.
3. For each original reference boundary, find the nearest surviving reference
   word backwards in the source language run and forwards in the destination
   run. Skip deleted words; never cross another reference language run.
4. Check the output languages aligned to these two selected words. Both must be
   correct. Stop at a wrong surviving label; do not search farther to find a
   favorable match.
5. Match the earliest unused hypothesis event of the same direction entirely
   between those support columns. All other hypothesis events remain FP; all
   unmatched original reference events remain FN.

Support intervals have disjoint interiors: a run's first surviving token supports
its incoming switch and its last supports its outgoing switch. Those two tokens
occur in that order, or are the same token. Thus an event cannot match two
reference boundaries. See [the formulas](method.md).

## Hallucinations and repetitions

A 100-word English insertion before a supported English → Tamil switch can leave
F1 perfect. So can repeated Tamil words within the Tamil stretch. These add word
errors, but do not invent language transitions. No raw offset cutoff or repeat
stripping is used.

Invented `en → ta → en → ta` inside one supported English → Tamil interval yields
one TP and two FP. Invented `en → fr → ta` has no direct English → Tamil event:
zero TP, two FP and one FN. Matching direction as well as location prevents
credit for that third-language detour.

## Known failures: text cannot settle every case

The executable audit includes **two cases where a reasonable switch-preservation
judgment differs from the conservative lexical-alignment result**:

- Reference `a/en b/en c/ta d/ta`; output `a/en noise/en ×128 d/ta`. Some `noise`
  tokens align as substitutions for omitted reference words, including `c/ta`.
  V3 sees surviving English support where Tamil was required and rejects the
  switch. Broad English → Tamil structure survives, but this alignment cannot
  establish its local correspondence.
- Changed neutral punctuation can align to a deleted language-bearing word,
  likewise blocking support. Freeze punctuation tokenization; do not change it
  separately for individual systems to improve their scores.

These limitations are retained in tests and reported openly. Allowing any
correct-language span anywhere in the output would fix these examples at the
cost of falsely rewarding misplaced switches. Choosing the edit alignment that
maximizes F1 would also bias the metric toward agreement.

Repeated identical words/passages admit ambiguous alignments. The deterministic
rule is reproducible, but cannot identify which repetition was actually spoken.
An invented passage in the expected languages may earn switch credit even if
all its words are wrong. That is why F1 must accompany WER/CER and raw-output
hallucination diagnostics.

For **actual spoken switches**, use audio-verified reference transcripts and
language labels, independently label the output, and split speaker streams when
the claim concerns switching within one speaker. No timestamps means no claim
about acoustic switch timing, internal language detection, or understanding why
the speaker switched. See the [scenario audit](scenario_audit.md) and
[human validation plan](validation.md).

## Longer text and possible timing support

Longer individual transcripts can contain more competing repeated passages and
accumulated insertion/deletion errors. Consequently, an aligned match can be less
informative about where a switch actually happened in speech. This is a potential
alignment limitation, not a proven rule that every longer transcript scores less
accurately. **SwitchF1 remains indicative, not ground truth.**

Reliable word-level timestamps on both sides could help distinguish occurrences
by audio position in a validated temporal evaluator. The current scorer does not
use them; inaccurate timestamps or coarse segment timing would not establish exact
switch locations. See the [full caveat](review.md#long-transcripts-timing-and-how-to-interpret-the-score),
including how segmentation can omit cross-record switches.

## Reproduce earlier definitions

- `boundary`: current v3, within-run deletion and insertion tolerance.
- `boundary_v2`: original endpoint support, insertion tolerance only;
  [archived alignment](alignment_v2.md), [archived specification](method_v2.md).
- `boundary_exact`: v1, exact two alignment columns, substitutions allowed.
- `anchored`: exact columns and exact normalized local words.

Version and mode must accompany every result. WER/CER normalization and
aggregation are separate choices and do not change when revising SwitchF1.
