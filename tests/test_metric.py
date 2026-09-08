import copy
import json
import itertools
from pathlib import Path
import unittest
from switchf1 import Token,score_utterance,evaluate,aggregate

class MetricTests(unittest.TestCase):
    def setUp(self):self.ref=[Token('hello','en'),Token('bonjour','fr')]
    def test_perfect(self):self.assertEqual(score_utterance(self.ref,self.ref)['f1'],1)
    def test_same_script_different_languages(self):self.assertEqual(score_utterance(self.ref,self.ref)['tp'],1)
    def test_reversed_direction(self):
        r=score_utterance(self.ref,[Token('hello','fr'),Token('bonjour','en')])
        self.assertEqual((r['tp'],r['fp'],r['fn']),(0,1,1))
    def test_wrong_anchors_do_not_count(self):
        wrong=[Token('goodbye','en'),Token('salut','fr')]
        self.assertEqual(score_utterance(self.ref,wrong,mode='anchored')['f1'],0)
        self.assertEqual(score_utterance(self.ref,wrong)['f1'],1)
    def test_one_wrong_anchor_fails(self):
        self.assertEqual(score_utterance(self.ref,[Token('goodbye','en'),self.ref[1]],mode='anchored')['tp'],0)
    def test_inserted_switch(self):
        r=score_utterance(self.ref,self.ref+[Token('again','en')])
        self.assertEqual((r['tp'],r['fp'],r['fn']),(1,1,0))
    def test_missed_switch(self):self.assertEqual(score_utterance(self.ref,[])['fn'],1)
    def test_monolingual_false_switch(self):
        r=score_utterance([Token('hello','en')],self.ref)
        self.assertEqual((r['fp'],r['false_switch_on_no_switch']),(1,True))
    def test_no_events_is_undefined(self):
        r=score_utterance([Token('hello','en')],[Token('salut','fr')])
        self.assertIsNone(r['f1']);self.assertFalse(r['language_presence_exact'])
    def test_repeated_switch_spam_is_not_perfect(self):
        r=score_utterance(self.ref,self.ref*5)
        self.assertEqual(r['tp'],1);self.assertLess(r['f1'],1)
    def test_neutral_punctuation_bridged(self):
        h=[self.ref[0],Token(',',None),self.ref[1]]
        self.assertEqual(score_utterance(self.ref,h)['f1'],1)
    def test_unknown_hypothesis_cannot_hide_false_switch(self):
        with self.assertRaises(ValueError):
            score_utterance(self.ref,self.ref+[Token('again','und')])
    def test_unknown_reference_fails(self):
        with self.assertRaises(ValueError):score_utterance([Token('x','und')],[])
    def test_unicode_marks_preserved(self):
        r=[Token('கி','ta'),Token('hello','en')]
        self.assertEqual(score_utterance(r,[Token('கீ','ta'),Token('hello','en')],mode='anchored')['tp'],0)
    def test_nfc_equivalence(self):
        r=[Token('café','fr'),Token('hello','en')]
        self.assertEqual(score_utterance(r,[Token('cafe\u0301','fr'),Token('HELLO','en')])['tp'],1)
    def test_relabel_invariance(self):
        mapping={'en':'x','fr':'y'}
        def relabel(ts):return [Token(t.text,mapping[t.lang]) for t in ts]
        h=self.ref+[Token('again','en')]
        self.assertEqual(score_utterance(self.ref,h)['f1'],score_utterance(relabel(self.ref),relabel(h))['f1'])
    def test_three_languages(self):
        r=self.ref+[Token('hallo','de')];self.assertEqual(score_utterance(r,r)['tp'],2)
    def test_same_count_wrong_location(self):
        r=[Token('hello','en'),Token('friend','en'),Token('bonjour','fr'),Token('ami','fr')]
        h=[Token('hello','en'),Token('friend','fr'),Token('bonjour','fr'),Token('ami','fr')]
        result=score_utterance(r,h)
        self.assertEqual((result['reference_events'],result['hypothesis_events'],result['tp']),(1,1,0))
    def test_word_error_away_from_anchors_does_not_remove_switch(self):
        r=[Token('start','en'),*self.ref,Token('fin','fr')]
        h=[Token('begin','en'),*self.ref,Token('fin','fr')]
        self.assertEqual(score_utterance(r,h)['tp'],1)
    def test_alignment_does_not_use_language_labels(self):
        h=[Token('hello','fr'),Token('bonjour','en')]
        self.assertEqual(score_utterance(self.ref,self.ref)['alignment'],score_utterance(self.ref,h)['alignment'])
    def test_micro_not_mean(self):
        a=score_utterance(self.ref,self.ref);b=score_utterance([Token('hi','en')],[Token('hi','en'),Token('salut','fr')])
        self.assertAlmostEqual(aggregate([a,b])['f1'],2/3)
    def test_cannot_mix_modes(self):
        with self.assertRaises(ValueError):aggregate([score_utterance(self.ref,self.ref),score_utterance(self.ref,self.ref,mode='anchored')])
    def test_no_input_mutation(self):
        r=[{'text':'hello','lang':'en'},{'text':'bonjour','lang':'fr'}];original=copy.deepcopy(r)
        score_utterance(r,r);self.assertEqual(r,original)
    def test_all_wrong_monolingual_labels_fail_token_metric(self):
        r=score_utterance([Token('hello','en'),Token('friend','en')],[Token('hello','fr'),Token('friend','fr')])
        result=aggregate([r])
        self.assertIsNone(result['f1'])
        self.assertEqual(result['aligned_token_language']['macro_f1'],0)
    def test_plain_text_error_is_actionable(self):
        with self.assertRaisesRegex(ValueError,'plain transcript'):
            score_utterance('hello bonjour','hello bonjour')
    def test_duplicates_fail(self):
        record={'id':'x','reference':[],'hypothesis':[]}
        with self.assertRaises(ValueError):evaluate([record,record])
    def test_fixture_counts(self):
        path=Path(__file__).resolve().parents[1]/'examples/pairs.jsonl'
        result=evaluate([json.loads(x) for x in path.read_text().splitlines()])['metrics']
        self.assertEqual((result['tp'],result['fp'],result['fn']),(5,3,1))
        anchored=evaluate([json.loads(x) for x in path.read_text().splitlines()],mode='anchored')['metrics']
        self.assertEqual((anchored['tp'],anchored['fp'],anchored['fn']),(4,4,2))
    def test_boundary_default_and_specification(self):
        self.assertEqual(score_utterance(self.ref,self.ref)['mode'],'boundary')
        self.assertEqual(evaluate([])['specification'],'switchf1-boundary-v3')
        self.assertEqual(evaluate([],mode='boundary_exact')['specification'],'switchf1-boundary-v1')
        self.assertEqual(evaluate([],mode='anchored')['specification'],'ase-f1-v1')
    def test_invalid_mode_even_with_empty_input(self):
        with self.assertRaises(ValueError):evaluate([],mode='typo')
    def test_long_hallucinated_prefix_shifts_indices_but_not_match(self):
        ref=[Token('we','en'),Token('say','en'),Token('bonjour','fr'),Token('maintenant','fr')]
        hyp=[Token('blah','en')]*100+ref
        result=score_utterance(ref,hyp)
        self.assertEqual((result['tp'],result['fp'],result['fn']),(1,0,0))
        self.assertEqual(result['ref_events'][0]['token_indices'],[1,2])
        self.assertEqual(result['hyp_events'][0]['token_indices'],[101,102])
        self.assertEqual(result['ref_events'][0]['position'],result['hyp_events'][0]['position'])
    def test_same_language_boundary_insertions_preserve_switch(self):
        hyp=[self.ref[0]]+[Token('blah','en')]*100+[self.ref[1]]
        result=score_utterance(self.ref,hyp)
        self.assertEqual((result['tp'],result['fp'],result['fn']),(1,0,0))
        self.assertEqual(result['matches_across_insertions'],1)
        exact=score_utterance(self.ref,hyp,mode='boundary_exact')
        self.assertEqual((exact['tp'],exact['fp'],exact['fn']),(0,1,1))
    def test_duplicate_passage_one_to_one_matching(self):
        ref=[Token('we','en'),Token('say','en'),Token('bonjour','fr'),Token('maintenant','fr')]
        result=score_utterance(ref,ref*3)
        self.assertEqual((result['tp'],result['fp'],result['fn']),(1,4,0))
        self.assertAlmostEqual(result['f1'],1/3)
    def test_inserted_false_switch_before_correct_passage_penalized(self):
        ref=[Token('we','en'),Token('say','en'),Token('bonjour','fr')]
        result=score_utterance(ref,[Token('hallo','de'),Token('extra','en')]+ref)
        self.assertEqual((result['tp'],result['fp'],result['fn']),(1,1,0))
    def test_destination_language_insertions_preserve_switch(self):
        result=score_utterance(self.ref,[self.ref[0]]+[Token('salut','fr')]*30+[self.ref[1]])
        self.assertEqual((result['tp'],result['fp'],result['fn']),(1,0,0))
    def test_insertions_on_both_sides_preserve_one_switch(self):
        hyp=[self.ref[0]]+[Token('extra','en')]*10+[Token('salut','fr')]*10+[self.ref[1]]
        self.assertEqual(score_utterance(self.ref,hyp)['f1'],1)
    def test_oscillating_insertions_keep_all_false_positives(self):
        hyp=[self.ref[0],Token('salut','fr'),Token('extra','en'),self.ref[1]]
        result=score_utterance(self.ref,hyp)
        self.assertEqual((result['tp'],result['fp'],result['fn']),(1,2,0))
        self.assertEqual(result['matches'],[(0,0)])
    def test_third_language_does_not_invent_direct_transition(self):
        result=score_utterance(self.ref,[self.ref[0],Token('hallo','de'),self.ref[1]])
        self.assertEqual((result['tp'],result['fp'],result['fn']),(0,2,1))
    def test_wrong_endpoint_label_cannot_be_rescued_by_inserted_switch(self):
        hyp=[Token('hello','fr'),Token('extra','en'),Token('salut','fr'),self.ref[1]]
        result=score_utterance(self.ref,hyp)
        self.assertEqual((result['tp'],result['fp'],result['fn']),(0,2,1))
    def test_deleted_endpoint_bridged_only_in_v3(self):
        ref=[Token('we','en'),Token('say','en'),Token('bonjour','fr')]
        hyp=[ref[0],ref[2]]
        result=score_utterance(ref,hyp,mode='boundary_v2')
        self.assertEqual((result['tp'],result['fp'],result['fn']),(0,1,1))
        self.assertEqual(score_utterance(ref,hyp)['tp'],1)
    def test_monolingual_reference_never_rewards_inserted_switches(self):
        ref=[Token('hello','en'),Token('again','en')]
        result=score_utterance(ref,[ref[0],Token('salut','fr'),ref[1]])
        self.assertEqual((result['tp'],result['fp'],result['fn']),(0,2,0))
    def test_two_reference_boundaries_do_not_share_a_prediction(self):
        ref=[Token('hello','en'),Token('bonjour','fr'),Token('again','en')]
        hyp=[ref[0],Token('salut','fr'),ref[1],Token('extra','en'),ref[2]]
        result=score_utterance(ref,hyp)
        self.assertEqual((result['tp'],result['fp'],result['fn']),(2,0,0))
        self.assertEqual(len({h for _,h in result['matches']}),2)
    def test_all_short_inserted_language_paths_keep_event_counts(self):
        for length in range(5):
            for labels in itertools.product(['en','fr','de'],repeat=length):
                hyp=[self.ref[0]]+[Token('extra'+str(i),lang) for i,lang in enumerate(labels)]+[self.ref[1]]
                sequence=['en',*labels,'fr']
                transitions=[(a,b) for a,b in zip(sequence,sequence[1:]) if a!=b]
                expected_tp=int(('en','fr') in transitions)
                result=score_utterance(self.ref,hyp)
                self.assertEqual((result['tp'],result['fp'],result['fn']),
                    (expected_tp,len(transitions)-expected_tp,1-expected_tp),labels)
    def test_identical_text_without_insertions_agrees_with_exact_mode(self):
        ref=[Token('hello','en'),Token('bonjour','fr'),Token('again','en')]
        for labels in itertools.product(['en','fr','de',None],repeat=3):
            hyp=[Token(t.text,lang) for t,lang in zip(ref,labels)]
            current=score_utterance(ref,hyp)
            exact=score_utterance(ref,hyp,mode='boundary_exact')
            self.assertEqual([current[k] for k in ['tp','fp','fn']],
                [exact[k] for k in ['tp','fp','fn']],labels)

if __name__=='__main__':unittest.main()
