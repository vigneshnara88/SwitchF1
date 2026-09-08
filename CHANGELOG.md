# Changelog

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
