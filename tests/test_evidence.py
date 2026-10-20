"""Failed subtests must survive release evidence collection."""
import importlib.util
import pathlib
import sys
import unittest
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from run_scenarios import EvidenceResult

class EvidenceTests(unittest.TestCase):
    def test_failed_and_error_subtests_are_recorded(self):
        class Sample(unittest.TestCase):
            def runTest(self):
                with self.subTest(case='assertion'):
                    self.assertEqual(1, 2)
                with self.subTest(case='exception'):
                    raise ValueError('sentinel error')
                with self.subTest(case='success'):
                    self.assertTrue(True)
        test = Sample()
        result = EvidenceResult()
        test.run(result)
        status, detail = result.outcomes[test.id()]
        self.assertEqual(status, 'error')
        self.assertIn('assertion', detail)
        self.assertIn('sentinel error', detail)
        self.assertFalse(result.wasSuccessful())

    def test_successful_subtests_are_recorded(self):
        class Sample(unittest.TestCase):
            def runTest(self):
                with self.subTest(case='success'):
                    self.assertTrue(True)
        test = Sample()
        result = EvidenceResult()
        test.run(result)
        self.assertEqual(result.outcomes[test.id()][0], 'passed')
