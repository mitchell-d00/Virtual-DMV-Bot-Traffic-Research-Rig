"""Deterministically generate a self-contained UI+Python-source HTML.

The Pyodide interpreter itself remains an external version-pinned CDN asset.
This is an intentional and documented runtime dependency, not an offline binary.
"""
from pathlib import Path
import json
import hashlib
import gzip
import base64

ROOT=Path(__file__).resolve().parents[1]
files={"portable.py":ROOT/"src/virtual_dmv/portable.py",
       "engine.py":ROOT/"src/virtual_dmv/engine.py",
       "__init__.py":ROOT/"src/virtual_dmv/__init__.py"}
source={name:path.read_text(encoding='utf-8') for name,path in files.items()}
source_json=json.dumps(source,ensure_ascii=True).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
base=(ROOT/"browser/template.html").read_text(encoding='utf8')
html=base.replace('__STYLE__',(ROOT/"browser/style.css").read_text(encoding='utf8'))
report=json.loads((ROOT/'evaluation/SCENARIO-RESULTS.json').read_text(encoding='utf8'))
scenario_text=json.dumps(report,ensure_ascii=False,separators=(',',':')).encode('utf-8')
scenario_json=json.dumps({'compression':'gzip-base64-v1','data':base64.b64encode(gzip.compress(scenario_text,compresslevel=9,mtime=0)).decode('ascii')},separators=(',',':'))
html=html.replace('__SCENARIO_REPORT__',scenario_json)
html=html.replace('__PYTHON_SOURCES__',source_json)
html=html.replace('__CLIENT__',(ROOT/"browser/client.js").read_text(encoding='utf8').replace('</script','<\\/script'))
(ROOT/"index.html").write_text(html,encoding='utf8')
hash_map={name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in files.items()}
(ROOT/"docs/ENGINE-SOURCE-PINS.json").write_text(json.dumps({"schema":"vdmv.source-pins.v1","sha256":hash_map,
    "standalone_html_sha256":hashlib.sha256(html.encode()).hexdigest(),"runtime":"Pyodide v0.27.7 via external jsDelivr CDN"},indent=2)+'\n')
print('Single-file browser UI: index.html',len(html.encode()),'bytes; Python source embedded')

summary = report['summary']
(ROOT/'docs/CURRENT-TEST-RESULTS.md').write_text(
    '# Current recorded test results\n\n'
    + 'Generated from `evaluation/SCENARIO-RESULTS.json`; historical counts elsewhere describe earlier releases.\n\n'
    + '\n'.join(f'- {key}: {summary[key]}' for key in ('unit','probe','game','security_matrix','ingress_matrix','recorded_passed','recorded_failed','calculator_pending'))
    + '\n\nThese are local synthetic checks. Browser and CI results are recorded separately in the pull request. Pending external checks are not passes.\n')
