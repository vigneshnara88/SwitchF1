# Validation plan and release status

Release 0.1.0 provides a specified algorithm, package, examples and semantic regression tests. It is an experimental method. No multi-language human-validation study or peer-reviewed novelty claim is included.

## Required checks before external performance claims

1. **Gold labels:** Have two bilingual annotators independently label a fixed, model-blinded sample. Resolve borrowing, named-entity, filler, mixed-token and ambiguous cases under a written policy. Keep hypothesis labels independent of reference labels and model identity.
2. **Human construct validity:** Ask reviewers whether each proposed transcript switch has the correct language direction, location and local words. Compare anchored and boundary scores with these judgments. Use a held-out portion to assess correlation, rather than selecting rules and demonstrating agreement on the same examples.
3. **Language transfer:** Include at least one different-script pair, one shared-script pair (e.g. English-French), a pair without English, and three-language utterances. Do not infer broad validity from Tamil-English alone.
4. **Coverage:** Include monolingual controls, short utterances, genuine repetitions, hallucinated language insertions, entire-language deletions, ASR word errors next to switches, and Romanized text. Report excluded ambiguous regions and annotation agreement.
5. **Uncertainty:** Resample paired recordings/speakers and pool event counts inside each sample. Report percentile confidence intervals and separate variation across model training seeds. Repeated clips from the same speaker are not independent evidence.

## What the tests establish

Tests check perfect matches, incorrect directions, wrong lexical anchors, inserted and missed switches, no-switch false positives, repeat spam, unknown/neutral handling, Unicode preservation, identical results after consistent language-ID renaming, multiple/shared-script languages, pooled counts, input immutability, and duplicate-ID rejection.

These tests prevent the known failure where an incorrect switch direction or arbitrary extra switches can receive a perfect score. They do not prove the annotation labels themselves are right.

## Reporting sentence

“We report Anchored Switch Event F1 (ASE-F1 v1), a proposed text-based metric requiring correct directed language transitions and exact normalized words at both aligned boundary anchors. We pool event counts across all test utterances, including monolingual references. We additionally report aligned boundary F1 and WER/CER. Language labels were obtained by [describe independently validated procedure].”

For script-derived labels replace “language” claims with **“script-based proxy”** and explicitly describe the adapter. Do not state that the metric proves the model understands switching norms or that code-switch evaluation has never existed.
