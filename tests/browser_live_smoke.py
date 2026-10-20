"""Real Chromium/Pyodide integration. Requires network to the pinned CDN."""
import functools
import http.server
import json
import os
import pathlib
import threading
from playwright.sync_api import sync_playwright
ROOT = pathlib.Path(__file__).resolve().parents[1]
server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT)))
threading.Thread(target=server.serve_forever, daemon=True).start()
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH'))
        page = browser.new_page(viewport={'width': 390, 'height': 844})
        page.set_default_timeout(180000)
        page.goto(f'http://127.0.0.1:{server.server_port}')
        page.wait_for_selector('#runtimeStatus.ready')
        page.evaluate('window.VirtualDMV.ready()')
        result = page.evaluate("window.VirtualDMV.command('bench')")
        assert result['passed'] == result['total'] == 22, result
        decision = page.evaluate("window.VirtualDMV.command('request', {plate_id:'VDMV-RESEARCH-01',owner:'alice',resource:'research-library',action:'summarize'})")
        assert decision['allow'], decision
        snapshot = page.evaluate('window.VirtualDMV.snapshot()')
        page.reload()
        page.wait_for_selector('#runtimeStatus.ready')
        assert page.evaluate('window.VirtualDMV.snapshot()') == snapshot
        page.locator('[data-tab="registry"]').click()
        with page.expect_download() as download:
            page.locator('#exportState').click()
        exported = pathlib.Path(download.value.path()).read_bytes()
        assert json.loads(exported) == snapshot
        page.locator('#importFile').set_input_files({'name':'state.json','mimeType':'application/json','buffer':exported})
        page.wait_for_function("document.querySelector('#operationOutput').textContent.includes('Imported local test state')")
        assert page.evaluate('window.VirtualDMV.snapshot()') == snapshot
        print('LIVE PASS: real Pyodide, 22 probes, signed request, reload, export/import; 390px Chromium')
        browser.close()
finally:
    server.shutdown()
