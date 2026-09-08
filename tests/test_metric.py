import copy
import json
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
        self.assertEqual(score_utterance(self.ref,wrong)['f1'],0)
        self.assertEqual(score_utterance(self.ref,wrong,mode='boundary')['f1'],1)
    def test_one_wrong_anchor_fails(self):
        self.assertEqual(score_utterance(self.ref,[Token('goodbye','en'),self.ref[1]])['tp'],0)
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
    def test_unknown_hypothesis_breaks_sequence(self):
        r=score_utterance(self.ref,[self.ref[0],Token('?', 'und'),self.ref[1]])
        self.assertEqual(r['tp'],0);self.assertEqual(r['unknown_hypothesis_tokens'],1)
    def test_unknown_reference_fails(self):
        with self.assertRaises(ValueError):score_utterance([Token('x','und')],[])
    def test_unicode_marks_preserved(self):
        r=[Token('கி','ta'),Token('hello','en')]
        self.assertEqual(score_utterance(r,[Token('கீ','ta'),Token('hello','en')])['tp'],0)
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
        with self.assertRaises(ValueError):aggregate([score_utterance(self.ref,self.ref),score_utterance(self.ref,self.ref,mode='boundary')])
    def test_no_input_mutation(self):
        r=[{'text':'hello','lang':'en'},{'text':'bonjour','lang':'fr'}];original=copy.deepcopy(r)
        score_utterance(r,r);self.assertEqual(r,original)
    def test_duplicates_fail(self):
        record={'id':'x','reference':[],'hypothesis':[]}
        with self.assertRaises(ValueError):evaluate([record,record])
    def test_fixture_counts(self):
        path=Path(__file__).resolve().parents[1]/'examples/pairs.jsonl'
        result=evaluate([json.loads(x) for x in path.read_text().splitlines()])['metrics']
        self.assertEqual((result['tp'],result['fp'],result['fn']),(4,4,2))

if __name__=='__main__':unittest.main()
