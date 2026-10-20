"""v0.6 regression gates: defensive ingress and signed timeline semantics.

Cases were authored against v0.5 before changes and the red log is retained.
The issuer and host remain demo-local and are NOT production trust roots.
"""
import copy
import unittest
from virtual_dmv import engine as E
from virtual_dmv import portable as C

FIXED = 1893456000
PLATE = 'VDMV-RESEARCH-01'


class ChallengeIngress(unittest.TestCase):
    def setUp(self):
        self.state = E.bootstrap(seed='ingress-v06',now=FIXED)
    def test_long_plate_id_cannot_fill_pending_storage(self):
        before=(len(self.state['challenges']), self.state['sequence_nonce'])
        with self.assertRaises(E.ProtocolError):
            E.challenge(self.state,'P'*50000,'research-library','crawl',now=FIXED)
        self.assertEqual((len(self.state['challenges']),self.state['sequence_nonce']),before)
    def test_nonstring_plate_ids_fail_before_challenge_allocation(self):
        for label in ([],{},None,0,True):
            with self.subTest(label=repr(label)):
                before=(len(self.state['challenges']),self.state['sequence_nonce'])
                with self.assertRaises(E.ProtocolError):
                    E.challenge(self.state,label,'research-library','crawl',now=FIXED)
                self.assertEqual((len(self.state['challenges']),self.state['sequence_nonce']),before)
    def test_nonhashable_resource_is_protocol_error(self):
        for resource in ([],{'resource':'open-index'}):
            with self.subTest(resource=str(resource)):
                with self.assertRaises(E.ProtocolError):
                    E.challenge(self.state,PLATE,resource,'crawl',now=FIXED)
        self.assertEqual(len(self.state['challenges']),0)
    def test_unknown_but_syntactically_safe_plate_still_denied_by_gate(self):
        ch=E.challenge(self.state,'VDMV-UNREGISTERED-123','research-library','crawl',now=FIXED)
        r=E.decide(self.state,ch,'',now=FIXED)
        self.assertEqual((r['allow'],r['reason']),(False,'UNKNOWN_OR_REVOKED'))
        self.assertTrue(E.verify_receipts(self.state)['ok'])
    def test_bad_plate_unicode_nul_and_whitespace_rejected(self):
        for label in ('bad\0plate','VDMV LAB','VDMV-\u0430BC',''):
            with self.subTest(label=repr(label)):
                with self.assertRaises(E.ProtocolError):
                    E.challenge(self.state,label,'open-index','discover',now=FIXED)


class SignedTimeSemantics(unittest.TestCase):
    def setUp(self):
        self.state = E.bootstrap(seed='time-v06',now=FIXED)
    def test_retroactive_revocation_fails_without_event_append(self):
        before=len(self.state['events'])
        with self.assertRaises(E.ProtocolError):
            E.revoke(self.state,PLATE,now=FIXED-500)
        self.assertEqual(len(self.state['events']),before)
        self.assertEqual(E.audit(self.state)[PLATE]['status'],'active')
    def test_retroactive_signed_revoke_event_fails_full_audit(self):
        E._event(self.state,'revoke',{'plate_id':PLATE,'from_revision':1,'revoked_at':FIXED-500})
        with self.assertRaises(E.ProtocolError):
            E.audit(self.state)
    def test_unsigned_type_confusion_bool_revision_rejected_even_when_signed(self):
        state=E.new_state(seed='bool-v06',now=FIXED)
        E.add_owner(state,'alice',seed=C.b64(bytes(range(32))))
        plate={'schema':'vdmv.plate.v1','plate_id':'VDMV-BOOL','issuer':state['issuer']['id'],
            'participation_class':'research','owner_public_key':state['owners']['alice']['public_key'],
            'revision':True,'issued_at':FIXED,'expires_at':FIXED+100}
        E._event(state,'issue',{'credential':{'payload':plate,'signature':C.sign(state['issuer']['seed'],plate)}})
        with self.assertRaises(E.ProtocolError):
            E.audit(state)
    def test_normal_revocation_and_replay_safety_preserved(self):
        E.revoke(self.state,PLATE,now=FIXED)
        self.assertEqual(E.audit(self.state)[PLATE]['status'],'revoked')
        a=E.request(self.state,PLATE,'research-library','crawl',owner='alice',now=FIXED)
        self.assertEqual(a['reason'],'UNKNOWN_OR_REVOKED')
        self.assertTrue(E.verify_receipts(self.state)['ok'])


if __name__ == '__main__': unittest.main()
