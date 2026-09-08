# SwitchF1 v3 semantic scenario audit

These are constructed examples, not an empirical speech benchmark. Expected
counts encode the declared rule. Two explicitly marked cases retain a gap
between a plausible human judgment and lexical-alignment behavior; regression
success does not resolve that validity limitation.

Reproduce from the installed repository with:

```bash
python examples/audit_scenarios.py --markdown docs/scenario_audit.md
```

All language labels are explicit, including Romanized Tamil. Higher F1 is better.
TP = matched reference/output event; FP = unmatched output event; FN = missed reference event.
F1 = 2 TP / (2 TP + FP + FN); no events on either side gives undefined F1.

| Case | v2 TP/FP/FN | v3 TP/FP/FN | v3 F1 | Explanation |
|---|---|---|---:|---|
| user_missing_is_sam | 0/1/1 | 1/0/0 | 100.0% | Omitting English words preserves the English-to-Tamil transition. |
| user_misplaced_tamil | 0/2/1 | 0/2/1 | 0.0% | Tamil appears inside the aligned English span and adds a return to English. |
| wrong_words_correct_languages | 1/0/0 | 1/0/0 | 100.0% | Substitutions with correct languages still preserve the boundary. |
| all_words_wrong | 1/0/0 | 1/0/0 | 100.0% | Even all-wrong words can preserve aligned language structure; not acoustic proof. |
| delete_first_tamil_word | 0/1/1 | 1/0/0 | 100.0% | A surviving Tamil word supports the destination run. |
| delete_both_boundary_words | 0/1/1 | 1/0/0 | 100.0% | Both adjacent language stretches survive despite endpoint deletions. |
| two_correct | 2/0/0 | 2/0/0 | 100.0% | English-to-Tamil and Tamil-to-English are separate events. |
| two_correct_with_deletions | 0/2/2 | 2/0/0 | 100.0% | Each original language run survives; both transitions remain. |
| middle_single_survivor | 1/1/1 | 2/0/0 | 100.0% | One surviving middle token can support two distinct events. |
| delete_entire_middle_run | 0/0/2 | 0/0/2 | 0.0% | The entire Tamil stretch disappears; both switches are missed. |
| translate_middle_run | 0/0/2 | 0/0/2 | 0.0% | English rendering of Tamil removes both language changes. |
| delete_final_run | 1/0/1 | 1/0/1 | 66.7% | First switch preserved, return to English missed. |
| delete_initial_run | 1/0/1 | 1/0/1 | 66.7% | First switch missed, return to English preserved. |
| extra_tail_switch | 2/1/0 | 2/1/0 | 80.0% | An invented final switch lowers precision. |
| same_tamil_loop | 2/0/0 | 2/0/0 | 100.0% | Repetition within one language adds words but no new transition. |
| extra_oscillation | 2/2/0 | 2/2/0 | 66.7% | Inserted Tamil-English detour adds two unmatched switches. |
| duplicate_two_switch_passage | 2/4/0 | 2/4/0 | 50.0% | Two reference switches can match only once each across repeated copies. |
| empty_output | 0/0/2 | 0/0/2 | 0.0% | All reference events remain false negatives. |
| empty_reference | 0/1/0 | 0/1/0 | 0.0% | Every invented transition counts even on an empty reference. |
| monolingual_false_island | 0/2/0 | 0/2/0 | 0.0% | Two spurious transitions on a no-switch reference. |
| wrong_direction | 0/1/1 | 0/1/1 | 0.0% | Language direction is part of the event identity. |
| third_language_detour | 0/2/1 | 0/2/1 | 0.0% | English-French-Tamil has no direct English-Tamil event. |
| three_languages_partial_deletion | 0/2/2 | 2/0/0 | 100.0% | The same survival rule works with three languages. |
| third_language_run_deleted | 0/1/2 | 0/1/2 | 0.0% | Do not invent an English-Tamil reference event after deleting French. |
| no_english_pair | 0/1/1 | 1/0/0 | 100.0% | Shared-script languages without English use the same rule. |
| changed_neutral_alignment_limit | 0/1/1 | 0/1/1 | 0.0% | Known limitation: changed punctuation aligns as a substitution for a deleted Tamil word; the conservative rule rejects the boundary. **Known limitation; desired 1/0/0.** |
| surviving_wrong_label_blocks_rescue | 0/1/1 | 0/1/1 | 0.0% | After sam is deleted, the nearest survivor has the wrong label; do not search past it. |
| same_count_early_boundary | 0/1/1 | 0/1/1 | 0.0% | Correct switch count and direction at the wrong surviving word is insufficient. |
| same_count_late_boundary | 0/1/1 | 0/1/1 | 0.0% | A late boundary is rejected when its aligned endpoint language is wrong. |
| five_switches | 5/0/0 | 5/0/0 | 100.0% | All five directed events count independently. |
| five_switches_missing_island | 2/1/3 | 2/1/3 | 50.0% | Two complete adjacent runs disappear: the middle predicted transition spans three reference boundaries and cannot be assigned locally; only the two outer events match. |
| no_switches | 0/0/0 | 0/0/0 | undefined | Switch F1 is undefined, not perfect, when neither side switches. |
| neutral_deleted_bridge | 0/1/1 | 1/0/0 | 100.0% | Unchanged neutral punctuation and within-run deletions retain the switch. |
| hallucination_masks_deletions_limit | 0/1/1 | 0/1/1 | 0.0% | Known limitation: some hallucinated English words substitute for deleted reference tokens; the Tamil endpoint has a surviving wrong-language alignment. **Known limitation; desired 1/0/0.** |

The complete token sequences and labels are in [adversarial.jsonl](../examples/adversarial.jsonl).
Tests also enumerate 7,776 pure-deletion cases using an independent original-run
survival oracle, 256 v3/v2 equivalence cases without deletions, 121 inserted
language paths and 64 identical-text label combinations. Language-renaming
checks rerun all 34 scenarios, including shared-script and non-English pairs.

**Decision:** use v3 as the experimental text switch-preservation companion,
with precision, recall, directional support, no-switch false alarms, and WER/CER.
Keep v2 as a sensitivity result. Do not replace positional matching with mere
language-sequence/count agreement: it would reward misplaced boundaries.

This suite establishes reproducible behavior on declared examples, not that
the metric recognizes spoken switches perfectly. [Independent audio and
bilingual validation](validation.md) is still required.

## Every example, with its complete labeled text

Expand any case below. Each `word/language` entry labels one token;
`neutral` denotes an explicitly neutral token and `(empty)` means no tokens.
Long loops are shown in full so the displayed input is reproducible.

To inspect every alignment column and matched event as JSON:

```bash
switchf1 examples/adversarial.jsonl --output results/adversarial.json
```

<details>
<summary>user_missing_is_sam — F1 100.0%</summary>

```text
Reference: hello/en my/en name/en is/en sam/en ennaku/ta
Output:    hello/en my/en name/en ennaku/ta
```

Reference switches: **1**. Output switches: **1**.
Correct: **1**; extra: **0**; missed: **0**.

**Calculation:** 2 × 1 / (2 × 1 + 0 + 0) = 100.0%.

**Explanation:** Omitting English words preserves the English-to-Tamil transition.

</details>

<details>
<summary>user_misplaced_tamil — F1 0.0%</summary>

```text
Reference: hello/en my/en name/en is/en sam/en ennaku/ta
Output:    hello/en ennaku/ta name/en sam/en
```

Reference switches: **1**. Output switches: **2**.
Correct: **0**; extra: **2**; missed: **1**.

**Calculation:** 2 × 0 / (2 × 0 + 2 + 1) = 0.0%.

**Explanation:** Tamil appears inside the aligned English span and adds a return to English.

</details>

<details>
<summary>wrong_words_correct_languages — F1 100.0%</summary>

```text
Reference: hello/en my/en name/en is/en sam/en ennaku/ta
Output:    hello/en my/en name/en is/en john/en unakku/ta
```

Reference switches: **1**. Output switches: **1**.
Correct: **1**; extra: **0**; missed: **0**.

**Calculation:** 2 × 1 / (2 × 1 + 0 + 0) = 100.0%.

**Explanation:** Substitutions with correct languages still preserve the boundary.

</details>

<details>
<summary>all_words_wrong — F1 100.0%</summary>

```text
Reference: one/en two/en மூன்று/ta நான்கு/ta
Output:    alpha/en beta/en ஐந்து/ta ஆறு/ta
```

Reference switches: **1**. Output switches: **1**.
Correct: **1**; extra: **0**; missed: **0**.

**Calculation:** 2 × 1 / (2 × 1 + 0 + 0) = 100.0%.

**Explanation:** Even all-wrong words can preserve aligned language structure; not acoustic proof.

</details>

<details>
<summary>delete_first_tamil_word — F1 100.0%</summary>

```text
Reference: hello/en ennaku/ta venum/ta
Output:    hello/en venum/ta
```

Reference switches: **1**. Output switches: **1**.
Correct: **1**; extra: **0**; missed: **0**.

**Calculation:** 2 × 1 / (2 × 1 + 0 + 0) = 100.0%.

**Explanation:** A surviving Tamil word supports the destination run.

</details>

<details>
<summary>delete_both_boundary_words — F1 100.0%</summary>

```text
Reference: hello/en sam/en ennaku/ta venum/ta
Output:    hello/en venum/ta
```

Reference switches: **1**. Output switches: **1**.
Correct: **1**; extra: **0**; missed: **0**.

**Calculation:** 2 × 1 / (2 × 1 + 0 + 0) = 100.0%.

**Explanation:** Both adjacent language stretches survive despite endpoint deletions.

</details>

<details>
<summary>two_correct — F1 100.0%</summary>

```text
Reference: hello/en friend/en ennaku/ta venum/ta coffee/en today/en
Output:    hello/en friend/en ennaku/ta venum/ta coffee/en today/en
```

Reference switches: **2**. Output switches: **2**.
Correct: **2**; extra: **0**; missed: **0**.

**Calculation:** 2 × 2 / (2 × 2 + 0 + 0) = 100.0%.

**Explanation:** English-to-Tamil and Tamil-to-English are separate events.

</details>

<details>
<summary>two_correct_with_deletions — F1 100.0%</summary>

```text
Reference: hello/en friend/en ennaku/ta venum/ta coffee/en today/en
Output:    hello/en venum/ta today/en
```

Reference switches: **2**. Output switches: **2**.
Correct: **2**; extra: **0**; missed: **0**.

**Calculation:** 2 × 2 / (2 × 2 + 0 + 0) = 100.0%.

**Explanation:** Each original language run survives; both transitions remain.

</details>

<details>
<summary>middle_single_survivor — F1 100.0%</summary>

```text
Reference: hello/en friend/en ennaku/ta venum/ta coffee/en today/en
Output:    hello/en friend/en venum/ta coffee/en today/en
```

Reference switches: **2**. Output switches: **2**.
Correct: **2**; extra: **0**; missed: **0**.

**Calculation:** 2 × 2 / (2 × 2 + 0 + 0) = 100.0%.

**Explanation:** One surviving middle token can support two distinct events.

</details>

<details>
<summary>delete_entire_middle_run — F1 0.0%</summary>

```text
Reference: hello/en friend/en ennaku/ta venum/ta coffee/en today/en
Output:    hello/en friend/en coffee/en today/en
```

Reference switches: **2**. Output switches: **0**.
Correct: **0**; extra: **0**; missed: **2**.

**Calculation:** 2 × 0 / (2 × 0 + 0 + 2) = 0.0%.

**Explanation:** The entire Tamil stretch disappears; both switches are missed.

</details>

<details>
<summary>translate_middle_run — F1 0.0%</summary>

```text
Reference: hello/en friend/en ennaku/ta venum/ta coffee/en today/en
Output:    hello/en friend/en i/en want/en coffee/en today/en
```

Reference switches: **2**. Output switches: **0**.
Correct: **0**; extra: **0**; missed: **2**.

**Calculation:** 2 × 0 / (2 × 0 + 0 + 2) = 0.0%.

**Explanation:** English rendering of Tamil removes both language changes.

</details>

<details>
<summary>delete_final_run — F1 66.7%</summary>

```text
Reference: hello/en friend/en ennaku/ta venum/ta coffee/en today/en
Output:    hello/en friend/en ennaku/ta venum/ta
```

Reference switches: **2**. Output switches: **1**.
Correct: **1**; extra: **0**; missed: **1**.

**Calculation:** 2 × 1 / (2 × 1 + 0 + 1) = 66.7%.

**Explanation:** First switch preserved, return to English missed.

</details>

<details>
<summary>delete_initial_run — F1 66.7%</summary>

```text
Reference: hello/en friend/en ennaku/ta venum/ta coffee/en today/en
Output:    ennaku/ta venum/ta coffee/en today/en
```

Reference switches: **2**. Output switches: **1**.
Correct: **1**; extra: **0**; missed: **1**.

**Calculation:** 2 × 1 / (2 × 1 + 0 + 1) = 66.7%.

**Explanation:** First switch missed, return to English preserved.

</details>

<details>
<summary>extra_tail_switch — F1 80.0%</summary>

```text
Reference: hello/en friend/en ennaku/ta venum/ta coffee/en today/en
Output:    hello/en friend/en ennaku/ta venum/ta coffee/en today/en nandri/ta
```

Reference switches: **2**. Output switches: **3**.
Correct: **2**; extra: **1**; missed: **0**.

**Calculation:** 2 × 2 / (2 × 2 + 1 + 0) = 80.0%.

**Explanation:** An invented final switch lowers precision.

</details>

<details>
<summary>same_tamil_loop — F1 100.0%</summary>

```text
Reference: hello/en friend/en ennaku/ta venum/ta coffee/en today/en
Output:    hello/en friend/en ennaku/ta venum/ta venum/ta venum/ta coffee/en today/en
```

Reference switches: **2**. Output switches: **2**.
Correct: **2**; extra: **0**; missed: **0**.

**Calculation:** 2 × 2 / (2 × 2 + 0 + 0) = 100.0%.

**Explanation:** Repetition within one language adds words but no new transition.

</details>

<details>
<summary>extra_oscillation — F1 66.7%</summary>

```text
Reference: hello/en friend/en ennaku/ta venum/ta coffee/en today/en
Output:    hello/en friend/en extra/ta noise/en ennaku/ta venum/ta coffee/en today/en
```

Reference switches: **2**. Output switches: **4**.
Correct: **2**; extra: **2**; missed: **0**.

**Calculation:** 2 × 2 / (2 × 2 + 2 + 0) = 66.7%.

**Explanation:** Inserted Tamil-English detour adds two unmatched switches.

</details>

<details>
<summary>duplicate_two_switch_passage — F1 50.0%</summary>

```text
Reference: hello/en friend/en ennaku/ta venum/ta coffee/en today/en
Output:    hello/en friend/en ennaku/ta venum/ta coffee/en today/en hello/en friend/en ennaku/ta venum/ta coffee/en today/en hello/en friend/en ennaku/ta venum/ta coffee/en today/en
```

Reference switches: **2**. Output switches: **6**.
Correct: **2**; extra: **4**; missed: **0**.

**Calculation:** 2 × 2 / (2 × 2 + 4 + 0) = 50.0%.

**Explanation:** Two reference switches can match only once each across repeated copies.

</details>

<details>
<summary>empty_output — F1 0.0%</summary>

```text
Reference: hello/en friend/en ennaku/ta venum/ta coffee/en today/en
Output:    (empty)
```

Reference switches: **2**. Output switches: **0**.
Correct: **0**; extra: **0**; missed: **2**.

**Calculation:** 2 × 0 / (2 × 0 + 0 + 2) = 0.0%.

**Explanation:** All reference events remain false negatives.

</details>

<details>
<summary>empty_reference — F1 0.0%</summary>

```text
Reference: (empty)
Output:    hello/en vanakkam/ta
```

Reference switches: **0**. Output switches: **1**.
Correct: **0**; extra: **1**; missed: **0**.

**Calculation:** 2 × 0 / (2 × 0 + 1 + 0) = 0.0%.

**Explanation:** Every invented transition counts even on an empty reference.

</details>

<details>
<summary>monolingual_false_island — F1 0.0%</summary>

```text
Reference: hello/en friend/en today/en
Output:    hello/en friend/ta today/en
```

Reference switches: **0**. Output switches: **2**.
Correct: **0**; extra: **2**; missed: **0**.

**Calculation:** 2 × 0 / (2 × 0 + 2 + 0) = 0.0%.

**Explanation:** Two spurious transitions on a no-switch reference.

</details>

<details>
<summary>wrong_direction — F1 0.0%</summary>

```text
Reference: hello/en ennaku/ta
Output:    hello/ta ennaku/en
```

Reference switches: **1**. Output switches: **1**.
Correct: **0**; extra: **1**; missed: **1**.

**Calculation:** 2 × 0 / (2 × 0 + 1 + 1) = 0.0%.

**Explanation:** Language direction is part of the event identity.

</details>

<details>
<summary>third_language_detour — F1 0.0%</summary>

```text
Reference: hello/en ennaku/ta
Output:    hello/en bonjour/fr ennaku/ta
```

Reference switches: **1**. Output switches: **2**.
Correct: **0**; extra: **2**; missed: **1**.

**Calculation:** 2 × 0 / (2 × 0 + 2 + 1) = 0.0%.

**Explanation:** English-French-Tamil has no direct English-Tamil event.

</details>

<details>
<summary>three_languages_partial_deletion — F1 100.0%</summary>

```text
Reference: hello/en friend/en bonjour/fr ami/fr vanakkam/ta nanba/ta
Output:    hello/en ami/fr nanba/ta
```

Reference switches: **2**. Output switches: **2**.
Correct: **2**; extra: **0**; missed: **0**.

**Calculation:** 2 × 2 / (2 × 2 + 0 + 0) = 100.0%.

**Explanation:** The same survival rule works with three languages.

</details>

<details>
<summary>third_language_run_deleted — F1 0.0%</summary>

```text
Reference: hello/en bonjour/fr vanakkam/ta
Output:    hello/en vanakkam/ta
```

Reference switches: **2**. Output switches: **1**.
Correct: **0**; extra: **1**; missed: **2**.

**Calculation:** 2 × 0 / (2 × 0 + 1 + 2) = 0.0%.

**Explanation:** Do not invent an English-Tamil reference event after deleting French.

</details>

<details>
<summary>no_english_pair — F1 100.0%</summary>

```text
Reference: bonjour/fr ami/fr hola/es amigo/es
Output:    bonjour/fr amigo/es
```

Reference switches: **1**. Output switches: **1**.
Correct: **1**; extra: **0**; missed: **0**.

**Calculation:** 2 × 1 / (2 × 1 + 0 + 0) = 100.0%.

**Explanation:** Shared-script languages without English use the same rule.

</details>

<details>
<summary>changed_neutral_alignment_limit — F1 0.0%</summary>

```text
Reference: hello/en friend/en ,/neutral ennaku/ta venum/ta
Output:    hello/en ./neutral venum/ta
```

Reference switches: **1**. Output switches: **1**.
Correct: **0**; extra: **1**; missed: **1**.

**Calculation:** 2 × 0 / (2 × 0 + 1 + 1) = 0.0%.

**Explanation:** Known limitation: changed punctuation aligns as a substitution for a deleted Tamil word; the conservative rule rejects the boundary. **Known limitation; desired 1/0/0.**

</details>

<details>
<summary>surviving_wrong_label_blocks_rescue — F1 0.0%</summary>

```text
Reference: hello/en friend/en sam/en ennaku/ta
Output:    hello/en friend/ta ennaku/ta
```

Reference switches: **1**. Output switches: **1**.
Correct: **0**; extra: **1**; missed: **1**.

**Calculation:** 2 × 0 / (2 × 0 + 1 + 1) = 0.0%.

**Explanation:** After sam is deleted, the nearest survivor has the wrong label; do not search past it.

</details>

<details>
<summary>same_count_early_boundary — F1 0.0%</summary>

```text
Reference: hello/en friend/en ennaku/ta venum/ta
Output:    hello/en friend/ta ennaku/ta venum/ta
```

Reference switches: **1**. Output switches: **1**.
Correct: **0**; extra: **1**; missed: **1**.

**Calculation:** 2 × 0 / (2 × 0 + 1 + 1) = 0.0%.

**Explanation:** Correct switch count and direction at the wrong surviving word is insufficient.

</details>

<details>
<summary>same_count_late_boundary — F1 0.0%</summary>

```text
Reference: hello/en friend/en ennaku/ta venum/ta
Output:    hello/en friend/en ennaku/en venum/ta
```

Reference switches: **1**. Output switches: **1**.
Correct: **0**; extra: **1**; missed: **1**.

**Calculation:** 2 × 0 / (2 × 0 + 1 + 1) = 0.0%.

**Explanation:** A late boundary is rejected when its aligned endpoint language is wrong.

</details>

<details>
<summary>five_switches — F1 100.0%</summary>

```text
Reference: a/en b/ta c/en d/ta e/en f/ta
Output:    a/en b/ta c/en d/ta e/en f/ta
```

Reference switches: **5**. Output switches: **5**.
Correct: **5**; extra: **0**; missed: **0**.

**Calculation:** 2 × 5 / (2 × 5 + 0 + 0) = 100.0%.

**Explanation:** All five directed events count independently.

</details>

<details>
<summary>five_switches_missing_island — F1 50.0%</summary>

```text
Reference: a/en b/ta c/en d/ta e/en f/ta
Output:    a/en b/ta e/en f/ta
```

Reference switches: **5**. Output switches: **3**.
Correct: **2**; extra: **1**; missed: **3**.

**Calculation:** 2 × 2 / (2 × 2 + 1 + 3) = 50.0%.

**Explanation:** Two complete adjacent runs disappear: the middle predicted transition spans three reference boundaries and cannot be assigned locally; only the two outer events match.

</details>

<details>
<summary>no_switches — F1 undefined</summary>

```text
Reference: hello/en friend/en
Output:    hi/en friend/en
```

Reference switches: **0**. Output switches: **0**.
Correct: **0**; extra: **0**; missed: **0**.

**Calculation:** undefined: neither side has a switch.

**Explanation:** Switch F1 is undefined, not perfect, when neither side switches.

</details>

<details>
<summary>neutral_deleted_bridge — F1 100.0%</summary>

```text
Reference: hello/en friend/en ,/neutral ennaku/ta venum/ta
Output:    hello/en ,/neutral venum/ta
```

Reference switches: **1**. Output switches: **1**.
Correct: **1**; extra: **0**; missed: **0**.

**Calculation:** 2 × 1 / (2 × 1 + 0 + 0) = 100.0%.

**Explanation:** Unchanged neutral punctuation and within-run deletions retain the switch.

</details>

<details>
<summary>hallucination_masks_deletions_limit — F1 0.0%</summary>

```text
Reference: a/en b/en c/ta d/ta
Output:    a/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en noise/en d/ta
```

Reference switches: **1**. Output switches: **1**.
Correct: **0**; extra: **1**; missed: **1**.

**Calculation:** 2 × 0 / (2 × 0 + 1 + 1) = 0.0%.

**Explanation:** Known limitation: some hallucinated English words substitute for deleted reference tokens; the Tamil endpoint has a surviving wrong-language alignment. **Known limitation; desired 1/0/0.**

</details>
