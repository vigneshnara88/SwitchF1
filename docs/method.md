# ASE-F1 v1: complete text-only specification

## Inputs and claim

For each independent utterance/stream, supply two ordered token sequences:

\[
R=((r_1,\ell^R_1),\ldots,(r_n,\ell^R_n)),\qquad
H=((h_1,\ell^H_1),\ldots,(h_m,\ell^H_m)).
\]

Each token contains text and an explicit language ID. IDs are fixed semantic names, preferably BCP-47 tags under one documented granularity policy. Do not permutation-map language names to maximize scores. Any number of languages is supported. Tokenization and contextual language annotation are benchmark inputs, not inferred from the model ranking.

Primary claim: preservation of directed, locally correct switches in recognized text. This combines local lexical correctness with language structure. For pure language-identification experiments on identical text tokens, alignment is trivial and labels determine correctness. With ASR substitutions, ASE-F1 intentionally adds a lexical requirement. Use the companion boundary mode to inspect that distinction.

## Normalization and alignment

Normalize token text with Unicode NFC and lowercase. Preserve diacritics, Tamil vowel/virama marks, every script, real repetitions, digits and symbols. No transliteration, spelling dictionary, repetition removal or model-specific rewriting occurs. Tokenization must treat punctuation consistently before evaluation; explicitly neutral punctuation can be labeled `null`.

Compute ordinary unit-cost Levenshtein alignment on normalized token **text only**. An equal token costs 0; substitution, insertion or deletion costs 1. Each token occurs in exactly one alignment column. Backtracking ties prefer diagonal, then deletion, then insertion. Language labels and resulting F1 do not influence alignment.

Let \(a_R(i)\) and \(a_H(j)\) be the alignment columns of reference and hypothesis tokens. Different equally optimal edit alignments can imply different boundary locations in repeated text. The fixed tie rule makes this deterministic; it does not solve ambiguity. Alignment costs O(nm) time and memory, so split long documents at independent utterance boundaries.

## Events

Ignore explicitly neutral (`lang=null`) tokens when finding successive language-bearing tokens. If successive resolved tokens at indices \(i,k\) have different languages, define an event

\[
e_R=(a_R(i),a_R(k),\ell^R_i,\ell^R_k,\nu(r_i),\nu(r_k)).
\]

Construct hypothesis events identically. The first two fields identify the aligned pair of boundary anchors, the next two give the ordered language transition, and the last two give normalized lexical anchors.

A primary-mode match requires equality of **all six fields**. Therefore:

1. Both sides are aligned to the same reference boundary anchors.
2. The language change has the correct origin and destination.
3. Both local words are recognized correctly under the fixed normalization.

Event positions are unique within an ordered token sequence, so exact equality creates a one-to-one matching without a greedy search. The same reference event cannot be credited multiple times. An unmatched reference event is FN; an unmatched predicted event is FP. A wrong event can contribute both one FP and one FN.

In `boundary` diagnostic mode, compare only the first four fields. Substituted words with correct aligned language labels may then match. This is a different explicitly named metric.

## Unknowns, neutrality and speaker scope

`null` means a confidently designated neutral token. It is not a missing annotation. Freeze which fillers, numbers, names, punctuation and borrowings are neutral. Many such tokens are language-bearing in context and should not automatically be neutralized.

Reference labels `und`, `mul` and `ambiguous` fail validation: adjudicate them, split a mixed token according to a predeclared tokenization policy, or define an exclusion region before running the scorer. Excluded regions must be split into independent records so that no artificial event bridges them, and excluded support must be reported externally. Do not exclude difficult regions after seeing model errors.

Hypothesis `und`/`mul`/`ambiguous` tokens break the resolved-language sequence and are counted as unknowns. The scorer does not bridge them into apparently valid events. Resulting missed reference switches remain FN. Supply all requested utterances and inspect unknown counts; a benchmark adapter must validate ID coverage.

One record represents one independent evaluated text stream. If the intended claim is **within-speaker** code-switching, split speaker turns or otherwise provide separate speaker streams before evaluation. A language change between two speakers is not evidence that either individual code-switched. No cross-record events are created.

## Aggregation and zero denominators

Let M be the matched event set for the corpus, E_R all reference events and E_H all predicted events:

\[
TP=|M|,\quad FP=|E_H|-|M|,\quad FN=|E_R|-|M|.
\]

\[
P=TP/(TP+FP),\quad R=TP/(TP+FN),\quad F1=2TP/(2TP+FP+FN).
\]

Pool counts across all utterances, including no-switch references. Precision is undefined (`null`) if there are no predicted events; recall is undefined if there are no reference events. F1 is 0 if any events exist but none match. It is undefined if neither side has events. Never award perfect switching performance to an all-no-switch corpus.

Also report each language direction separately, language-presence exact rate, the number of unknown hypothesis tokens, and the proportion of no-switch-reference utterances with a predicted switch. Language-presence rate is only a coverage diagnostic: it does not verify each word's language.

## Known limits

- Reference LID errors directly corrupt the score. Script-based labeling is only a restricted proxy.
- Exact anchor matching can reject linguistically acceptable synonyms, transliteration variants, spelling variants and boundary-adjacent insertions/deletions. Freeze permitted conventions; do not tune exceptions on test outputs.
- An error inside a long monolingual span may leave every boundary intact. WER/CER and token-LID metrics remain necessary.
- No timestamps means no acoustic localization or language-duration accuracy claim.
- A transcript metric cannot establish comprehension of intent, emotional nuance or social code-switch norms.
- Unit tests establish implementation behavior; they do not establish correlation with human judgments or statistical generalization across languages.
