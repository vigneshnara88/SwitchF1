# SwitchF1: complete user walkthrough and method review

SwitchF1 asks: **does the output preserve the language changes in the reference
at corresponding places?** It evaluates explicitly language-labeled text. For
ASR, audio-verified reference words and labels connect this to spoken switching.
It does not listen to audio or infer the model's internal language decisions.

Start with the runnable functions below, then explore [all 34 worked examples](scenario_audit.md#every-example-with-its-complete-labeled-text).
The [formal specification](method.md) gives the full alignment and matching formulas.

## Install

```bash
python -m pip install "git+https://github.com/vigneshnara88/SwitchF1.git"
```

For reproducible metric behavior, pin a version or commit, for example
`git+https://github.com/vigneshnara88/SwitchF1.git@v0.4.0`. The expanded documentation
on `main` describes the same v3 algorithm as that release.

To run the repository's supplied examples:

```bash
git clone https://github.com/vigneshnara88/SwitchF1.git
cd SwitchF1
python -m pip install .
```

## Score one reference/output pair

```python
from switchf1 import Token, score_utterance

# Languages are supplied explicitly. ennaku is Romanized Tamil here.
reference = [
    Token("hello", "en"),
    Token("ennaku", "ta"),
    Token("coffee", "en"),
]
hypothesis = [
    Token("hello", "en"),
    Token("ennaku", "ta"),
    Token("coffee", "en"),
    Token("nandri", "ta"),
]

result = score_utterance(
    reference,
    hypothesis,
    mode="boundary",       # default: boundary v3 in package 0.4.0
    utterance_id="clip-1",  # optional identifier for the returned trace
)

assert (result["tp"], result["fp"], result["fn"]) == (2, 1, 0)
assert result["precision"] == 2 / 3
assert result["recall"] == 1.0
assert result["f1"] == 0.8
print(f"SwitchF1: {100 * result['f1']:.1f}%")  # SwitchF1: 80.0%
```

The reference switches English → Tamil → English: two events. The output keeps
both and adds English → Tamil at the end: two correct events and one extra.
Scores are returned as **fractions between 0 and 1**, or `None` when undefined.
Multiply by 100 for a percentage; do not interpret 0.8 as 0.8%.

You can supply dictionaries instead of `Token` objects:

```python
from switchf1 import score_utterance

result = score_utterance(
    [{"text": "hello", "lang": "en"}, {"text": "ennaku", "lang": "ta"}],
    [{"text": "hi", "lang": "en"}, {"text": "unakku", "lang": "ta"}],
)
assert result["f1"] == 1.0
```

Both words are wrong in the second example, but the aligned English → Tamil
transition is preserved. WER still penalizes the substitutions. SwitchF1 does not
establish that these invented words were spoken.

A plain string such as `"hello ennaku"` is **not** accepted: it lacks token-language
labels. The function does not automatically identify languages or tokenize text.

## What each input means

| Input | Meaning |
|---|---|
| `reference` | Ordered reference tokens; each contains `text` and `lang` |
| `hypothesis` | Ordered model-output tokens, independently language-labeled |
| `mode` | Matching rule; default `boundary` uses v3 in version 0.4.0 |
| `utterance_id` | Optional name returned in the result as `id` |

Use any fixed language IDs consistently; `en`, `ta`, `fr` and `es` are examples.
Shared-script languages are supported because the scorer consumes explicit labels.
Freeze your tokenizer and label policy across systems. For languages without
spaces, supply an appropriate tokenization rather than assuming whitespace words.

An ordinary transcript usually has no word-level language labels. Use independent
human annotation, validated contextual text language identification, or actual
per-token model labels. Do not copy reference labels onto the hypothesis. A script
rule is a restricted proxy: Latin-written Tamil is not automatically English.
If a separate labeler supplies the hypothesis labels, the evaluation reflects the
ASR output **and** that labeler.

`lang=None` (JSON `null`) is for deliberately neutral tokens under a fixed policy,
not missing annotations. Labels `und`, `mul` and `ambiguous` are rejected; resolve
them first. Empty transcripts use `[]`. Each token must have nonempty text.

## How the function is calculated

### 1. Align the words

Apply Unicode NFC and lowercase to token text. Preserve scripts, marks, numbers
and repetitions. This is the package's own minimal alignment convention; it is
not an STT WER normalizer and does not run a repetition reducer.

Compute unit-cost Levenshtein alignment on **text only**: equal words cost zero;
substitutions, deletions and insertions each cost one. Ties during backtracking
prefer diagonal, deletion, insertion. Language labels never choose the alignment.
The result is shared columns containing two tokens or a token opposite a gap.

### 2. Find the language changes

On each side, a change between successive non-neutral language labels creates a
**directed event**. English → Tamil differs from Tamil → English. Count every
event, including invented switches on monolingual references. Separate records
do not create cross-record switches.

### 3. Match corresponding events

For each original reference boundary A → B:

1. Find the nearest surviving aligned reference token backwards within its A
   language stretch and forwards within its B stretch. Only missing words may
   be skipped; never cross another reference language stretch.
2. Check that the hypothesis tokens aligned to these chosen support words have
   languages A and B. A surviving wrong label blocks the match; do not search
   past it for a better label. If a whole adjacent run is absent, no match exists.
3. Match the earliest unused hypothesis A → B event fully inside that supported
   alignment interval. Exact words are not required. Count extra events as errors.

These intervals have disjoint interiors. A reference event and a hypothesis
event can each be credited at most once. One middle surviving word can support
the two distinct switches on either side, but one event cannot be reused.

### 4. Count correct, extra and missed switches

Let M be the number of matches, G the reference event count and H the hypothesis
event count:

$$
TP=M,\qquad FP=H-M,\qquad FN=G-M.
$$

- **TP (true positive):** a correctly matched directed switch.
- **FP (false positive):** an output switch with no eligible reference match.
- **FN (false negative):** a reference switch with no eligible output match.

A misplaced output switch can cause both one FP and one FN: it introduced an
unmatched event while failing to preserve the real event.

### 5. Compute precision, recall and F1

$$
P=\frac{TP}{TP+FP},\qquad R=\frac{TP}{TP+FN},\qquad
F1=\frac{2TP}{2TP+FP+FN}.
$$

In the first Python example, TP=2, FP=1 and FN=0:

- Precision = `2 / (2 + 1)` = **66.7%**: two of three output switches are correct.
- Recall = `2 / (2 + 0)` = **100%**: both reference switches were preserved.
- F1 = `4 / (4 + 1 + 0)` = **80%**.

Every switch has the same event weight. There is no weighting by generated word
count. Longer output hurts boundary F1 if it creates unmatched transitions;
same-language repetition can leave F1 unchanged and still cause large WER.

## Score a whole dataset

Use `evaluate` to pool event counts before calculating the ratios:

```python
from switchf1 import evaluate

records = [
    {
        "id": "clip-1",
        "reference": [
            {"text": "hello", "lang": "en"},
            {"text": "ennaku", "lang": "ta"},
            {"text": "coffee", "lang": "en"},
        ],
        "hypothesis": [
            {"text": "hello", "lang": "en"},
            {"text": "ennaku", "lang": "ta"},
            {"text": "coffee", "lang": "en"},
            {"text": "nandri", "lang": "ta"},
        ],
    },
    {
        "id": "clip-2",
        "reference": [{"text": "hello", "lang": "en"}],
        "hypothesis": [
            {"text": "hello", "lang": "en"},
            {"text": "vanakkam", "lang": "ta"},
        ],
    },
]

report = evaluate(records, mode="boundary")
metrics = report["metrics"]
assert report["specification"] == "switchf1-boundary-v3"
assert (metrics["tp"], metrics["fp"], metrics["fn"]) == (2, 2, 0)
assert metrics["f1"] == 2 / 3
print(metrics["by_direction"])
```

Clip 2 has no real switch but adds an invented one, so it contributes one FP.
Pooled F1 is `4 / (4 + 2 + 0)` = **66.7%**. Averaging clip F1 values would give
`(80% + 0%) / 2 = 40%`, a different statistic. **Do not average clip F1.**

Alternatively, `aggregate([score_utterance(...), ...])` pools already scored rows.
Do not mix modes. `evaluate` rejects duplicate IDs; your benchmark loader must
also verify all expected IDs are present, rather than silently dropping failures.
For within-speaker switching, give separate speaker streams/turns as appropriate.

## Understand the returned fields

| Field | Meaning |
|---|---|
| `tp`, `fp`, `fn`, `precision`, `recall`, `f1` | Counts and scores explained above |
| `reference_events`, `hypothesis_events` | Total events before matching |
| `alignment` | Zero-based `(reference_index, hypothesis_index)` pairs; `None` means a gap |
| `ref_events`, `hyp_events` | Direction, original token indices, aligned positions and lexical anchors |
| `supported_intervals` | Alignment-column limits considered for each reference event; `None` if support is absent; labels may still disqualify a non-null interval |
| `matches` | Zero-based `(reference_event_index, hypothesis_event_index)` pairs |
| `matches_across_deletions` | Matches requiring expansion past deleted reference boundary words |

`evaluate` returns `specification`, `mode`, pooled `metrics`, and detailed
`utterances`. Its metrics additionally include direction-wise scores, false-switch
incidence on no-switch references, language-presence checks and aligned token-
language F1. These diagnostics answer separate questions and do not alter boundary
F1. The CLI adds package version and input-file hash; Python callers should record
`switchf1.__version__` and their own input hashes for reproducibility.

Precision is `None` when there are no output events; recall is `None` when there
are no reference events. F1 is zero if any events exist but none match. If neither
side has any events, F1 is `None`, not 100%. Handle that when formatting:

```python
def format_f1(value):
    return "undefined (no events)" if value is None else f"{100 * value:.1f}%"
```

## Use the CLI and inspect all examples

From an installed checkout:

```bash
switchf1 examples/pairs.jsonl --output results/basic.json
switchf1 examples/adversarial.jsonl --output results/adversarial.json
# Equivalent module invocation:
python -m switchf1 examples/adversarial.jsonl --output results/adversarial.json
# Reproduce the human-readable 34-case audit:
python examples/audit_scenarios.py --markdown docs/scenario_audit.md
```

Each JSONL line is one object with `id`, `reference` and `hypothesis`; the latter
two are arrays of `{ "text": "...", "lang": "..." }` objects. The six basic and
34 adversarial records are complete runnable inputs, not pseudocode.

## Why v3 changed and what remains difficult

V2 rejected a switch when an immediately neighboring reference word was omitted.
V3 lets the adjacent language stretches provide surviving support. Thus
`hello my name is sam/en ennaku/ta` versus `hello my name/en ennaku/ta` receives
switch credit while WER counts the omissions. Several switches are counted
independently. Entirely omitted language stretches still lose their events.

Same-language hallucinations can preserve perfect F1. Wrong words in the right
languages may also receive credit. Conversely, hallucinations combined with
omissions can align as substitutions and cause a human-plausible switch to fail.
Changed neutral punctuation can cause similar alignment failures. Two such cases
are explicitly identified in the [complete audit](scenario_audit.md); their desired
human interpretation is distinguished from the implemented result.

Repeated passages can admit several equally good text alignments. Fixed tie-
breaking makes the result reproducible, but cannot establish which copy was spoken.
Do not choose the alignment that maximizes F1. Do not replace positional matching
with language presence or switch counts, which would reward misplaced switches.

The method supports arbitrary explicit language IDs but is **experimental**.
Constructed examples and exhaustive checks establish implementation behavior;
independent bilingual/audio validation and transfer studies establish empirical
validity. Report WER/CER, precision/recall, event support, directional results and
hallucination diagnostics alongside it. See the [validation plan](validation.md).

## Versioning and further reading

| Mode in package 0.4.0 | Specification | Criterion |
|---|---|---|
| `boundary` (default) | `switchf1-boundary-v3` | Supported intervals with within-run deletion tolerance |
| `boundary_v2` | `switchf1-boundary-v2` | Original endpoints, insertion tolerance only |
| `boundary_exact` | `switchf1-boundary-v1` | Exact event alignment columns |
| `anchored` | `ase-f1-v1` | Exact event columns and exact normalized neighboring words |

Pin package version and mode. Rescore all compared systems under the same rule;
a definition change is not a model improvement. Keep tokenizer, language labels
and benchmark coverage consistent across systems.

- [All worked examples and calculations](scenario_audit.md).
- [Alignment walkthrough and counterexamples](alignment.md).
- [Complete mathematical specification](method.md).
- [Background, applications and prior research](../README.md#related-work-and-validity).
- [Tests](../tests/test_scenarios.py) and [public inputs](../examples/adversarial.jsonl).

This repository documents a particular reusable boundary metric. It does not
claim that code-switch detection or its evaluation has never been studied before.
