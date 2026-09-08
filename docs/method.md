# SwitchF1 boundary v2: complete text-only specification

## Inputs and claim

For each independent utterance/stream, supply two ordered token sequences:

$$
R=((r_1,\ell^R_1),\ldots,(r_n,\ell^R_n)),\qquad
H=((h_1,\ell^H_1),\ldots,(h_m,\ell^H_m)).
$$

Each token contains text and an explicit language ID. IDs are fixed semantic names, preferably BCP-47 tags under one documented granularity policy. Do not permutation-map language names to maximize scores. Any number of languages is supported. Tokenization and contextual language annotation are benchmark inputs, not inferred from the model ranking.

Primary claim: preservation of directed language-switch boundaries at corresponding aligned positions in recognized text. The default `boundary` mode uses specification `switchf1-boundary-v2`. Exact local word recognition is not required, but lexical edit alignment still determines positional correspondence. For language-identification experiments on identical text tokens, alignment is trivial. `boundary_exact` preserves the exact-position v1 criterion (`switchf1-boundary-v1`); `anchored` additionally requires correctly recognized local words at those exact positions (`ase-f1-v1`). Reference words and language labels must be independently checked against the speech when making an ASR switching claim; the algorithm cannot authenticate the audio provenance of a transcript.

## Normalization and alignment

Normalize token text with Unicode NFC and lowercase. Preserve diacritics, Tamil vowel/virama marks, every script, real repetitions, digits and symbols. No transliteration, spelling dictionary, repetition removal or model-specific rewriting occurs. Tokenization must treat punctuation consistently before evaluation; explicitly neutral punctuation can be labeled `null`.

Compute ordinary unit-cost Levenshtein alignment on normalized token **text only**. An equal token costs 0; substitution, insertion or deletion costs 1. Each token occurs in exactly one alignment column. Backtracking ties prefer diagonal, then deletion, then insertion. Language labels and resulting F1 do not influence alignment.

Let $a_R(i)$ and $a_H(j)$ be the alignment columns of reference and hypothesis tokens. Different equally optimal edit alignments can imply different boundary locations in repeated text. The fixed tie rule makes this deterministic; it does not solve ambiguity. Alignment costs O(nm) time and memory, so split long documents at independent utterance boundaries.

## Events

Ignore explicitly neutral (`lang=null`) tokens when finding successive language-bearing tokens. If successive resolved tokens at indices $i,k$ have different languages, define an event

$$
e_R=(a_R(i),a_R(k),\ell^R_i,\ell^R_k,\nu(r_i),\nu(r_k)).
$$

Construct hypothesis events identically. The first two fields identify the aligned pair of boundary anchors, the next two give the ordered language transition, and the last two give normalized lexical anchors.

## Primary matching: a supported boundary interval

For a reference event from language A to B, let its endpoint alignment columns
be L and U, with L < U. Let q(c) be the hypothesis token in alignment column c,
or a gap if no hypothesis token is present.

A hypothesis event with endpoint columns l and u is eligible exactly when:

$$
q(L)\ne\varnothing,\quad q(U)\ne\varnothing,\quad
\ell(q(L))=A,\quad\ell(q(U))=B,
$$
$$
L\le l<u\le U,\qquad \operatorname{direction}(e_H)=(A,B).
$$

Thus both ends of the reference boundary must be supported by aligned hypothesis
tokens of the correct languages, and a real directed hypothesis event must occur
inside that boundary interval. Exact lexical equality is not required. Because
the reference endpoints are successive language-bearing tokens, the interval has
no other language-bearing reference token inside it. It can contain insertion
columns and explicitly neutral reference tokens.

This credits extra A-language words before the transition, extra B-language words
after it, or both, if the directed transition is preserved. It does **not** search
arbitrarily far through other language-bearing reference words. There is no
word-distance threshold to tune: interval limits come from the fixed edit
alignment. Insertion length affects WER, not eligibility by itself.

Count every hypothesis event before matching. Process reference events in text
order and match the first eligible unused hypothesis event in each interval.
Reference intervals have disjoint interiors, so no hypothesis event can be an
eligible candidate for two reference intervals; earliest-event tie-breaking only
chooses among events within one interval. This realizes one-to-one matching
without optimizing text alignment to improve F1. Extra forward/reverse switches
remain FP, including those wholly inside the insertion interval. If the sequence
is A → C → B and contains no direct A → B event, it receives no A → B credit.
If either endpoint is deleted or assigned the wrong language, there is no match.

The optional `boundary_exact` mode requires equality of both event columns and
the ordered language labels. Optional `anchored` additionally requires equality
of the normalized words. These reproduce v1 and ASE-F1 semantics respectively.
An unmatched reference event is FN; an unmatched predicted event is FP.

Returned event traces retain actual token indices and alignment positions.
`matches_across_insertions` counts matches whose endpoint positions differ under
the interval rule; it also includes displacement across explicitly neutral tokens.
Report this alongside exact-boundary F1 to show sensitivity to the relaxation.
See [worked examples](alignment.md).

## Unknowns, neutrality and speaker scope

`null` means a confidently designated neutral token. It is not a missing annotation. Freeze which fillers, numbers, names, punctuation and borrowings are neutral. Many such tokens are language-bearing in context and should not automatically be neutralized.

Reference labels `und`, `mul` and `ambiguous` fail validation: adjudicate them, split a mixed token according to a predeclared tokenization policy, or define an exclusion region before running the scorer. Excluded regions must be split into independent records so that no artificial event bridges them, and excluded support must be reported externally. Do not exclude difficult regions after seeing model errors.

Hypothesis `und`/`mul`/`ambiguous` labels are also rejected. Silently dropping them could remove false events and improve F1 through abstention. Resolve labels with a fixed, validated independent annotation/LID process before headline scoring. Neutral `null` is allowed only under a predeclared shared policy, never as an arbitrary abstention class. Supply all requested utterances; a benchmark adapter must validate ID coverage. Experiments on abstention itself require a separate coverage-aware evaluation, not this fully labeled protocol.

One record represents one independent evaluated text stream. If the intended claim is **within-speaker** code-switching, split speaker turns or otherwise provide separate speaker streams before evaluation. A language change between two speakers is not evidence that either individual code-switched. No cross-record events are created.

## Aggregation and zero denominators

Let M be the matched event set for the corpus, E_R all reference events and E_H all predicted events:

$$
TP=|M|,\quad FP=|E_H|-|M|,\quad FN=|E_R|-|M|.
$$

$$
P=TP/(TP+FP),\quad R=TP/(TP+FN),\quad F1=2TP/(2TP+FP+FN).
$$

Pool counts across all utterances, including no-switch references. Precision is undefined (`null`) if there are no predicted events; recall is undefined if there are no reference events. F1 is 0 if any events exist but none match. It is undefined if neither side has events. Never award perfect switching performance to an all-no-switch corpus.

Also report each language direction separately, language-presence exact rate, the number of unknown hypothesis tokens, and the proportion of no-switch-reference utterances with a predicted switch. Language-presence rate is only a coverage diagnostic: it does not verify each word's language.

The package additionally computes **aligned token-language** precision/recall/F1. For each named language L and each edit-alignment column, a correct L/L pair adds TP(L), a predicted L with a different or absent reference label adds FP(L), and a reference L with a different or absent prediction adds FN(L). Neutral/neutral columns add no counts. Pool each language's counts, report their micro F1, and average the per-language F1 values for macro F1 over languages present on either side. This catches entirely wrong monolingual labeling even when switch F1 is undefined. With ASR insertions/deletions this remains alignment-dependent; on identical token sequences it evaluates ordinary token-language predictions. Word substitutions retaining correct language labels can receive token-language credit even though they fail ASE lexical anchoring.

## Known limits

- Reference LID errors directly corrupt the score. Script-based labeling is only a restricted proxy.
- The primary mode permits insertion displacement only inside a supported reference boundary interval. It still rejects deleted/mislabeled reference endpoints; it does not solve all ASR alignment failures. Exact-boundary and anchored modes retain stricter positional requirements. Lexical variants can affect alignment in every mode.
- A long hallucination using the expected languages can preserve the supported transition and receive boundary credit. This is deliberate separation of switching from transcription fidelity, not evidence that the hallucinated words were spoken. Always report WER/CER and hallucination diagnostics.
- The interval rule was selected from semantic counterexamples and needs independent bilingual human validation. Robustness tests do not establish acoustic or sociolinguistic construct validity.
- Repeated identical passages can have multiple optimal alignments. Fixed tie-breaking is reproducible but cannot identify the acoustically correct occurrence. A long same-language hallucination can leave boundary F1 perfect; WER/CER must accompany it.
- An error inside a long monolingual span may leave every boundary intact. WER/CER and token-LID metrics remain necessary.
- No timestamps means no acoustic localization or language-duration accuracy claim.
- A transcript metric cannot establish comprehension of intent, emotional nuance or social code-switch norms.
- Unit tests establish implementation behavior; they do not establish correlation with human judgments or statistical generalization across languages.
