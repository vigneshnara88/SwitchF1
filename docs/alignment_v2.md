# Alignment, hallucinations, and boundary-only F1 v2

Archived 0.3.0 specification. Its `boundary` mode is now available as
`boundary_v2`; the current default is [v3](method.md).

SwitchF1 compares **corresponding text positions after alignment**, not the
original word numbers. A language change at hypothesis word 103 can match a
reference change at word 3 if the previous 100 hypothesis words are insertions.
No maximum raw offset is imposed.

## How correspondence is established

Normalize token text with NFC and lowercase. Given reference tokens R and
hypothesis tokens H, compute the word edit-distance table:

$$
D(i,j)=\min\{D(i-1,j)+1,\ D(i,j-1)+1,\ D(i-1,j-1)+[\nu(r_i)\ne\nu(h_j)]\}.
$$

The boundary conditions are D(i,0)=i and D(0,j)=j. Trace back a minimum-cost path;
ties prefer diagonal, deletion, insertion. This produces shared columns with a
reference token, a hypothesis token, or a gap. Language labels do not enter the
distance calculation or tie-breaking.

For each sequence, identify successive non-neutral tokens whose language labels differ. Count **all** such directed events before matching.

For each reference A → B boundary, use the alignment columns of its two endpoint tokens as an interval. Both endpoints must align to hypothesis tokens labeled A and B respectively. Match at most one actual A → B hypothesis event wholly inside that interval. This allows same-language insertions on either side without treating the switch as wrong. It does not cross other language-bearing reference words or award credit when endpoint labels are wrong/deleted.

If several A → B events occur inside that interval, choose the earliest and count all unmatched events as FP. Reference intervals have disjoint interiors, so one predicted event cannot support two reference events. The full eligibility formulas are in [method.md](method.md). WER/CER continue to count every word error; no repetition is removed.

The optional `boundary_exact` mode instead requires both event endpoint columns to be equal. The optional `anchored` mode also requires the corresponding words to be equal. These preserve the earlier scoring definitions for comparison.

## Executable examples

```python
from switchf1 import Token, score_utterance

reference = [Token("we", "en"), Token("say", "en"),
             Token("bonjour", "fr"), Token("maintenant", "fr")]

# A large offset in raw word numbers is absorbed by insertion gaps.
shifted = [Token("blah", "en")] * 100 + reference
score = score_utterance(reference, shifted, mode="boundary")
assert (score["tp"], score["fp"], score["fn"]) == (1, 0, 0)
assert score["ref_events"][0]["token_indices"] == [1, 2]
assert score["hyp_events"][0]["token_indices"] == [101, 102]
assert score["ref_events"][0]["position"] == score["hyp_events"][0]["position"]

# Same-language insertions at the boundary still preserve the switch in v2.
adjacent = reference[:2] + [Token("blah", "en")] * 100 + reference[2:]
score = score_utterance(reference, adjacent)
assert (score["tp"], score["fp"], score["fn"]) == (1, 0, 0)
# The old exact-position diagnostic intentionally differs.
exact = score_utterance(reference, adjacent, mode="boundary_exact")
assert (exact["tp"], exact["fp"], exact["fn"]) == (0, 1, 1)

# Destination-language insertions also preserve the directed transition.
destination = reference[:2] + [Token("salut", "fr")] * 100 + reference[2:]
assert score_utterance(reference, destination)["f1"] == 1.0

# Extra oscillations are counted, not removed before evaluating switches.
oscillating = reference[:2] + [Token("salut", "fr"), Token("extra", "en")] + reference[2:]
score = score_utterance(reference, oscillating)
assert (score["tp"], score["fp"], score["fn"]) == (1, 2, 0)

# A third-language detour does not count as a direct English → French event.
detour = reference[:2] + [Token("hallo", "de")] + reference[2:]
score = score_utterance(reference, detour)
assert (score["tp"], score["fp"], score["fn"]) == (0, 2, 1)

# Repeated passages cannot repeatedly claim the same reference event.
score = score_utterance(reference, reference * 3)
assert (score["tp"], score["fp"], score["fn"]) == (1, 4, 0)
assert score["f1"] == 1 / 3
```

The prefix example has 100 word insertions and 2500% WER despite perfect boundary
F1. The score intentionally evaluates switch structure, not all transcript errors.
For a pure language detector evaluated on a fixed transcript, instead supply the
same words on both sides and compare reference versus predicted token labels.

## What exact alignment cannot establish

Repeated words can admit several equally optimal alignments. In the repeated
passage example, the current tie rule aligns the reference to the last identical
copy. Choosing the first copy would not establish which one corresponds to the
audio either. The evaluator exposes alignment/event traces and counts every extra
event, but does not claim acoustic provenance.

If a model produces a correct switch far later **in audio time**, text alone cannot
measure that delay. No timing claim is made. A reference transcript and its
language labels must be checked against audio to evaluate actual spoken switches.
When evaluating switching within a speaker, split different speakers' streams;
an English-speaking person followed by a French-speaking person is a different
phenomenon from one person changing languages.

## Limits of the insertion-aware rule

- **Expected-language hallucinations:** A long invented span in the expected
  languages may preserve a supported boundary and earn switch credit. That does
  not make the invented words correct. WER/CER and hallucination diagnostics are
  required alongside F1.
- **Deletion:** If either reference endpoint is deleted, v2 cannot establish the
  required endpoint support. A human may still hear/preserve a switch nearby;
  this conservative failure remains explicit.
- **Mislabeled endpoints:** A matching-direction event inside the interval cannot
  rescue wrong labels on the aligned endpoints. This prevents an invented switch
  from masking an incorrectly represented reference transition.
- **Reference neutrality:** A reference interval may contain explicitly neutral
  words. Their policy must be fixed; labeling real language-bearing content
  neutral can hide distinctions and invalidate the interpretation.
- **Repeated text:** Equal-cost edit paths can align to different repeated copies.
  Do not pick the path that maximizes F1. The deterministic lexical tie rule
  cannot establish which copy was acoustically grounded.

The v2 rule was specified to address semantic counterexamples before rescoring the
existing models. This is still development of a proposed metric, not an
independent validation study. Evaluate it against blinded bilingual switch
judgments on held-out audio/transcripts, alongside the exact-position diagnostic,
before claiming robust human agreement across languages. See [validation.md](validation.md).
