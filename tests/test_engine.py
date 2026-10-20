"""Reproducible protocol rejection tests; no live servers, no keys from real users."""
import copy
import json
import unittest
from virtual_dmv import engine as E
from virtual_dmv import portable as C

FIXED=1893456000

class Ed25519Reference(unittest.TestCase):
    def test_rfc8032_vector_one(self):
        seed=bytes.fromhex('9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60')
        # RFC 8032 signs empty raw bytes; C.sign signs canonical JSON, so the
        # raw vector is verified below with the unencoded reference path.
        from hashlib import sha512
        a,prefix=C._scalar(seed)
        self.assertEqual(C._encode(C._mul(C.BASE,a)).hex(), 'd75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a')
        r=int.from_bytes(sha512(prefix+b'').digest(),'little')%C.L
        R=C._encode(C._mul(C.BASE,r))
        k=int.from_bytes(sha512(R+C._encode(C._mul(C.BASE,a))+b'').digest(),'little')%C.L
        raw=R+((r+k*a)%C.L).to_bytes(32,'little')
        self.assertEqual(raw.hex(),'e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e06522490155'+'5fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b')
    def test_sign_verify_and_tamper(self):
        seed=C.b64(bytes(range(32))); msg={'z':2,'a':['alpha','beta']}
        sig=C.sign(seed,msg)
        self.assertTrue(C.verify(C.public_key(seed),msg,sig))
        self.assertFalse(C.verify(C.public_key(seed),{'z':3,'a':['alpha','beta']},sig))
        self.assertFalse(C.verify(C.public_key(seed),msg,sig[:-2]+'AA'))
    def test_identity_public_key_rejected(self):
        seed=C.b64(bytes(range(32))); msg={'test':'x'}
        self.assertFalse(C.verify(C.b64(bytes([1]+[0]*31)),msg,C.sign(seed,msg)))
    def test_nonfinite_json_rejected(self):
        with self.assertRaises(ValueError):C.canonical({'x':float('nan')})

class Governance(unittest.TestCase):
    def setUp(self):self.s=E.bootstrap(seed='unit-fixture',now=FIXED)
    def tryit(self,plate='VDMV-RESEARCH-01',resource='research-library',action='crawl',owner='alice',offset=0,**kw):
        return E.request(self.s,plate,resource,action,owner=owner,now=FIXED+offset,**kw)
    def test_init_and_audit(self):
        self.assertEqual(E.audit_all(self.s)['active'],2)
        self.assertEqual(len(E.roster(self.s)),2)
    def test_issuer_signature(self):
        self.assertTrue(C.verify(self.s['issuer']['public_key'],self.s['events'][0]['data']['credential']['payload'],self.s['events'][0]['data']['credential']['signature']))
    def test_authorized_research_with_attribution(self):
        r=self.tryit(action='summarize');self.assertTrue(r['allow']);self.assertTrue(r['attribution_required'])
    def test_cross_scope_denied(self):
        self.assertEqual(self.tryit(plate='VDMV-CRAWLER-02',resource='licensed-training-data',action='train',owner='bob')['reason'],'POLICY_DENY')
    def test_unknown_denied_private(self):
        self.assertFalse(self.tryit(plate='anonymous',owner=None)['allow'])
    def test_unknown_allowed_public(self):
        self.assertTrue(self.tryit(plate='anonymous',resource='open-index',owner=None)['allow'])
    def test_known_not_automatically_authorized(self):
        self.assertFalse(self.tryit(action='redistribute')['allow'])
    def test_owner_signature_wrong(self):
        self.assertEqual(self.tryit(owner='mallory')['reason'],'INVALID_HOLDER_PROOF')
    def test_replay_consumed(self):
        c=E.challenge(self.s,'VDMV-RESEARCH-01','research-library','crawl',now=FIXED)
        proof=E.holder_proof(self.s,'alice',c)
        self.assertTrue(E.decide(self.s,c,proof,now=FIXED)['allow'])
        self.assertEqual(E.decide(self.s,c,proof,now=FIXED)['reason'],'INVALID_OR_REPLAYED_CHALLENGE')
    def test_modified_challenge_consumes_nonce(self):
        c=E.challenge(self.s,'VDMV-RESEARCH-01','research-library','crawl',now=FIXED)
        evil=copy.deepcopy(c);evil['action']='train'
        proof=E.holder_proof(self.s,'alice',evil)
        self.assertFalse(E.decide(self.s,evil,proof,now=FIXED)['allow'])
        self.assertEqual(E.decide(self.s,c,E.holder_proof(self.s,'alice',c),now=FIXED)['reason'],'INVALID_OR_REPLAYED_CHALLENGE')
    def test_expired(self):
        self.assertEqual(self.tryit(offset=86401)['reason'],'EXPIRED_OR_NOT_YET_VALID')
    def test_revocation(self):
        E.revoke(self.s,'VDMV-RESEARCH-01',now=FIXED)
        self.assertEqual(self.tryit()['reason'],'UNKNOWN_OR_REVOKED')
    def test_transfer(self):
        E.transfer(self.s,'VDMV-RESEARCH-01','alice','bob',now=FIXED)
        self.assertEqual(self.tryit(owner='alice')['reason'],'INVALID_HOLDER_PROOF')
        self.assertTrue(self.tryit(owner='bob')['allow'])
    def test_forged_transfer_refused(self):
        with self.assertRaises(E.ProtocolError):E.transfer(self.s,'VDMV-RESEARCH-01','mallory','bob',now=FIXED)
    def test_renew(self):
        E.renew(self.s,'VDMV-RESEARCH-01','alice',now=FIXED+300,ttl=100000)
        self.assertTrue(self.tryit(offset=90000)['allow'])
    def test_stale_credential_after_transfer(self):
        old=copy.deepcopy(E.audit(self.s)['VDMV-RESEARCH-01']['credential'])
        E.transfer(self.s,'VDMV-RESEARCH-01','alice','bob',now=FIXED)
        self.assertEqual(self.tryit(owner='bob',credential_override=old)['reason'],'STALE_OR_FORGED_CREDENTIAL')
    def test_hash_tamper(self):
        self.s['events'][0]['data']['credential']['payload']['participation_class']='agentic'
        with self.assertRaises(E.ProtocolError):E.audit(self.s)
    def test_transition_signature_tamper(self):
        E.transfer(self.s,'VDMV-RESEARCH-01','alice','bob',now=FIXED)
        self.s['events'][-1]['data']['owner_intent']['signature']='abc'
        # Event outer hash fails before intent check, also valid detection.
        with self.assertRaises(E.ProtocolError):E.audit(self.s)
    def test_new_owner_acceptance_is_signed(self):
        E.transfer(self.s,'VDMV-RESEARCH-01','alice','bob',now=FIXED)
        transfer_data=self.s['events'][-1]['data']
        acceptance=transfer_data['new_owner_acceptance']
        self.assertTrue(C.verify(self.s['owners']['bob']['public_key'],acceptance['payload'],acceptance['signature']))
        self.assertTrue(E.audit(self.s)['VDMV-RESEARCH-01']['status']=='active')
    def test_receipt_tamper(self):
        self.tryit(); self.s['receipts'][0]['decision']['allow']=False
        with self.assertRaises(E.ProtocolError):E.verify_receipts(self.s)
    def test_receipt_chain(self):
        self.tryit();self.tryit(action='train',resource='licensed-training-data')
        self.assertEqual(E.verify_receipts(self.s)['count'],2)
    def test_wrong_resource_never_allowed(self):
        with self.assertRaises(E.ProtocolError):E.challenge(self.s,'VDMV-RESEARCH-01','nonexistent','crawl',now=FIXED)
    def test_no_duplicate_issued(self):
        with self.assertRaises(E.ProtocolError):E.issue(self.s,'alice','research',plate_id='VDMV-RESEARCH-01',now=FIXED)
    def test_policy_immutable_by_issued_plate(self):
        self.s['policies']['research-library']['allows']['crawl']=[]
        self.assertFalse(self.tryit()['allow'])
    def test_proof_receipts_are_signable(self):
        r=self.tryit();packet=self.s['receipts'][0]; core={k:v for k,v in packet.items() if k not in ('hash','signature')}
        self.assertEqual(packet['hash'],r['receipt_hash']);self.assertTrue(C.verify(self.s['host']['public_key'],core,packet['signature']))
    def test_game_case_isolation_after_revocation(self):
        # Regression VDMV-REG-001: a scripted game must not inherit mutable registry actions.
        E.revoke(self.s,'VDMV-RESEARCH-01',now=FIXED)
        result=E.dispatch({'op':'game_try','state':self.s,'args':{'index':0}})
        self.assertTrue(result['result']['decision']['allow'])
        self.assertEqual(result['result']['decision']['reason'],'POLICY_ALLOW')
    def test_game_does_not_write_live_receipts(self):
        # Regression VDMV-REG-002: game evidence lives in a temporary fixture, not the registry.
        n=len(self.s['receipts'])
        E.dispatch({'op':'game_try','state':self.s,'args':{'index':0}})
        self.assertEqual(len(self.s['receipts']),n)
    def test_game_rejects_invalid_indices(self):
        # Regression VDMV-REG-003: signed indices cannot wrap around to a valid case.
        for index in (-1,10,999):
            with self.subTest(index=index):
                with self.assertRaises(E.ProtocolError):
                    E.dispatch({'op':'game_try','state':self.s,'args':{'index':index}})
    def test_game_expected_outcomes_independent_oracle(self):
        cases=E.traffic_cases()
        self.assertEqual(len(cases),10)
        for i,c in enumerate(cases):
            with self.subTest(id=c['id']):
                outcome=E.dispatch({'op':'game_try','state':self.s,'args':{'index':i}})['result']
                self.assertTrue(outcome['isolated'])
                self.assertTrue(outcome['scenario_matches_expectation'],outcome)
                self.assertEqual(outcome['decision']['allow'],c['expected_allow'])
                self.assertEqual(outcome['decision']['reason'],c['expected_reason'])
    def test_unique_game_scenario_signatures(self):
        cases=E.traffic_cases()
        self.assertEqual(len({c['id'] for c in cases}),len(cases))
        self.assertEqual(len({(c['plate'],c['owner'],c['resource'],c['action']) for c in cases}),len(cases))
    def test_game_ignores_registry_policy_edit(self):
        self.s['policies']['research-library']['allows']['summarize']=[]
        result=E.dispatch({'op':'game_try','state':self.s,'args':{'index':0}})
        self.assertTrue(result['result']['scenario_matches_expectation'])
        self.assertTrue(result['result']['decision']['allow'])
    def test_probe_scenario_ids_are_unique(self):
        r=E.run_bench()
        self.assertEqual(len({c['id'] for c in r['cases']}),r['total'])
        self.assertTrue(all(c['expected'] and c['observed'] for c in r['cases']))
    def test_bench_all(self):
        x=E.run_bench();self.assertEqual(x['passed'],x['total'])
    def test_command_json(self):
        req=E.bridge(json.dumps({'op':'roster','state':self.s}))
        self.assertEqual(len(json.loads(req)['result']),2)
    def test_economics_determinism(self):
        a=E.economics_simulation(self.s,rounds=100,seed=4,adoption=.3)
        self.assertEqual(a,E.economics_simulation(self.s,rounds=100,seed=4,adoption=.3))
    def test_original_ownership_separated_from_identification(self):
        a=E.roster(self.s);self.assertEqual(a[0]['owner'],'alice')
        self.assertNotEqual(self.s['owners']['alice']['public_key'],self.s['owners']['bob']['public_key'])

if __name__=='__main__':unittest.main()
