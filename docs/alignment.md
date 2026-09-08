# Alignment, hallucinations, and boundary-only F1

SwitchF1 compares **corresponding text positions after alignment**, not the
original word numbers. A language change at hypothesis word 103 can match a
reference change at word 3 if the previous 100 hypothesis words are insertions.
No maximum raw offset is imposed.

## How correspondence is established

Normalize token text with NFC and lowercase. Given reference tokens R and
hypothesis tokens H, compute the word edit-distance table:

\[
D(i,j)=\min\{D(i-1,j)+1,\ D(i,j-1)+1,\
D(i-1,j-1)+[\nu(r_i)\ne\nu(h_j)]\}.
\]

The boundary conditions are D(i,0)=i and D(0,j)=j. Trace back a minimum-cost path;
ties prefer diagonal, deletion, insertion. This produces shared columns with a
reference token, a hypothesis token, or a gap. Language labels do not enter the
distance calculation or tie-breaking.

For each sequence, identify successive non-neutral tokens whose language labels
differ. Represent each transition by

\[
(\text{left alignment column},\text{right alignment column},
\text{source language},\text{destination language}).
\]

Boundary-only true positives have all four fields equal. Words in those columns
may be substitutions. A wrong direction or different boundary pair does not match.
Each event is matched at most once. Pool TP, FP, FN, then calculate
F1 = 2TP / (2TP + FP + FN).

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

# Inserting words immediately at the switch changes its boundary pair.
adjacent = reference[:2] + [Token("blah", "en")] * 100 + reference[2:]
score = score_utterance(reference, adjacent)
assert (score["tp"], score["fp"], score["fn"]) == (0, 1, 1)

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
measure that delay. No timing claim is made. If it inserts words directly beside a
boundary, the exact-pair rule can be harsher than a human preservation judgment.
This is an unresolved construct-validity limitation; deterministic unit tests do
not establish that it matches human judgments.

## Possible future tolerance study, not part of v1

An insertion-tolerant event matcher could project each predicted boundary onto a
reference gap interval, then match directed events one-to-one within a predeclared
tolerance. It must define how deletions, wholly inserted switches, uncertain
alignments and repeated passages are treated. Simply removing all inserted words
before counting switches would hide hallucinated false positives.

Compare such a separately named variant with v1 on independently annotated
development examples. Freeze tolerance, tie rules, and labels before held-out
evaluation. Do not select the alignment or tolerance that gives a preferred model
the highest F1. Version 0.2.0 implements the exact rule above; it implements no
insertion tolerance or reference-assisted selection between repeated copies.
