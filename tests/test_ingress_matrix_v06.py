"""Publish and reject duplicates in the v0.6 adversarial ingress matrix."""
import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from run_ingress_matrix import check_matrix

class IngressMatrixEvidence(unittest.TestCase):
    def test_each_case_has_unique_inputs_and_matches_expected(self):
        rows=check_matrix()
        self.assertGreaterEqual(len(rows),40)
        self.assertEqual(len({x['id'] for x in rows}),len(rows))
        failures=[x for x in rows if x['status']!='passed']
        self.assertEqual(failures,[])

if __name__=='__main__':unittest.main()
