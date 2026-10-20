"""v0.5 protect machine plate/operator namespaces from Unicode homographs."""
import unittest
from virtual_dmv import engine as E
NOW=1893456000
class IdentifierV05(unittest.TestCase):
    def test_confusable_owner_label_is_rejected(self):
        state=E.bootstrap(seed='homograph-v05',now=NOW)
        with self.assertRaises(E.ProtocolError):
            E.add_owner(state,'аlice')  # Cyrillic а; visually resembles Latin a
    def test_confusable_plate_id_is_rejected_before_event(self):
        state=E.bootstrap(seed='homograph-v05',now=NOW)
        n=len(state['events'])
        with self.assertRaises(E.ProtocolError):
            E.issue(state,'alice','research',plate_id='VDMV-АLICE',now=NOW)  # Cyrillic А
        self.assertEqual(len(state['events']),n)
        self.assertTrue(E.audit(state))
if __name__=='__main__':unittest.main()
