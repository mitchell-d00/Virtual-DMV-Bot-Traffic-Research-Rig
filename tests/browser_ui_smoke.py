"""Optional UI wiring smoke with a STUB Python loader.

This cannot establish that real Pyodide or the cryptographic engine executed.
Run separately: python tests/browser_ui_smoke.py
Requires Playwright and local Chromium. Uses page.set_content and a preloaded mock. No network.
"""
import pathlib
from playwright.sync_api import sync_playwright
ROOT=pathlib.Path(__file__).resolve().parents[1]
MOCK=r'''
(() => {
 let state={created_at:1893456000,owners:{alice:{},bob:{},mallory:{}},events:[{kind:'issue'},{kind:'issue'}],receipts:[],policies:{'research-library':{description:'Sample',anonymous:[],allows:{crawl:['research']},attribution:[]}}};
 const cases=[{label:'Known researcher requests a summary',plate:'VDMV-RESEARCH-01',owner:'alice',resource:'research-library',action:'summarize',truth:'Allow, with attribution.'}];
 let input='';
 window.loadPyodide=async()=>({FS:{mkdirTree(){},writeFile(){}},globals:{set(name,v){if(name==='vdmv_request')input=v}},runPython(s){if(!s.startsWith('browser_bridge('))return '';const q=JSON.parse(input);if(q.op==='bootstrap')return JSON.stringify({ok:true,state,result:{ready:true}}); if(q.op==='audit')return JSON.stringify({ok:true,state:q.state,result:{ok:true}});
   state=q.state||state;let result;
   switch(q.op){case 'casebook':result=cases;break;case 'roster':result=[{plate_id:'VDMV-RESEARCH-01',class:'research',owner:'alice',status:'active'}];break;case 'policies':result=state.policies;break;case 'game_try':result={case:cases[0],decision:{allow:true,reason:'POLICY_ALLOW',receipt_hash:'fake-ui-only'}};state.receipts.push({});break;case 'bench':result={passed:12,total:12,cases:Array.from({length:12},(_,i)=>({name:'Stub UI case '+i,pass:true}))};break;case 'economics':result={accepted:120,gross_access_utility:600,registration_cost:100,net_model_utility:500};break;default:result={ok:true};}return JSON.stringify({ok:true,state,result});}});
})();
'''
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    for width in [390,1280]:
        page=browser.new_page(viewport={'width':width,'height':900})
        page.evaluate(MOCK)
        page.set_content((ROOT/"index.html").read_text(encoding="utf8"),wait_until="domcontentloaded")
        page.wait_for_selector('#runtimeStatus.ready')
        if width==1280:page.screenshot(path='/tmp/vdmv_desktop_mock.png',full_page=True)
        if width==390:page.screenshot(path='/tmp/vdmv_mobile_mock.png',full_page=True)
        assert 'Known researcher' in page.locator('#trafficLabel').inner_text()
        page.locator('#chooseAllow').click()
        assert 'Correct' in page.locator('#gameFeedback').inner_text()
        page.locator('[data-tab="registry"]').click()
        assert page.locator('#rosterBody tr').count()>=1
        page.locator('[data-tab="bench"]').click()
        page.locator('#runBench').click()
        assert '12/12' in page.locator('#benchRows').inner_text()
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth+2'), 'horizontal overflow'
        print(f'{width}px UI wiring smoke passed (stub interpreter, NOT true Pyodide)')
        page.close()
    browser.close()
