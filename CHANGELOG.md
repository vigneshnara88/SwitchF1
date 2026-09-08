# Changelog

## 0.3.0

- Make primary `boundary` matching insertion-aware (`switchf1-boundary-v2`).
  A correct directed event can lie anywhere inside the reference boundary's
  alignment interval when both aligned endpoint languages are correct.
- Count every predicted transition before one-to-one matching. Extra transitions
  remain false positives; deleted or wrongly labeled endpoints receive no credit.
- Retain 0.2.0's default behavior as `boundary_exact` (`switchf1-boundary-v1`).
  `anchored` (`ase-f1-v1`) remains unchanged.
- Add adversarial and exhaustive short language-path tests, alignment traces,
  and explicit audio-ground-truth and empirical-validation requirements.

Migration: 0.2.0 `mode="boundary"` becomes 0.3.0 `mode="boundary_exact"` for
reproduction. Rescore all systems with 0.3.0 `mode="boundary"` before comparing
v2 values. A score change from changing the rule is not a model improvement.

## 0.2.0

- Make aligned boundary-only F1 the API/CLI default, specification
  `switchf1-boundary-v1`.
- Retain exact-word anchored F1 as explicit `mode="anchored"`, specification
  `ase-f1-v1`. Its event-matching behavior is unchanged.
- Document displacement by long hallucinated prefixes, boundary-adjacent
  insertions, repeated-passage ambiguity, and the limits of text-only evaluation.
- Add regression coverage for those cases and explicit scoring-mode metadata.

Migration: calls that omitted `mode` in 0.1.0 computed anchored F1. Pass
`mode="anchored"` (CLI `--mode anchored`) to reproduce those semantics. Rescore all
systems with `mode="boundary"` before comparing the new default. The score change
reflects a different criterion, not a model update.

## 0.1.0

- Initial evaluator with anchored F1 as default and optional boundary mode.
- Explicit token-language labels, one-to-one directed events, pooled counts,
  language diagnostics, and unresolved-label validation.
