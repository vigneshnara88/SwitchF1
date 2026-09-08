# SwitchF1

**Measure whether a transcript preserves the correct language switches, not just how many switches it contains.**

SwitchF1 is a dependency-free Python evaluator for **aligned language-switch boundary F1**. It compares reference and predicted text with explicit token-language labels. A correct event needs the same directed language change inside the corresponding supported boundary interval after text alignment. Same-language insertions beside the switch do not automatically invalidate it; extra language transitions still count as errors. The neighboring words may be substituted: exact word recognition is not required by the primary boundary score. It requires no timestamps and makes no assumption that different languages use different scripts.

Version **0.3.0 defaults to `boundary`**, specification `switchf1-boundary-v2`. Use `boundary_exact` for the earlier exact-position rule (`switchf1-boundary-v1`) or `anchored` for exact positions plus exact local words (`ase-f1-v1`). See [migration notes](CHANGELOG.md); always record package version and mode.

This is a proposed, documented evaluation method with executable tests. It is not an established industry standard or a claim to have invented code-switch evaluation. Its empirical validity across language pairs still needs independent annotation and human-agreement studies.

## Purpose

Speech systems should preserve how multilingual speakers move between languages, including English and other languages. This matters in communities where everyday conversation, education, media and online communication involve multiple languages, including younger multilingual speakers. The motivation does not depend on an unverified claim that all young people code-switch more often or that one global trend applies everywhere.

Overall transcription accuracy can hide failures around language transitions. SwitchF1 formalizes a narrower question: **does the recognized text preserve the reference's directed language transition at the corresponding aligned place?**

Potential downstream uses include evaluating multilingual captions, language-dependent search and indexing, vocabulary routing, bilingual educational tools, and conversation systems that should preserve a speaker's language choices. These are applications of detecting switches. A high score alone does not demonstrate understanding of social switching norms, speaker intent, identity, or pragmatics.

## Install and run

```bash
git clone git@github.com:vigneshnara88/SwitchF1.git
cd SwitchF1
python -m pip install .
```

From this repository:

```bash
python -m pip install .
switchf1 examples/pairs.jsonl --mode boundary --output results/example.json
# Optional stricter diagnostic:
switchf1 examples/pairs.jsonl --mode anchored --output results/anchored.json
python -m unittest discover -s tests -v
```

Or install directly from the Git repository:

```bash
python -m pip install "git+https://github.com/vigneshnara88/SwitchF1.git"
```

For reproducible research, append `@COMMIT_SHA` to the Git URL using the commit
you evaluated. This project does not require a PyPI release.

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

The scorer consumes labels; it does not guess languages. Obtain reference words and labels from annotations checked against the speech and hypothesis labels from independently validated text LID or a system that emits token-language labels. Do not copy labels from the reference to the hypothesis. English and French share a script, and Romanized Tamil is not automatically English.

## Where do the labels come from?

An ordinary ASR transcript usually contains **words, not a language label for every word**. An ASR system may also return one language for the whole recording. That is not enough to locate switches inside a sentence. If your system already emits per-token language labels, you can supply them directly after mapping them to your benchmark's label policy.

Start with a simple example:

```text
Reference words:       hello   bonjour
Reference languages:  en      fr
Model words:           hello   bonjour   again
Model languages:       en      fr        en
```

The reference contains one switch, English → French. The model preserved it and added an extra French → English switch. We count one correct event and one false event.

The full workflow is:

1. **Get the words.** Keep the reference transcript and the model transcript separately. For ASR evaluation, check the reference words and language choices against the audio; a model-generated reference is not automatically ground truth.
2. **Label each token's language.** Review reference labels. For model output, use a validated contextual token-language identifier, independent human annotation, or labels actually produced by the model. Do not assign the reference's labels to the model output.
3. **Align the words.** The evaluator finds an ordinary edit alignment, including inserted, deleted and substituted words.
4. **Find language changes.** Adjacent non-neutral language labels that differ create a directed event, such as `en → fr`.
5. **Check each event.** The primary score requires the same direction inside the reference boundary interval, supported by correct hypothesis languages at both aligned endpoints. Exact positions and words are required only in the stricter diagnostics.
6. **Count correct, extra and missed events.** Convert the pooled counts to precision, recall and F1 with the formulas below.

Tamil and English often use visibly different scripts, so a script rule can provide a convenient **proxy** for their labels. It can still fail on Romanized Tamil, borrowing or names. English and French both use Latin letters, so script cannot distinguish them; the words and their context must be considered. This package deliberately keeps the label source separate from scoring so it can support other language pairs correctly.

When a separate LID model labels plain ASR text, the result evaluates the **ASR output plus that labeler**. It does not reveal what language Whisper internally believed each word belonged to. Report the labeler's version and validation accuracy. If the task is instead to test a language detector itself, give the same tokens on both sides and compare gold versus predicted language labels. Still report token-language F1: labeling an entire English sentence French creates no switches but is completely wrong LID. The package reports aligned token-language micro/macro F1 alongside switch F1 to expose that case.

Use `lang=null` only for deliberately neutral tokens under the same frozen annotation policy for both sides. Do not fill missing language labels with null: that would hide switches. Unknown reference **or hypothesis** labels are rejected, because abstaining on a false switch must not improve the headline score. Use the same validated labeler/settings for every ASR system. For languages without spaces, use an appropriate fixed tokenizer; the package does not assume whitespace is universal word segmentation.

## What counts

For reference `hello/en bonjour/fr`:

| Hypothesis | TP | FP | FN | Boundary F1 | Reason |
|---|---:|---:|---:|---:|---|
| `hello/en bonjour/fr` | 1 | 0 | 0 | 1 | Correct directed event and aligned location |
| `hello/fr bonjour/en` | 0 | 1 | 1 | 0 | Wrong language direction |
| `goodbye/en salut/fr` | 1 | 0 | 0 | 1 | Correct aligned language boundary; WER still penalizes both wrong words |
| `hello/en bonjour/fr again/en` | 1 | 1 | 0 | 2/3 | Extra reverse switch penalized |
| `hello/en` | 0 | 0 | 1 | 0 | Missed switch |

All reference clips count, including monolingual clips. A false switch on a monolingual reference adds FP. A corpus with no true or predicted switches has undefined F1 (`null`), not a perfect switching score.

## Formula and reporting

After per-utterance lexical alignment, construct directed events from successive non-neutral language-labeled tokens. Match events one-to-one under the rules in [the method specification](docs/method.md).

$$
P=\frac{TP}{TP+FP},\quad R=\frac{TP}{TP+FN},\quad
F_{1,\mathrm{boundary}}=\frac{2TP}{2TP+FP+FN}.
$$

Pool TP/FP/FN across the corpus before computing these ratios. Do not average utterance F1. Report F1 with precision, recall, event support, direction-wise counts, and false-switch rate on monolingual references. Pair it with WER/CER.

The optional `--mode boundary_exact` requires the exact pair of alignment positions and is called **exact-boundary F1**. `--mode anchored` also requires exact normalized words on both sides and is called **Anchored Switch Event F1 (ASE-F1)**. The boundary score measures aligned language structure; anchored F1 measures locally correct transcription of that structure. Both depend on lexical alignment and tokenization. Neither establishes pure acoustic language detection or switch timing.

## What if hallucinations move the correct switch far away?

Raw token numbers are **not** matched. First align the complete reference and hypothesis token sequences by ordinary minimum edit distance. Inserted words create gap columns on the reference side:

```text
Reference:   —     —     —    we/en  say/en | bonjour/fr  maintenant/fr
Hypothesis: blah  blah  blah  we/en  say/en | bonjour/fr  maintenant/fr
```

The switch still matches because `say` and `bonjour` occupy the same shared alignment columns. This remains true with 100 inserted prefix words. WER counts those 100 insertions; boundary F1 can still be perfect when the insertions introduce no additional language changes. That is why both metrics must be reported.

Extra words directly beside the switch are handled using a supported interval:

```text
Reference:  we/en  say/en    —       —       —      bonjour/fr
Hypothesis: we/en  say/en  blah/en  blah/en  salut/fr bonjour/fr
                         <--- one en → fr transition --->
```

The reference endpoint words `say` and `bonjour` align to output words labeled English and French respectively. The interval between them contains a direct English → French event, so **boundary F1 credits one correct switch**. WER still counts all three extra words. The earlier exact-position rule would reject this example; it remains available as `boundary_exact`.

This is not permission to ignore invented switches. If inserted labels go `en → fr → en → fr`, only one `en → fr` event can match the reference; the other two events are FP. If they go `en → de → fr`, neither event is a direct `en → fr` switch, so both are FP and the reference switch is FN. If the aligned endpoint words have wrong language labels or are deleted, the interval is not supported and receives no credit.

If a whole switched passage is hallucinated repeatedly, a reference switch can match only once; unmatched predicted switches are FP. Several identical passages can admit equally good text alignments. The fixed tie rule picks one deterministically; it cannot tell which copy was acoustically grounded. A long hallucination in the expected languages can still preserve the switch structure, so boundary F1 must be paired with WER/CER and hallucination diagnostics.

See [alignment and hallucination examples](docs/alignment.md) for the full rule and executable examples. No timestamps means text offset cannot tell us whether a model switched too late **in the audio**. Audio-verified reference labels connect this measure to spoken switching, but the scorer cannot recover hidden model beliefs or validate the audio by itself.

## Related work and validity

- [PIER, ICASSP 2025](https://arxiv.org/abs/2501.09512) evaluates errors in selected code-switched words. It motivates reporting targeted metrics beside overall WER; it is not this event-matching rule.
- [Benchmarking Evaluation Metrics for Code-Switching ASR, SLT 2022/2023](https://arxiv.org/abs/2211.16319) investigates agreement with human judgments and shows why transcript conventions matter.
- [MERLIon CCS, Interspeech 2023](https://www.isca-archive.org/interspeech_2023/chua23_interspeech.pdf) evaluates language identification/diarization; [DISPLACE 2024](https://displace2024.github.io/) specifies time-based language diarization evaluation. SwitchF1 instead evaluates labeled text.
- [The 2016 code-switched language-identification shared task](https://aclanthology.org/W16-5805/) documents ambiguous, mixed and other token categories. Language annotation policy is part of the benchmark.

These precedents rule out an unsupported claim that language-switch evaluation has never been formalized. Our contribution is the particular reproducible, directed, aligned boundary definition, optional lexical anchoring and this reusable implementation. See [validation requirements](docs/validation.md) before making broad empirical claims.

## Reproducibility

Version `0.3.0`: primary specification `switchf1-boundary-v2`; optional exact-position specification `switchf1-boundary-v1`; optional anchored specification `ase-f1-v1`. CLI output includes the package version, input hash, counts, per-event matches, and alignment traces. Record the Git commit, annotation policy, tokenizer, reference/prediction hashes, and scoring mode with published results. The software is MIT licensed; the license does not grant rights to external evaluation data.
