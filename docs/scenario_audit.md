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
