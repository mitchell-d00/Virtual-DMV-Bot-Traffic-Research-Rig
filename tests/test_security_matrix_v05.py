"""v0.5 separate 168-tuple permission and receipt conformance bank."""
import unittest
from virtual_dmv import engine as E

class MatrixV05(unittest.TestCase):
    def test_all_resource_roles_actions_have_unique_expected_receipted_decisions(self):
        from pathlib import Path
        import importlib.util
        path=Path(__file__).resolve().parents[1]/'tools/run_security_matrix.py'
        spec=importlib.util.spec_from_file_location('security_matrix',path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        rows=module.check_matrix()
        self.assertEqual(len(rows),4*6*7)
        self.assertTrue(all(x['status']=='passed' for x in rows))
        self.assertEqual(len({x['id'] for x in rows}),len(rows))
        self.assertEqual(len({x['title'] for x in rows}),len(rows))

if __name__=='__main__':unittest.main()
