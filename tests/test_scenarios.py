"""Semantic cases and independently derived pure-deletion/run-survival oracle."""
import itertools
import json
from pathlib import Path
import unittest
from switchf1 import Token, score_utterance


class ScenarioTests(unittest.TestCase):
    def test_predeclared_scenarios(self):
        path=Path(__file__).resolve().parents[1]/'examples/adversarial.jsonl'
        for line in path.read_text().splitlines():
            case=json.loads(line)
            with self.subTest(case=case['id']):
                result=score_utterance(case['reference'],case['hypothesis'])
                self.assertEqual({k:result[k] for k in ('tp','fp','fn')},case['expected'])

    def test_exhaustive_pure_deletions_against_run_survival(self):
        # Unique words give unambiguous subsequence alignment. Expectations come
        # from survival of ORIGINAL adjacent runs, not the scorer's intervals.
        for languages in itertools.product(('en','ta','fr'),repeat=5):
            ref=[Token('word'+str(i),lang) for i,lang in enumerate(languages)]
            runs=[]
            for i,lang in enumerate(languages):
                if not runs or lang!=languages[runs[-1][-1]]:runs.append([])
                runs[-1].append(i)
            for keep in itertools.product((False,True),repeat=5):
                hyp=[t for t,k in zip(ref,keep) if k]
                surviving=[any(keep[i] for i in run) for run in runs]
                tp=sum(a and b for a,b in zip(surviving,surviving[1:]))
                nh=sum(a.lang!=b.lang for a,b in zip(hyp,hyp[1:]))
                result=score_utterance(ref,hyp)
                self.assertEqual((result['tp'],result['fp'],result['fn']),
                                 (tp,nh-tp,len(runs)-1-tp),(languages,keep))
                self.assertEqual(len(set(j for _,j in result['matches'])),tp)

    def test_wrong_survivor_never_skipped_to_find_better_label(self):
        ref=[Token('a','en'),Token('b','en'),Token('c','en'),Token('d','ta')]
        hyp=[ref[0],Token('b','ta'),ref[-1]]
        self.assertEqual(score_utterance(ref,hyp)['tp'],0)

    def test_hallucination_masking_deletions_is_explicit_limit(self):
        ref=[Token('a','en'),Token('b','en'),Token('c','ta'),Token('d','ta')]
        hyp=[ref[0]]+[Token('noise','en')]*128+[ref[-1]]
        result=score_utterance(ref,hyp)
        self.assertEqual((result['tp'],result['fp'],result['fn']),(0,1,1))
        self.assertEqual(result['matches_across_deletions'],0)

    def test_v3_reduces_to_v2_without_deletions(self):
        ref=[Token('a','en'),Token('b','ta'),Token('c','en')]
        for langs in itertools.product(('en','ta','fr',None),repeat=4):
            hyp=[Token('a',langs[0]),Token('extra',langs[1]),
                 Token('b',langs[2]),Token('c',langs[3])]
            new=score_utterance(ref,hyp)
            old=score_utterance(ref,hyp,mode='boundary_v2')
            self.assertEqual(new['matches'],old['matches'])

    def test_language_renaming_including_no_english(self):
        mapping={'en':'es','ta':'fr','fr':'de','es':'it',None:None}
        path=Path(__file__).resolve().parents[1]/'examples/adversarial.jsonl'
        for line in path.read_text().splitlines():
            case=json.loads(line)
            def rename(tokens):return [Token(t['text'],mapping[t['lang']]) for t in tokens]
            renamed=score_utterance(rename(case['reference']),rename(case['hypothesis']))
            self.assertEqual({k:renamed[k] for k in ('tp','fp','fn')},case['expected'])

if __name__=='__main__':unittest.main()
