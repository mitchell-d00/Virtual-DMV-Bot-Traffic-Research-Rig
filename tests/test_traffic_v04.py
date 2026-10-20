"""v0.4 new red/green traffic security and bounded pending-request tests."""
import copy
import unittest
from virtual_dmv import engine as E

NOW=1893456000

class TrafficBoundaryV04(unittest.TestCase):
    def setUp(self):
        self.s=E.bootstrap(seed='traffic-v04',now=NOW)

    def test_malformed_challenge_envelope_fails_closed_with_signed_receipts(self):
        good=E.challenge(self.s,'VDMV-RESEARCH-01','research-library','crawl',now=NOW)
        for bad in (None, [], ['untrusted'], 'not-an-object', 42, True):
            with self.subTest(payload=repr(bad)):
                result=E.decide(self.s,bad,'invalid',now=NOW)
                self.assertFalse(result['allow'])
                self.assertEqual(result['reason'],'MALFORMED_CHALLENGE')
                self.assertIn('receipt_hash',result)
                self.assertIn(good['nonce'],self.s['challenges'])
        self.assertTrue(E.verify_receipts(self.s)['ok'])
        allowed=E.decide(self.s,good,E.holder_proof(self.s,'alice',good),now=NOW)
        self.assertTrue(allowed['allow'])

    def test_outstanding_challenges_are_bounded_fail_closed(self):
        limit=128
        for i in range(limit):
            E.challenge(self.s,'VDMV-RESEARCH-01','research-library','crawl',now=NOW)
        self.assertEqual(len(self.s['challenges']),limit)
        with self.assertRaisesRegex(E.ProtocolError,'pending challenge limit'):
            E.challenge(self.s,'VDMV-RESEARCH-01','research-library','crawl',now=NOW)
        self.assertEqual(len(self.s['challenges']),limit)
        self.assertTrue(E.verify_receipts(self.s)['ok'])

    def test_expired_pending_challenges_are_pruned_and_slots_reclaimed(self):
        stale=[E.challenge(self.s,'VDMV-RESEARCH-01','research-library','crawl',now=NOW) for _ in range(128)]
        fresh=E.challenge(self.s,'VDMV-RESEARCH-01','research-library','crawl',now=NOW+121)
        self.assertEqual(list(self.s['challenges']),[fresh['nonce']])
        self.assertEqual(E.decide(self.s,stale[0],E.holder_proof(self.s,'alice',stale[0]),now=NOW+121)['reason'],
            'INVALID_OR_REPLAYED_CHALLENGE')
        self.assertTrue(E.decide(self.s,fresh,E.holder_proof(self.s,'alice',fresh),now=NOW+121)['allow'])

    def test_cap_preserves_existing_requests_for_normal_admission(self):
        pending=[E.challenge(self.s,'VDMV-RESEARCH-01','research-library','crawl',now=NOW) for _ in range(128)]
        with self.assertRaises(E.ProtocolError):E.challenge(self.s,'anonymous','open-index','crawl',now=NOW)
        chosen=pending[52]
        self.assertTrue(E.decide(self.s,chosen,E.holder_proof(self.s,'alice',chosen),now=NOW)['allow'])
        newer=E.challenge(self.s,'anonymous','open-index','crawl',now=NOW)
        self.assertTrue(E.decide(self.s,newer,'',now=NOW)['allow'])
        self.assertEqual(len(self.s['challenges']),127)

    def test_new_shift_has_unique_ids_and_no_repeated_traffic_tuples(self):
        cases=E.traffic_cases()
        self.assertGreaterEqual(len(cases),60)
        key=lambda c:(c['scenario'],c['plate'],c['owner'],c['resource'],c['action'])
        self.assertEqual(len(set(map(key,cases))),len(cases))
        self.assertEqual(len({c['id'] for c in cases}),len(cases))
        self.assertEqual(len({c['label'].casefold() for c in cases}),len(cases))
        self.assertTrue(any(c['scenario']=='malformed_envelope' for c in cases))
        self.assertTrue(any(c['scenario']=='expired_challenge' for c in cases))

    def test_every_game_case_matches_oracle_and_does_not_modify_workspace(self):
        import json
        original=json.dumps(self.s,sort_keys=True)
        for index,case in enumerate(E.traffic_cases()):
            with self.subTest(id=case['id']):
                actual=E.dispatch({'op':'game_try','state':self.s,'args':{'index':index}})['result']
                self.assertTrue(actual['scenario_matches_expectation'],case)
                self.assertEqual(actual['decision']['reason'],case['expected_reason'])
        self.assertEqual(json.dumps(self.s,sort_keys=True),original)

if __name__=='__main__':unittest.main()
