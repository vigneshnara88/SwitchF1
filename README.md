# SwitchF1

**Measure whether a transcript preserves the correct language switches, not just how many switches it contains.**

SwitchF1 is a dependency-free Python evaluator for **Anchored Switch Event F1 (ASE-F1)**. It compares reference and predicted text with explicit token-language labels. A correct event needs the same directed language change, the same aligned boundary, and correctly recognized words immediately on both sides. It requires no timestamps and makes no assumption that different languages use different scripts.

This is a proposed, documented evaluation method with executable tests. It is not an established industry standard or a claim to have invented code-switch evaluation. Its empirical validity across language pairs still needs independent annotation and human-agreement studies.

## Purpose

Speech systems should preserve how multilingual speakers move between languages, including English and other languages. This matters in communities where everyday conversation, education, media and online communication involve multiple languages, including younger multilingual speakers. The motivation does not depend on an unverified claim that all young people code-switch more often or that one global trend applies everywhere.

Overall transcription accuracy can hide failures around language transitions. SwitchF1 formalizes a narrower question: **does the recognized text preserve the reference's language transition at the right place, with correct local words?**

Potential downstream uses include evaluating multilingual captions, language-dependent search and indexing, vocabulary routing, bilingual educational tools, and conversation systems that should preserve a speaker's language choices. These are applications of detecting switches. A high score alone does not demonstrate understanding of social switching norms, speaker intent, identity, or pragmatics.

## Install and run

From this repository:

```bash
python -m pip install .
switchf1 examples/pairs.jsonl --output results/example.json
python -m unittest discover -s tests -v
```

The project uses a standard Python package layout and can be installed from a Git URL once hosted. No public remote or PyPI release is implied by this local repository.

```python
from switchf1 import Token, score_utterance

reference = [Token("hello", "en"), Token("bonjour", "fr")]
hypothesis = [Token("hello", "en"), Token("bonjour", "fr")]
result = score_utterance(reference, hypothesis)
assert result["f1"] == 1.0
```

For corpus scoring, use `evaluate(records)` or the CLI. JSONL records have this shape:

```json
{"id":"clip-1","reference":[{"text":"hello","lang":"en"},{"text":"bonjour","lang":"fr"}],"hypothesis":[{"text":"hello","lang":"en"},{"text":"bonjour","lang":"fr"}]}
```

The scorer consumes labels; it does not guess languages. Obtain reference labels from reviewed annotations and hypothesis labels from independently validated text LID or a system that emits token-language labels. Do not copy labels from the reference to the hypothesis. English and French share a script, and Romanized Tamil is not automatically English.

## What counts

For reference `hello/en bonjour/fr`:

| Hypothesis | TP | FP | FN | ASE-F1 | Reason |
|---|---:|---:|---:|---:|---|
| `hello/en bonjour/fr` | 1 | 0 | 0 | 1 | Correct directed event and anchors |
| `hello/fr bonjour/en` | 0 | 1 | 1 | 0 | Wrong language direction |
| `goodbye/en salut/fr` | 0 | 1 | 1 | 0 | Correct shape, wrong local words |
| `hello/en bonjour/fr again/en` | 1 | 1 | 0 | 2/3 | Extra reverse switch penalized |
| `hello/en` | 0 | 0 | 1 | 0 | Missed switch |

All reference clips count, including monolingual clips. A false switch on a monolingual reference adds FP. A corpus with no true or predicted switches has undefined F1 (`null`), not a perfect switching score.

## Formula and reporting

After per-utterance lexical alignment, construct directed events from successive non-neutral language-labeled tokens. Match events one-to-one under the rules in [the method specification](docs/method.md).

\[
P=\frac{TP}{TP+FP},\quad R=\frac{TP}{TP+FN},\quad
F_{1,\mathrm{ASE}}=\frac{2TP}{2TP+FP+FN}.
\]

Pool TP/FP/FN across the corpus before computing these ratios. Do not average utterance F1. Report F1 with precision, recall, event support, direction-wise counts, and false-switch rate on monolingual references. Pair it with WER/CER.

The optional `--mode boundary` removes the exact-word anchor requirement while retaining directed, aligned event matching. Call it **aligned boundary F1**, not ASE-F1. The gap between these modes helps separate local word errors from switch-structure errors. Neither mode measures acoustic switch timing.

ASE-F1 is deliberately strict: a correct language boundary next to a misspelled word can fail. It therefore measures **locally correct transcription of switches**, rather than pure language identification. This tradeoff must be disclosed rather than interpreting every missed anchored event as a language-detection error.

## Related work and validity

- [PIER, ICASSP 2025](https://arxiv.org/abs/2501.09512) evaluates errors in selected code-switched words. It motivates reporting targeted metrics beside overall WER; it is not this event-matching rule.
- [Benchmarking Evaluation Metrics for Code-Switching ASR, SLT 2022/2023](https://arxiv.org/abs/2211.16319) investigates agreement with human judgments and shows why transcript conventions matter.
- [MERLIon CCS, Interspeech 2023](https://www.isca-archive.org/interspeech_2023/chua23_interspeech.pdf) evaluates language identification/diarization; [DISPLACE 2024](https://displace2024.github.io/) specifies time-based language diarization evaluation. SwitchF1 instead evaluates labeled text.
- [The 2016 code-switched language-identification shared task](https://aclanthology.org/W16-5805/) documents ambiguous, mixed and other token categories. Language annotation policy is part of the benchmark.

These precedents rule out an unsupported claim that language-switch evaluation has never been formalized. Our contribution is the particular reproducible, directed, lexically anchored event definition and this reusable implementation. See [validation requirements](docs/validation.md) before making broad empirical claims.

## Reproducibility

Version `0.1.0`, specification `ase-f1-v1`. CLI output includes the package version, input hash, counts, per-event matches, and alignment traces. Record the Git commit, annotation policy, tokenizer, reference/prediction hashes, and scoring mode with published results. The software is MIT licensed; the license does not grant rights to external evaluation data.
