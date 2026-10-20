"""New Bot Traffic adversarial tests: intentionally red against v0.2 engine."""
import copy
import json
import unittest
from unittest.mock import patch
from virtual_dmv import engine as E

NOW=1893456000

class TrafficBoundaryV03(unittest.TestCase):
    def setUp(self):
        self.s=E.bootstrap(seed='traffic-v03',now=NOW)

    def test_malformed_nonce_returns_host_receipt_without_consuming_valid_challenge(self):
        valid=E.challenge(self.s,'VDMV-RESEARCH-01','research-library','crawl',now=NOW)
        for bad in ([],{},['CH-forged']):
            with self.subTest(nonce=repr(bad)):
                fake=copy.deepcopy(valid)
                fake['nonce']=bad
                result=E.decide(self.s,fake,'forged',now=NOW)
                self.assertFalse(result['allow'])
                self.assertEqual(result['reason'],'MALFORMED_CHALLENGE')
                self.assertIsInstance(result['receipt_hash'],str)
                self.assertIn(valid['nonce'],self.s['challenges'])
        result=E.decide(self.s,valid,E.holder_proof(self.s,'alice',valid),now=NOW)
        self.assertTrue(result['allow'])
        self.assertTrue(E.verify_receipts(self.s)['ok'])

    def test_new_challenge_nonce_collision_does_not_overwrite_existing_request(self):
        with patch.object(E.secrets,'token_hex',side_effect=['same','same','different']):
            first=E.challenge(self.s,'VDMV-RESEARCH-01','research-library','crawl',now=NOW)
            second=E.challenge(self.s,'VDMV-CRAWLER-02','open-index','index',now=NOW)
        self.assertNotEqual(first['nonce'],second['nonce'])
        self.assertEqual(len(self.s['challenges']),2)
        self.assertTrue(E.decide(self.s,first,E.holder_proof(self.s,'alice',first),now=NOW)['allow'])
        self.assertTrue(E.decide(self.s,second,E.holder_proof(self.s,'bob',second),now=NOW)['allow'])

    def test_traffic_shift_exposes_at_least_24_unique_scripted_cases(self):
        cases=E.traffic_cases()
        self.assertGreaterEqual(len(cases),24)
        keys=[(c.get('scenario','baseline'),c['plate'],c['owner'],c['resource'],c['action']) for c in cases]
        self.assertEqual(len(keys),len(set(keys)))
        self.assertEqual(len({c['id'] for c in cases}),len(cases))
        self.assertTrue(any(c.get('scenario')=='malformed_nonce' for c in cases))
        self.assertTrue(any(c.get('scenario')=='replay' for c in cases))
        self.assertTrue(any(c.get('scenario')=='expired' for c in cases))
        self.assertTrue(any(c.get('scenario') in ('transfer_old','transfer_new') for c in cases))

    def test_traffic_semantics_repeat_stably_across_isolated_runs(self):
        # Random request nonces change receipt hashes; semantic results must not.
        for index,case in enumerate(E.traffic_cases()):
            with self.subTest(case=case['id']):
                outcomes=[]
                for _ in range(2):
                    answer=E.dispatch({'op':'game_try','state':self.s,'args':{'index':index}})['result']
                    d=answer['decision']
                    outcomes.append((d['allow'],d['reason'],d['attribution_required']))
                self.assertEqual(outcomes[0],outcomes[1])

    def test_all_game_cases_match_separately_declared_oracles_and_preserve_workspace(self):
        before=json.dumps(self.s,sort_keys=True)
        for index,c in enumerate(E.traffic_cases()):
            with self.subTest(id=c['id']):
                result=E.dispatch({'op':'game_try','state':self.s,'args':{'index':index}})['result']
                self.assertTrue(result['scenario_matches_expectation'])
                self.assertEqual(result['decision']['allow'],c['expected_allow'])
                self.assertEqual(result['decision']['reason'],c['expected_reason'])
                self.assertEqual(result['decision']['attribution_required'],c['expected_attribution'])
                self.assertTrue(result['isolated'])
        self.assertEqual(json.dumps(self.s,sort_keys=True),before)

if __name__=='__main__':unittest.main()
