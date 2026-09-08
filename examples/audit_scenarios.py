"""Run public semantic fixtures, compare modes, and optionally write Markdown."""
import argparse
import json
from pathlib import Path
from switchf1 import score_utterance, SPECIFICATIONS


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--markdown',type=Path)
    args=parser.parse_args()
    cases=[json.loads(line) for line in Path(__file__).with_name('adversarial.jsonl').read_text().splitlines()]
    lines=['# SwitchF1 v3 semantic scenario audit','',
        'These are constructed examples, not an empirical speech benchmark. Expected',
        'counts encode the declared rule. Two explicitly marked cases retain a gap',
        'between a plausible human judgment and lexical-alignment behavior; regression',
        'success does not resolve that validity limitation.','',
        'Reproduce from the installed repository with:', '',
        '```bash','python examples/audit_scenarios.py --markdown docs/scenario_audit.md','```','',
        'All language labels are explicit, including Romanized Tamil. Higher F1 is better.',
        'TP = matched reference/output event; FP = unmatched output event; FN = missed reference event.',
        'F1 = 2 TP / (2 TP + FP + FN); no events on either side gives undefined F1.','',
        '| Case | v2 TP/FP/FN | v3 TP/FP/FN | v3 F1 | Explanation |',
        '|---|---|---|---:|---|']
    for case in cases:
        old=score_utterance(case['reference'],case['hypothesis'],mode='boundary_v2')
        new=score_utterance(case['reference'],case['hypothesis'])
        assert {k:new[k] for k in ('tp','fp','fn')}==case['expected'],case['id']
        counts=lambda x:'/'.join(str(x[k]) for k in ('tp','fp','fn'))
        f1='undefined' if new['f1'] is None else f"{new['f1']*100:.1f}%"
        reason=case['reason']
        if 'desired_counts' in case:reason+=' **Known limitation; desired '+counts(case['desired_counts'])+'.**'
        lines.append(f"| {case['id']} | {counts(old)} | {counts(new)} | {f1} | {reason} |")
    lines += ['',
        'The complete token sequences and labels are in [adversarial.jsonl](../examples/adversarial.jsonl).',
        'Tests also enumerate 7,776 pure-deletion cases using an independent original-run',
        'survival oracle, 256 v3/v2 equivalence cases without deletions, 121 inserted',
        'language paths and 64 identical-text label combinations. Language-renaming',
        'checks rerun all 34 scenarios, including shared-script and non-English pairs.','',
        '**Decision:** use v3 as the experimental text switch-preservation companion,',
        'with precision, recall, directional support, no-switch false alarms, and WER/CER.',
        'Keep v2 as a sensitivity result. Do not replace positional matching with mere',
        'language-sequence/count agreement: it would reward misplaced boundaries.','',
        'This suite establishes reproducible behavior on declared examples, not that',
        'the metric recognizes spoken switches perfectly. [Independent audio and',
        'bilingual validation](validation.md) is still required.']
    report='\n'.join(lines)+'\n'
    if args.markdown:args.markdown.write_text(report)
    else:print(report,end='')
    print(f"Checked {len(cases)} scenarios under {SPECIFICATIONS['boundary']}; two documented alignment limitations.")


if __name__=='__main__':main()
