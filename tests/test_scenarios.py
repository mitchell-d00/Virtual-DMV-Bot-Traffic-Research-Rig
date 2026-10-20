"""Release catalog integrity: stable IDs, visible provenance, unique calculator questions."""
import json
import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]

class ScenarioPublication(unittest.TestCase):
    def setUp(self):
        self.document=json.loads((ROOT/'evaluation/SCENARIO-RESULTS.json').read_text(encoding='utf-8'))
        self.rows=self.document['scenarios']
    def test_unique_scenario_ids_and_titles(self):
        ids=[c['id'] for c in self.rows]
        self.assertEqual(len(ids),len(set(ids)))
        label=[(c['kind'],c['title'].lower().strip()) for c in self.rows]
        self.assertEqual(len(label),len(set(label)))
    def test_every_public_scenario_has_evidence_boundary(self):
        for row in self.rows:
            with self.subTest(case=row['id']):
                self.assertTrue(row['source'] and row['expected'] and row['observed'])
                self.assertIn(row['status'],('passed','failed','error','skipped','pending'))
                self.assertIn(row['execution'],('recorded-local-python','run-locally-and-rerunnable-in-browser','requires-console-in-Mitchell-Tech','recorded-local-python-security-matrix'))
    def test_calculator_questions_are_distinct_and_pending(self):
        questions=[r for r in self.rows if r['kind']=='mitchell_tech_manual']
        self.assertEqual(len(questions),5)
        self.assertEqual(len({r['input'] for r in questions}),5)
        self.assertTrue(all(r['status']=='pending' for r in questions))
    def test_source_bound_release_manifest_in_html(self):
        html=(ROOT/'index.html').read_text(encoding='utf-8')
        self.assertIn('scenarioManifest',html)
        self.assertIn('CASE ',html)
        self.assertIn('copyCalculator',html)
        self.assertIn('GAME-001',html)
        self.assertNotIn('__SCENARIO_REPORT__',html)

if __name__=='__main__':unittest.main()
