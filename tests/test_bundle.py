"""ZIP/browser source consistency. No network, no browser-only pass claims."""
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import unittest
from virtual_dmv.engine import POLICIES

BASE=pathlib.Path(__file__).resolve().parents[1]

class Packaging(unittest.TestCase):
    def test_original_papers_match_manifest(self):
        pins=json.loads((BASE/'PAPERS/ORIGINAL-FILE-HASHES.json').read_text(encoding='utf8'))
        self.assertEqual(len(pins),4)
        for name,item in pins.items():
            body=(BASE/'PAPERS'/name).read_bytes()
            self.assertTrue(item['unchanged'])
            self.assertEqual(hashlib.sha256(body).hexdigest(),item['sha256'])
            self.assertEqual(len(body),item['byte_count'])
    def test_embedded_exact_python(self):
        html=(BASE/'index.html').read_text(encoding='utf8')
        match=re.search(r'<script type="application/json" id="pythonSources">(.*?)</script>',html,re.S)
        self.assertIsNotNone(match)
        embedded=json.loads(match.group(1))
        for k in ('portable.py','engine.py','__init__.py'):
            self.assertEqual(embedded[k],(BASE/'src/virtual_dmv'/k).read_text(encoding='utf8'))
    def test_browser_source_hashes(self):
        manifest=json.loads((BASE/'docs/ENGINE-SOURCE-PINS.json').read_text())
        for name,expected in manifest['sha256'].items():
            self.assertEqual(hashlib.sha256((BASE/'src/virtual_dmv'/name).read_bytes()).hexdigest(),expected)
        self.assertEqual(hashlib.sha256((BASE/'index.html').read_bytes()).hexdigest(),manifest['standalone_html_sha256'])
    def test_example_policy_is_canonical(self):
        spec=json.loads((BASE/'SPECS/participation-policy.example.json').read_text())
        self.assertEqual(spec['resources'],POLICIES)
    def test_single_file_shell_no_local_asset_links(self):
        html=(BASE/'index.html').read_text()
        self.assertIn('window.VirtualDMV',html)
        self.assertIn('Bot Traffic',html)
        self.assertIn('pyodide/v0.27.7',html)
        self.assertNotIn('__PYTHON_SOURCES__',html)
        self.assertNotIn('__CLIENT__',html)
        self.assertNotIn('__STYLE__',html)
        self.assertNotRegex(html,r'<script\s+src=|<link\s+[^>]*rel="stylesheet"')
    def test_browser_js_syntax_if_node(self):
        import shutil
        if not shutil.which('node'):self.skipTest('node not installed')
        command=['node','--check',str(BASE/'browser/client.js')]
        p=subprocess.run(command,capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)
    def test_extracted_browser_python_replays(self):
        html=(BASE/'index.html').read_text()
        embedded=json.loads(re.search(r'<script type="application/json" id="pythonSources">(.*?)</script>',html,re.S).group(1))
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            folder=pathlib.Path(td)/'virtual_dmv';folder.mkdir()
            for name,code in embedded.items():(folder/name).write_text(code,encoding='utf8')
            command=[sys.executable,'-c',"from virtual_dmv.engine import run_bench; x=run_bench(); assert x['passed']==22, x; print(x['passed'])"]
            p=subprocess.run(command,cwd=td,capture_output=True,text=True,env={'PYTHONPATH':td})
            self.assertEqual(p.returncode,0,p.stdout+'\n'+p.stderr)
            self.assertIn('22',p.stdout)

if __name__=='__main__':unittest.main()
