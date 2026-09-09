# SwitchF1

**Measure whether a transcript preserves the correct language switches, not just how many switches it contains.**

SwitchF1 is a dependency-free Python evaluator for **aligned language-switch boundary F1**. It compares reference and predicted text with explicit token-language labels. A correct event needs the same directed language change inside the corresponding supported boundary interval after text alignment. Same-language insertions and omitted words within the two adjacent language stretches do not automatically invalidate it; extra language transitions still count as errors. The neighboring words may be substituted: exact word recognition is not required by the primary boundary score. It requires no timestamps and makes no assumption that different languages use different scripts.

Version **0.4.0 defaults to `boundary`**, specification `switchf1-boundary-v3`. Use `boundary_v2` for the insertion-only v2 rule, `boundary_exact` for the earlier exact-position rule (`switchf1-boundary-v1`) or `anchored` for exact positions plus exact local words (`ase-f1-v1`). See [migration notes](CHANGELOG.md); always record package version and mode.

This is a proposed, documented evaluation method with executable tests. It is not an established industry standard or a claim to have invented code-switch evaluation. Its empirical validity across language pairs still needs independent annotation and human-agreement studies.

> **Interpretation caveat:** SwitchF1 is an indicative statistic of language-switch
> preservation in text, not ground truth about the exact switches in speech.
> Longer individual transcripts can make correspondence less reliable, especially
> with repeated passages, hallucinations or omissions: a matched text transition
> does not prove that the model switched at the correct moment in the audio.
> Reliable word-level timestamps on both sides could support more precise
> localization in a separately validated time-aware evaluator. The current scorer
> does not use timestamps, and timestamps alone do not guarantee correctness.
> See [long transcripts and timing](docs/review.md#long-transcripts-timing-and-how-to-interpret-the-score).

## Start here

- **[Full method review and walkthrough](docs/review.md):** what the score measures, how labels and alignment work, formulas, multiple switches, omissions, hallucinations and limitations.
- **[All 34 worked examples](docs/scenario_audit.md#every-example-with-its-complete-labeled-text):** expand each case to see the complete reference and output, token-language labels, correct/extra/missed counts, F1 calculation and explanation.
- **[Exact mathematical specification](docs/method.md):** the reproducible v3 matching and aggregation rules.
- **[Runnable inputs](examples/adversarial.jsonl)** and **[basic examples](examples/pairs.jsonl):** use the same examples with the Python API or CLI.
- **[Validation status](docs/validation.md):** what has been tested and which human/audio checks remain necessary.

## Background: speech across languages

Multilingual speakers can move between languages within a conversation, a sentence, or even a short phrase. This practice, commonly called **code-switching**, is part of the speech that ASR systems need to represent. A speaker might use one language for the surrounding sentence and another for a familiar expression, a technical term, a quotation, or a change in emphasis. Research on speech transcripts documents motivations including expressing emotion, borrowing terms, humor and introducing a topic. [Belani and Flanigan, 2022](https://arxiv.org/abs/2212.08565)

**Our motivating assumption is that younger multilingual speakers in communities with strong exposure to English may code-switch more frequently than older generations**, particularly as English becomes part of education, entertainment, social media and peer interaction. A person may speak a local language at home, encounter English terminology in class or online, and bring both into everyday conversation. Speech technology should be designed and evaluated for that mixed-language use. Research on multilingual youth communication provides context for these practices; the age comparison here is a project assumption, not an effect measured by SwitchF1. [Multilingual Youth Practices in Computer Mediated Communication](https://www.cambridge.org/core/books/multilingual-youth-practices-in-computer-mediated-communication/190771570DA07D9607A0B8987F2432B7)

English–Tamil speech motivated this project, but the evaluation question applies to English–Spanish, English–Hindi, English–Mandarin, shared-script pairs such as English–French, and combinations without English. It also applies when a speaker uses more than two languages. Those settings require explicit language labels: identifying the alphabet alone cannot distinguish languages that share a writing system. Earlier work on multilingual word-level language identification demonstrates the importance of handling more than one fixed language pair. [Rijhwani et al., ACL 2017](https://aclanthology.org/P17-1180/)

For a recognizer, being able to transcribe each language separately does not establish that it preserves the places where a speaker moves between them. A system may omit a switched phrase, render it in the surrounding language, or introduce a change that was never spoken. These are concrete behaviors that an evaluation should expose. If a reference contains only a short span in its less frequent language, an overall average may give little visibility into what happened at that transition.

## Purpose: measure preservation of language changes

SwitchF1 formalizes the question: **when the speaker changes language, does the model's output preserve that directed transition at the corresponding place?** For speech-model evaluation, the reference transcript and its token-language labels must be checked against the audio. The evaluator then compares that reference with independently labeled model output.

The primary score separates **switch preservation** from **exact word recognition**. If the speaker changes from English to French and the output preserves that change using incorrect English and French words, the switch should receive credit. WER and CER still penalize the wrong words. If the output stays entirely in English, invents an extra change, or reverses the transition, the switch score should reflect that failure. This distinction lets us ask what a model got right about the multilingual structure even when transcription is imperfect.

Precision asks how many predicted transitions correspond to real reference transitions. Recall asks how many reference transitions were preserved. F1 balances the two, so a system cannot obtain a perfect score merely by generating many language changes. Matching is tied to text alignment, and each reference event can receive credit only once. Same-language insertions beside a supported switch can preserve its boundary credit while remaining transcription errors.

The purpose of publishing SwitchF1 is to make that definition **explicit, reproducible and reusable**: shared formulas, an executable evaluator, inspectable alignments, and tests for cases that otherwise lead to inconsistent scoring. The same rule should apply to every model and language pair under a declared annotation policy. SwitchF1 complements corpus WER/CER, token-language scores and hallucination diagnostics. It gives a focused view of switching behavior that an overall transcription score alone does not supply.

## Why preserving switches matters

Potential downstream applications include:

- **Multilingual captions and transcripts:** assess whether the output preserves the speaker's language choices, including short switched phrases that a dominant-language average can obscure.
- **Search and retrieval:** evaluate the language boundaries supplied to systems that select language-specific tokenization, dictionaries or indexes for different spans.
- **Conversational assistants:** assess whether an ASR front end preserves the language changes that a downstream system could use when interpreting an utterance or choosing a response language.
- **Bilingual learning and classroom tools:** support evaluation of transcripts where explanations, examples and subject terminology move between languages, without automatically treating mixing as a mistake.
- **Research on switching norms:** check whether a transcript retains the transitions needed for later analysis of emphasis, quotation, topic changes and social context. Separate annotated tasks are needed to evaluate those meanings themselves.

Preserving an observable switch is a useful step toward systems that can respond appropriately to multilingual communication. SwitchF1 measures that step. Understanding why someone switched, what the change signals socially, or whether a reply respects local switching norms requires additional contextual evaluation. The metric is intended to make progress on this specific capability measurable while keeping those broader research questions open.

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

## Multiple switches and missing words

Treat each language change as a separate event. In `hello/en ennaku/ta coffee/en`
there are **two** switches: English → Tamil and Tamil → English.

| Reference | Output | TP / FP / FN | F1 |
|---|---|---|---:|
| `hello my name is sam/en ennaku/ta` | `hello my name/en ennaku/ta` | 1 / 0 / 0 | 100% |
| Same reference | `hello/en ennaku/ta name sam/en` | 0 / 2 / 1 | 0% |
| `hello friend/en ennaku venum/ta coffee today/en` | `hello/en venum/ta today/en` | 2 / 0 / 0 | 100% |
| Same reference | `hello friend coffee today/en` | 0 / 0 / 2 | 0% |
| Same reference | `hello friend/en ennaku venum/ta` | 1 / 0 / 1 | 66.7% |
| Same reference | Correct output followed by `nandri/ta` | 2 / 1 / 0 | 80% |

Suffixes label each preceding stretch in this table; API inputs still label every
token. `ennaku` is explicitly Tamil here despite Latin spelling. Do not assign it
English merely because it uses Latin letters.

The rule keeps original reference language stretches and uses the nearest surviving
word on each side of each switch. Missing some words can preserve a switch;
missing the entire intervening language cannot. A single surviving middle word
can support the two different events on either side, but one predicted event can
never receive credit twice. We do not simply compress text to `en → ta → en`:
that would forgive switches in the wrong place.

See the [34-case audit](docs/scenario_audit.md) for executable examples and known
failures. In particular, combined hallucination and omission can confuse lexical
alignment. **This remains a text-based proxy, not a verified acoustic detector.**

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

This is not permission to ignore invented switches. If inserted labels go `en → fr → en → fr`, only one `en → fr` event can match the reference; the other two events are FP. If they go `en → de → fr`, neither event is a direct `en → fr` switch, so both are FP and the reference switch is FN. If an endpoint word is deleted, v3 uses the nearest surviving reference word within that same language stretch. Wrong labels on surviving support still fail. A completely omitted language stretch receives no boundary credit; the search cannot cross it.

If a whole switched passage is hallucinated repeatedly, a reference switch can match only once; unmatched predicted switches are FP. Several identical passages can admit equally good text alignments. The fixed tie rule picks one deterministically; it cannot tell which copy was acoustically grounded. A long hallucination in the expected languages can still preserve the switch structure, so boundary F1 must be paired with WER/CER and hallucination diagnostics.

See [alignment and hallucination examples](docs/alignment.md) for the full rule and executable examples. No timestamps means text offset cannot tell us whether a model switched too late **in the audio**. Audio-verified reference labels connect this measure to spoken switching, but the scorer cannot recover hidden model beliefs or validate the audio by itself.

## Related work and validity

- [Wang et al., Interspeech 2019](https://www.isca-archive.org/interspeech_2019/wang19l_interspeech.html) studies language-switch detection and spurious extra switches using acoustic language posteriors. This supports keeping false-switch penalties explicit; its time-based detection task differs from our text metric.
- [HiKE, EACL 2026](https://aclanthology.org/2026.findings-eacl.33/) supplies Korean-English speech with loanword and hierarchical switch labels, illustrating why annotation conventions and language transfer need evaluation.
- [PIER, ICASSP 2025](https://arxiv.org/abs/2501.09512) evaluates errors in selected code-switched words. It motivates reporting targeted metrics beside overall WER; it is not this event-matching rule.
- [Benchmarking Evaluation Metrics for Code-Switching ASR, SLT 2022/2023](https://arxiv.org/abs/2211.16319) investigates agreement with human judgments and shows why transcript conventions matter.
- [MERLIon CCS, Interspeech 2023](https://www.isca-archive.org/interspeech_2023/chua23_interspeech.pdf) evaluates language identification/diarization; [DISPLACE 2024](https://displace2024.github.io/) specifies time-based language diarization evaluation. SwitchF1 instead evaluates labeled text.
- [The 2016 code-switched language-identification shared task](https://aclanthology.org/W16-5805/) documents ambiguous, mixed and other token categories. Language annotation policy is part of the benchmark.

These precedents rule out an unsupported claim that language-switch evaluation has never been formalized. Our contribution is the particular reproducible, directed, aligned boundary definition, optional lexical anchoring and this reusable implementation. See [validation requirements](docs/validation.md) before making broad empirical claims.

## Reproducibility

Version `0.4.0`: primary specification `switchf1-boundary-v3`; optional insertion-only `boundary_v2` specification `switchf1-boundary-v2`; optional exact-position specification `switchf1-boundary-v1`; optional anchored specification `ase-f1-v1`. CLI output includes the package version, input hash, counts, per-event matches, and alignment traces. Record the Git commit, annotation policy, tokenizer, reference/prediction hashes, and scoring mode with published results. The software is MIT licensed; the license does not grant rights to external evaluation data.
