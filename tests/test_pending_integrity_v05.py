"""v0.5 poisoned pending traffic should not bypass or crash admission."""
import unittest
from virtual_dmv import engine as E

NOW=1893456000

class PendingSafety(unittest.TestCase):
    def setUp(self):self.s=E.bootstrap(seed='v05-poisoned-pending',now=NOW)

    def test_poisoned_pending_entry_denied_with_receipt_not_exception(self):
        ch=E.challenge(self.s,'VDMV-RESEARCH-01','research-library','crawl',now=NOW)
        self.s['challenges'][ch['nonce']]={'nonce':ch['nonce']}
        result=E.decide(self.s,{'nonce':ch['nonce']},'forged',now=NOW)
        self.assertEqual(result['reason'],'INVALID_OR_REPLAYED_CHALLENGE')
        self.assertFalse(result['allow'])
        self.assertIn('receipt_hash',result)
        self.assertTrue(E.verify_receipts(self.s)['ok'])

    def test_non_dict_pending_entry_denied_and_removed(self):
        ch=E.challenge(self.s,'VDMV-RESEARCH-01','research-library','crawl',now=NOW)
        self.s['challenges'][ch['nonce']]='malformed-pending'
        result=E.decide(self.s,ch,'forged',now=NOW)
        self.assertEqual(result['reason'],'INVALID_OR_REPLAYED_CHALLENGE')
        self.assertNotIn(ch['nonce'],self.s['challenges'])
        self.assertTrue(E.verify_receipts(self.s)['ok'])

if __name__=='__main__':unittest.main()
