# Validation plan and release status

Release 0.4.0 provides a specified algorithm, package, examples and semantic regression tests. It is an experimental method. No multi-language human-validation study or peer-reviewed novelty claim is included.

## Required checks before external performance claims

1. **Gold labels:** Have two bilingual annotators independently check a fixed, model-blinded reference sample against the audio, including the actual spoken words, speaker turns and language labels. A transcript copied from an ASR model is not sufficient ground truth. Independently annotate the hypothesis text; do not assign gold labels to predicted words. Resolve borrowing, named-entity, filler, mixed-token and ambiguous cases under a written policy. Keep hypothesis labels independent of reference labels and model identity.
2. **Human construct validity:** Ask reviewers whether each proposed transcript switch preserves the language direction and location, then separately whether its local words are correct. Include long inserted prefixes, boundary-adjacent insertions and repeated passages. Compare v3 boundary F1, insertion-only v2 and exact-boundary F1 with switch-preservation judgments, and anchored F1 with local-transcription judgments. Specifically include correct-language insertions, wrong-language detours, displaced boundaries, deleted endpoint words, copied passages and genuinely spoken repetitions. The primary interval rule has not yet been independently validated against these human judgments. Use a held-out portion to assess correlation, rather than selecting rules and demonstrating agreement on the same examples.
3. **Language transfer:** Include at least one different-script pair, one shared-script pair (e.g. English-French), a pair without English, and three-language utterances. Do not infer broad validity from Tamil-English alone.
4. **Coverage:** Include monolingual controls, short utterances, genuine repetitions, hallucinated language insertions, entire-language deletions, ASR word errors next to switches, and Romanized text. Report excluded ambiguous regions and annotation agreement.
5. **Uncertainty:** Resample paired recordings/speakers and pool event counts inside each sample. Report percentile confidence intervals and separate variation across model training seeds. Repeated clips from the same speaker are not independent evidence.

## What the tests establish

The 49 test methods cover correct switches with wrong words, same-language insertions before/after a switch, incorrect directions, third-language detours, wrong surviving endpoints, partial and entire-run deletions, monolingual false positives, repeated passages, unknown/neutral labels, Unicode, language-ID renaming, shared-script/multiple languages, pooled counts, input immutability and duplicate IDs. An independent run-survival oracle checks all 7,776 combinations of five-token reference labels (three languages) and deletion subsets, and 256 insertion/label cases check v3/v2 equivalence without deletions. The 34 hand-specified scenarios include two documented alignment limitations; passing their regression assertions is not claiming they agree with human intuition. They also enumerate all 121 inserted language paths of length 0–4 over three languages, and all 64 three-token label combinations over three languages plus neutral to verify agreement with exact-boundary mode when the text is unchanged.

These tests prevent the known failure where an incorrect switch direction or arbitrary extra switches can receive a perfect score. They do not prove the annotation labels themselves are right.

## Reporting sentence

“We report aligned language-switch boundary F1 (`switchf1-boundary-v3`), a proposed text-based metric requiring correct directed transitions inside corresponding alignment intervals whose endpoint languages are supported, without requiring exact neighboring words. Same-language insertions and within-run deletions can preserve the event; entirely missing runs cannot; all unmatched predicted transitions count as false positives. We pool event counts across all test utterances, including monolingual references. We also report WER/CER and optionally anchored F1 as a stricter transcription diagnostic. Language labels were obtained by [describe independently validated procedure].”

For script-derived labels replace “language” claims with **“script-based proxy”** and explicitly describe the adapter. Do not state that the metric proves the model understands switching norms or that code-switch evaluation has never existed.

## Next empirical study

Freeze v3 before collecting independent judgments. Use a new held-out sample of
at least 200 utterances, stratified by no switches, one switch, multiple switches,
partial deletions, entirely missing language spans, long insertions, repeated
passages and Romanized/shared-script text. This is a proposed pilot size, not a
power calculation. Include both systems equally and hide their identities.

Have two bilingual reviewers mark the reference spoken switches and decide which
output transitions correspond to them, separately from judging word accuracy.
Adjudicate disagreements; publish annotation agreement, false-match and missed-
match cases, direction-wise results and paired recording-level uncertainty.
Keep a separate portion for final validation if pilot findings motivate a v4.
Specifically measure how often the two known alignment failures occur and how
often deletion-tolerant matches disagree with reviewers. Do not claim broad
cross-language validity until the same procedure is repeated on other pairs.
