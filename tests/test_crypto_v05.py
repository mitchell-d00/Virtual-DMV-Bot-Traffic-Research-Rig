"""v0.5 red-green tests: cryptographic canonicalization and fail-closed traffic."""
import copy
import base64
import hashlib
import json
import unittest
from virtual_dmv import engine as E
from virtual_dmv import portable as C

NOW=1893456000

class CryptoBoundaryV05(unittest.TestCase):
    def setUp(self):
        self.s=E.bootstrap(seed='crypto-v05',now=NOW)

    def test_noncanonical_signature_base64_is_rejected(self):
        seed=self.s['owners']['alice']['seed']; msg={'test':'malleability'}
        signature=C.sign(seed,msg)
        alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'
        idx=alphabet.index(signature[-1]); alt=signature[:-1]+alphabet[idx+1]
        self.assertEqual(base64.urlsafe_b64decode(signature+'=='),base64.urlsafe_b64decode(alt+'=='),'fixture must encode identical signature bytes')
        self.assertFalse(C.verify(C.public_key(seed),msg,alt))

    def test_noncanonical_public_key_is_rejected(self):
        seed=self.s['owners']['alice']['seed']; msg={'test':'canonical key'}
        public=C.public_key(seed); signature=C.sign(seed,msg)
        alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'
        idx=alphabet.index(public[-1]); alt=public[:-1]+alphabet[idx+1]
        self.assertEqual(base64.urlsafe_b64decode(public+'=='),base64.urlsafe_b64decode(alt+'=='))
        self.assertFalse(C.verify(alt,msg,signature))

    def test_canonical_decoder_rejects_all_aliases(self):
        raw=bytes(range(64)); canonical=C.b64(raw); letters='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'
        idx=letters.index(canonical[-1])
        for diff in range(1,16):
            duplicate=canonical[:-1]+letters[idx+diff]
            with self.subTest(diff=diff):
                with self.assertRaises(ValueError):C.unb64(duplicate)

    def test_legacy_v1_owner_intent_is_readable_not_silently_upgraded(self):
        old=E.audit(self.s)['VDMV-RESEARCH-01']['credential']['payload']
        successor={**old,'revision':old['revision']+1,'issued_at':NOW+20,'expires_at':NOW+500}
        intent={'schema':'vdmv.owner-intent.v1','kind':'renew','plate_id':old['plate_id'],
                'from_revision':old['revision'],'requested_at':NOW+20}
        E._event(self.s,'renew',{
            'credential':E._signed(self.s['issuer']['seed'],successor),
            'owner_intent':E._signed(self.s['owners']['alice']['seed'],intent)})
        self.assertEqual(E.audit(self.s)['VDMV-RESEARCH-01']['credential']['payload'],successor)
        self.assertEqual(self.s['events'][-1]['data']['owner_intent']['payload']['schema'],'vdmv.owner-intent.v1')

    def test_boolean_and_noninteger_security_timestamps_and_lifetimes_fail(self):
        for now in (True,False,1893456000.5,float('nan'),'1893456000'):
            with self.subTest(now=repr(now)):
                with self.assertRaises(E.ProtocolError):E.challenge(self.s,'anonymous','open-index','discover',now=now)
        for ttl in (True,False,1.5,float('inf'),'120'):
            with self.subTest(ttl=repr(ttl)):
                with self.assertRaises(E.ProtocolError):E.issue(self.s,'alice','research',now=NOW,ttl=ttl)

    def test_64_distinct_ill_formed_packets_fail_closed_without_losing_pending(self):
        active=E.challenge(self.s,'VDMV-RESEARCH-01','research-library','crawl',now=NOW)
        seen=set()
        for i in range(64):
            malformed={**active,'attack_marker':f'bad-{i}-'+('x'*(4097+i))}
            marker=malformed['attack_marker'];self.assertNotIn(marker,seen);seen.add(marker)
            result=E.decide(self.s,malformed,'invalid',now=NOW)
            self.assertFalse(result['allow']);self.assertEqual(result['reason'],'MALFORMED_CHALLENGE')
            self.assertIn(active['nonce'],self.s['challenges'])
        self.assertEqual(len(seen),64)
        self.assertEqual(E.verify_receipts(self.s)['count'],64)
        self.assertTrue(E.decide(self.s,active,E.holder_proof(self.s,'alice',active),now=NOW)['allow'])

    def test_ed25519_differential_against_mature_library_when_available(self):
        try:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
            from cryptography.hazmat.primitives import serialization
        except ImportError:
            self.skipTest('optional cryptography verification package not installed')
        for i in range(8):
            seed=hashlib.sha256(f'security-v05-{i}'.encode()).digest()
            ours=C.b64(seed); reference=Ed25519PrivateKey.from_private_bytes(seed)
            public=reference.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)
            data={'nonce':i,'purpose':'differential-test','scopes':['crawl','train'],'nested':{'allowed':i%2==0}}
            self.assertEqual(C.unb64(C.public_key(ours)),public)
            sig=C.unb64(C.sign(ours,data))
            self.assertEqual(sig,reference.sign(C.canonical(data)))
            reference.public_key().verify(sig,C.canonical(data))
            self.assertTrue(C.verify(C.b64(public),data,C.b64(sig)))

    def test_successor_renewal_intent_binds_successor_hash(self):
        E.renew(self.s,'VDMV-RESEARCH-01','alice',now=NOW+10,ttl=110)
        event=self.s['events'][-1]; detail=event['data']
        self.assertEqual(detail['owner_intent']['payload']['schema'],'vdmv.owner-intent.v2')
        self.assertEqual(detail['owner_intent']['payload']['successor_sha256'],C.sha256(detail['credential']['payload']))
        self.assertEqual(E.audit(self.s)['VDMV-RESEARCH-01']['credential'],detail['credential'])

    def test_transfer_old_and_new_owners_sign_exact_successor(self):
        E.transfer(self.s,'VDMV-RESEARCH-01','alice','bob',now=NOW+10,ttl=120)
        event=self.s['events'][-1]['data']; digest=C.sha256(event['credential']['payload'])
        self.assertEqual(event['owner_intent']['payload']['successor_sha256'],digest)
        self.assertEqual(event['new_owner_acceptance']['payload']['successor_sha256'],digest)

    def _forge_issuer_only_successor_expiry(self,kind):
        if kind=='transfer':E.transfer(self.s,'VDMV-RESEARCH-01','alice','bob',now=NOW+10,ttl=110)
        else:E.renew(self.s,'VDMV-RESEARCH-01','alice',now=NOW+10,ttl=110)
        event=self.s['events'][-1]
        new=copy.deepcopy(event['data']['credential']['payload'])
        new['expires_at']+=10000
        event['data']['credential']={'payload':new,'signature':C.sign(self.s['issuer']['seed'],new)}
        core={k:v for k,v in event.items() if k not in ('signature','hash')}
        event['signature']=C.sign(self.s['issuer']['seed'],core)
        event['hash']=C.sha256({k:v for k,v in event.items() if k!='hash'})

    def test_owner_transfer_intent_rejects_issuer_only_expiry_change(self):
        self._forge_issuer_only_successor_expiry('transfer')
        with self.assertRaisesRegex(E.ProtocolError,'successor'):
            E.audit(self.s)

    def test_owner_renewal_intent_rejects_issuer_only_expiry_change(self):
        self._forge_issuer_only_successor_expiry('renew')
        with self.assertRaisesRegex(E.ProtocolError,'successor'):
            E.audit(self.s)

    def test_retroactive_renewal_fails_before_append(self):
        before=json.dumps(self.s,sort_keys=True)
        with self.assertRaises(E.ProtocolError):E.renew(self.s,'VDMV-RESEARCH-01','alice',now=NOW-10)
        self.assertEqual(json.dumps(self.s,sort_keys=True),before)
        self.assertEqual(E.audit(self.s)['VDMV-RESEARCH-01']['status'],'active')

    def test_retroactive_transfer_fails_before_append(self):
        before=json.dumps(self.s,sort_keys=True)
        with self.assertRaises(E.ProtocolError):E.transfer(self.s,'VDMV-RESEARCH-01','alice','bob',now=NOW-10)
        self.assertEqual(json.dumps(self.s,sort_keys=True),before)
        self.assertEqual(E.audit(self.s)['VDMV-RESEARCH-01']['status'],'active')

    def test_malformed_json_numbers_fail_closed_with_receipt(self):
        ch=E.challenge(self.s,'VDMV-RESEARCH-01','research-library','crawl',now=NOW)
        for bad in [dict(ch,malformed=float('nan')),dict(ch,malformed=float('inf'))]:
            result=E.decide(self.s,bad,'invalid',now=NOW)
            self.assertEqual(result['reason'],'MALFORMED_CHALLENGE')
            self.assertIn('receipt_hash',result)
            self.assertIn(ch['nonce'],self.s['challenges'])
        self.assertTrue(E.decide(self.s,ch,E.holder_proof(self.s,'alice',ch),now=NOW)['allow'])
        self.assertTrue(E.verify_receipts(self.s)['ok'])

    def test_recursive_and_unserializable_challenges_fail_closed(self):
        ch=E.challenge(self.s,'VDMV-RESEARCH-01','research-library','crawl',now=NOW)
        circular={}; circular['self']=circular
        for bad in [circular,dict(ch,unsafe={3,4}),dict(ch,unsafe={1:'bad-key'})]:
            result=E.decide(self.s,bad,'invalid',now=NOW)
            self.assertEqual(result['reason'],'MALFORMED_CHALLENGE')
            self.assertIn(ch['nonce'],self.s['challenges'])
        self.assertTrue(E.verify_receipts(self.s)['ok'])

    def test_oversize_packet_is_rejected_without_echoing_untrusted_body(self):
        ch=E.challenge(self.s,'VDMV-RESEARCH-01','research-library','crawl',now=NOW)
        bad=dict(ch);bad['untrusted']='z'*30000
        result=E.decide(self.s,bad,'not-proof',now=NOW)
        self.assertEqual(result['reason'],'MALFORMED_CHALLENGE')
        self.assertLess(len(json.dumps(self.s['receipts'][-1])),2048)
        self.assertIn(ch['nonce'],self.s['challenges'])

    def test_nested_packet_depth_limit_and_receipt_chain(self):
        ch=E.challenge(self.s,'VDMV-RESEARCH-01','research-library','crawl',now=NOW)
        nested={}; item=nested
        for _ in range(20):
            item['nest']={};item=item['nest']
        bad=dict(ch,untrusted=nested)
        result=E.decide(self.s,bad,'invalid',now=NOW)
        self.assertEqual(result['reason'],'MALFORMED_CHALLENGE')
        self.assertTrue(E.verify_receipts(self.s)['ok'])

if __name__=='__main__':unittest.main()
