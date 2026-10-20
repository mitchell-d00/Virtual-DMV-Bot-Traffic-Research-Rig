/* Browser transport and UI only. All gate decisions run in Python via Pyodide. */
(() => {
'use strict';
const CDN='https://cdn.jsdelivr.net/pyodide/v0.27.7/full/';
const storeKey='virtual-dmv-lab-state-v1';
const $=id=>document.getElementById(id);
let py=null, state=null, gameCases=[], caseIndex=0, gameResolved=false, inspected=false, verdict=null;
let gameScore=0, correct=0, played=0, busy=false;
let releaseEvidence=null;
async function loadReleaseEvidence(){
  const packed=JSON.parse(document.getElementById('scenarioManifest').textContent);
  if(packed.compression!=='gzip-base64-v1' || typeof packed.data!=='string')throw Error('Unsupported scenario evidence format');
  if(typeof DecompressionStream!=='function')throw Error('This browser lacks built-in gzip DecompressionStream support. Use modern Safari, Chrome or Firefox.');
  const bytes=Uint8Array.from(atob(packed.data),c=>c.charCodeAt(0));
  const decoded=await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))).text();
  releaseEvidence=JSON.parse(decoded);
  if(!Array.isArray(releaseEvidence.scenarios))throw Error('Scenario evidence payload invalid');
}
const liveEvidence=new Map();
const gameEvidence=[];
function formatEvidence(){
  const items=releaseEvidence.scenarios.map(item=>({...item}));
  for(const item of items){const live=liveEvidence.get(item.id);if(live){item.observed=live.observed;item.status=live.status;item.execution=live.execution||'this-browser-Pyodide-session'}}
  return {schema:'vdmv.scenario-evidence.v1',release:{at:releaseEvidence.generated_at_utc,source_sha256:releaseEvidence.source_sha256},
    exported_at:new Date().toISOString(),records:items,played:gameEvidence.slice(),
    note:'Unit cases reflect a recorded Python release run; browser probes/game are actual session runs; pending calculator checks were not performed.'};
}
function renderScenarioLedger(){
  const all=formatEvidence().records,bank=$('scenarioFilter').value,needle=$('scenarioSearch').value.trim().toLowerCase();
  const shown=all.filter(item=>(bank==='all'||item.kind===bank)&&(!needle||[item.id,item.title,item.status,item.input,item.observed,item.expected].some(v=>(typeof v==='object'?JSON.stringify(v):String(v)).toLowerCase().includes(needle))));
  const root=$('scenarioRows');root.replaceChildren();
  for(const item of shown){
    const card=document.createElement('article');card.className='scenario-card';
    const head=document.createElement('div');head.className='scenario-head';
    const identifier=document.createElement('span');identifier.className='scenario-id';identifier.textContent=item.id;
    const result=document.createElement('span');result.className='scenario-status '+item.status;result.textContent=item.status.toUpperCase();head.append(identifier,result);
    const title=document.createElement('h3');title.textContent=item.title;
    card.append(head,title);
    for(const [name,value] of [['Intent',item.intent],['Input / case',item.input],['Expected',item.expected],['Observed',item.observed]]){
      if(!value)continue;
      const detail=document.createElement('p');const label=document.createElement('b');label.textContent=name+': ';
      const text=document.createTextNode(typeof value==='object'?JSON.stringify(value):String(value));detail.append(label,text);card.appendChild(detail);
    }
    const footer=document.createElement('div');footer.className='scenario-meta';footer.textContent=item.execution+' · '+item.source;card.appendChild(footer);
    root.appendChild(card);
  }
  $('scenarioCount').textContent=shown.length+'/'+all.length+' cases';
  const passed=all.filter(x=>x.status==='passed').length,pending=all.filter(x=>x.status==='pending').length;
  $('scenarioSummary').textContent=passed+' recorded PASS, '+pending+' external PENDING; '+shown.length+' shown. '+releaseEvidence.summary.unit+' CLI units, '+releaseEvidence.summary.probe+' browser probes, '+releaseEvidence.summary.game+' game cases, '+(releaseEvidence.summary.security_matrix||0)+' signed policy-matrix cases, '+(releaseEvidence.summary.ingress_matrix||0)+' hostile-input cases. Names/IDs are unique; logical coverage can overlap.';
}

const pretty=x=>JSON.stringify(x,null,2);
const status=(message,ready=false)=>{const el=$('runtimeStatus');el.textContent=message;el.classList.toggle('ready',ready)};
const info=(message)=>{$('loadingMask').textContent=message};
const report=(where,error)=>{where.textContent='ERROR: '+String(error);console.error(error)};
function bootScript(){return new Promise((resolve,reject)=>{
  if(window.loadPyodide)return resolve();
  const script=document.createElement('script');script.src=CDN+'pyodide.js';script.async=true;
  script.onload=resolve;script.onerror=()=>reject(Error('Pyodide CDN unavailable. Connect once or host an offline bundle of Pyodide runtime assets.'));
  document.head.appendChild(script);
});}
async function initializePython(){
  status('Starting Python/WebAssembly...');
  await bootScript();
  py=await window.loadPyodide({indexURL:CDN});
  const sources=JSON.parse($('pythonSources').textContent);
  const root='/home/py/virtual_dmv';
  py.FS.mkdirTree(root);
  for(const [name,content] of Object.entries(sources))py.FS.writeFile(root+'/'+name,content);
  py.runPython("import sys\nsys.path.insert(0,'/home/py')\nfrom virtual_dmv.engine import bridge as browser_bridge");
  let remembered=null;
  try{const raw=localStorage.getItem(storeKey);if(raw)remembered=JSON.parse(raw)}catch(e){console.warn('No saved browser data; continuing with volatile demo.',e)}
  if(remembered){const auditResponse=direct({op:'audit',state:remembered});if(auditResponse.ok){state=remembered;}else{throw Error('Saved registry failed validation: '+auditResponse.error+'; export/delete damaged storage manually before resetting.')}}
  if(!state){const r=direct({op:'bootstrap',args:{now:1893456000}});if(!r.ok)throw Error(r.error);state=r.state;save();}
  status('Python engine ready / local',true);
  $('loadingMask').classList.add('hidden');
  const b=direct({op:'casebook',state});gameCases=b.result;
  enableControls(true);await refresh();showCase();renderScenarioLedger();
}
function direct(input){
  if(!py)throw Error('Python is not ready');
  py.globals.set('vdmv_request',JSON.stringify(input));
  const raw=py.runPython('browser_bridge(vdmv_request)');
  return JSON.parse(raw);
}
function save(){try{localStorage.setItem(storeKey,JSON.stringify(state));}catch(e){console.warn('Demo state is not durably saved in this browser',e);status('Python ready / volatile state',true)}}
async function command(op,args={}){
  if(!py)throw Error('Python is still starting');
  const response=direct({op,state,args});
  if(!response.ok)throw Error(response.error);
  state=response.state;save();
  updateSummary();return response.result;
}
function enableControls(ready){document.querySelectorAll('button:not([data-tab])').forEach(x=>x.disabled=!ready)}
function updateSummary(){
  if(!state)return;
  $('receipts').textContent=state.receipts.length;
  $('receipts2').textContent=state.receipts.length;
  $('events').textContent=state.events.length;
  $('score').textContent=gameScore;
  $('correct').textContent=correct+'/'+played;
  $('plates').textContent=state.events.filter(x=>x.kind==='issue').length;
}
async function refresh(){
  const rows=await command('roster');
  $('rosterBody').replaceChildren();
  for(const p of rows){
    const tr=document.createElement('tr');
    for(const key of ['plate_id','class','owner','status']){
      const td=document.createElement('td');td.textContent=p[key];tr.appendChild(td);
    }
    tr.addEventListener('click',()=>{$('plateId').value=p.plate_id;$('owner').value=p.owner;activateTab('registry');});
    $('rosterBody').appendChild(tr);
  }
  for(const sel of [$('owner'),$('newOwner')]){
    const previous=sel.value;sel.replaceChildren();
    for(const name of Object.keys(state.owners)){
      const opt=document.createElement('option');opt.textContent=name;sel.appendChild(opt);
    }
    if(previous in state.owners)sel.value=previous;
  }
  updateSummary();
  const cards=$('policyCards');cards.replaceChildren();
  for(const [name,policy] of Object.entries(state.policies)){
    const panel=document.createElement('div');panel.className='paper';
    const title=document.createElement('strong');title.textContent=name;
    const text=document.createElement('p');text.className='small';text.textContent=policy.description;
    const permissions=document.createElement('div');permissions.className='small';permissions.textContent='Anonymous: '+(policy.anonymous.join(', ')||'none')+' | Registered: '+Object.entries(policy.allows).map(([k,v])=>k+' → '+v.join('/')).join(' · ');
    panel.append(title,text,permissions);cards.appendChild(panel);
  }
}
function showCase(){
  if(!gameCases.length)return;
  if(caseIndex>=gameCases.length){
    $('trafficLabel').textContent='Shift completed. Review your decisions or reset the challenge.';
    $('trafficMeta').textContent=played+' decisions · score '+gameScore;
    $('gameRound').textContent='SHIFT COMPLETE';
    for(const id of ['inspect','chooseAllow','chooseDeny','nextCase'])$(id).disabled=true;
    return;
  }
  const c=gameCases[caseIndex];verdict=null;inspected=false;gameResolved=false;
  $('trafficLabel').textContent=c.label;
  $('trafficMeta').textContent=c.id+' · '+c.plate+' · '+c.action.toUpperCase()+' · '+c.resource;
  $('gameRound').textContent='CASE '+(caseIndex+1)+' / '+gameCases.length;
  $('gameFeedback').textContent='Review the request and decide. You can pay two points for the signed-gate verdict.';
  $('gameFeedback').className='feedback';
  for(const id of ['inspect','chooseAllow','chooseDeny'])$(id).disabled=false;
  $('nextCase').disabled=true;
}
async function inspect(){
  if(inspected||gameResolved)return;
  try{
    const replay=await command('game_try',{index:caseIndex});
    verdict=replay.decision;
    if(replay.scenario_matches_expectation===false)throw Error('SCENARIO ORACLE MISMATCH: game fixture disagrees with its expected result');
    inspected=true;gameScore-=2;updateSummary();
    $('gameLast').textContent=pretty(verdict);
    $('gameFeedback').textContent='Gate: '+verdict.reason+' — '+(verdict.allow?'eligible':'ineligible')+'. This audit inspection cost 2 points.';
    $('inspect').disabled=true;
  }catch(e){report($('gameLast'),e)}
}
async function choose(allow){
  if(gameResolved)return;
  try{
    if(!verdict){
      const replay=await command('game_try',{index:caseIndex});
      verdict=replay.decision;
      if(replay.scenario_matches_expectation===false)throw Error('SCENARIO ORACLE MISMATCH: refuse scoring until regression is fixed');
    }
    gameResolved=true;played++;
    const right=allow===gameCases[caseIndex].expected_allow;
    const g=gameCases[caseIndex];
    gameEvidence.push({id:g.id,choice:allow?'ADMIT':'DENY',expected:g.expected,
      observed:(verdict.allow?'ADMIT':'DENY')+' / '+verdict.reason,correct:right,inspected,at:new Date().toISOString()});
    liveEvidence.set(g.id,{status:'passed',observed:(verdict.allow?'ADMIT':'DENY')+' / '+verdict.reason});
    renderScenarioLedger();
    if(right){correct++;gameScore+=10;}else gameScore-=8;
    updateSummary();
    $('gameLast').textContent=pretty(verdict);
    const feedback=$('gameFeedback');feedback.className='feedback '+(right?'good':'bad');
    feedback.textContent=(right?'Correct +10. ':'Incorrect −8. ') +gameCases[caseIndex].truth+' Gate reason: '+verdict.reason+'.';
    for(const id of ['inspect','chooseAllow','chooseDeny'])$(id).disabled=true;
    $('nextCase').disabled=false;
  }catch(e){report($('gameLast'),e)}
}
function resetGame(){caseIndex=0;gameScore=0;correct=0;played=0;gameEvidence.length=0;updateSummary();showCase()}
function activateTab(name){
  document.querySelectorAll('[data-tab]').forEach(el=>el.setAttribute('aria-selected',el.dataset.tab===name?'true':'false'));
  document.querySelectorAll('.view').forEach(el=>el.classList.toggle('active',el.id===name));
}
async function actionOperation(op,args={}){
  if(busy)return;busy=true;
  $('operationOutput').textContent='Python processing '+op+' ...';
  try{
    const result=await command(op,args);
    $('operationOutput').textContent=pretty(result);
    await refresh();
  }catch(e){report($('operationOutput'),e)}finally{busy=false}
}
const uiArgs=()=>({owner:$('owner').value,old_owner:$('owner').value,new_owner:$('newOwner').value,role:$('role').value,plate_id:$('plateId').value.trim(),resource:$('resource').value,action:$('action').value,now:state.created_at});
function download(filename,data){
  const url=URL.createObjectURL(new Blob([data],{type:'application/json'}));
  const a=document.createElement('a');a.href=url;a.download=filename;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
async function importState(file){
  if(!file)return;
  try{
    if(file.size>3_000_000)throw Error('JSON over 3 MB refused');
    const parsed=JSON.parse(await file.text());
    const result=direct({op:'audit',state:parsed});
    if(!result.ok)throw Error('Incoming state failed audit: '+result.error);
    state=parsed;save();await refresh();$('operationOutput').textContent='Imported local test state. '+pretty(result.result);
  }catch(e){report($('operationOutput'),e)}finally{$('importFile').value=''}
}
async function runBench(){
  const target=$('benchRows');target.textContent='Python executing regression scenarios ...';
  try{
    const result=await command('bench');target.replaceChildren();
    const summary=document.createElement('p');summary.className=result.passed===result.total?'pass':'fail';summary.textContent=result.passed+'/'+result.total+' Python probes passed';target.appendChild(summary);
    for(const item of result.cases){
      const line=document.createElement('div');line.className='checkrow';const name=document.createElement('span');
      name.textContent=item.id+' · '+item.name;const outcome=document.createElement('strong');outcome.className=item.pass?'pass':'fail';outcome.textContent=item.pass?'PASS':'FAIL';line.append(name,outcome);target.appendChild(line);
      liveEvidence.set(item.id,{status:item.pass?'passed':'failed',observed:item.observed+(item.error?' — '+item.error:'')});
    }
    renderScenarioLedger();
  }catch(e){report(target,e)}
}
async function replayAllGameScenarios(){
  const label=$('gameSuiteSummary');label.textContent='Python replaying '+gameCases.length+' isolated scenarios ...';
  try{
    let passed=0;const seen=new Set();
    for(let index=0;index<gameCases.length;index++){
      const item=await command('game_try',{index});
      const id=item.case.id;
      if(seen.has(id))throw Error('Repeated game scenario '+id);
      seen.add(id);
      const ok=item.scenario_matches_expectation===true && item.isolated===true;
      if(ok)passed++;
      liveEvidence.set(id,{status:ok?'passed':'failed',observed:(item.decision.allow?'ADMIT':'DENY')+' / '+item.decision.reason});
    }
    label.className=passed===gameCases.length?'pass':'fail';
    label.textContent=passed+'/'+gameCases.length+' Python game oracles passed. All '+gameCases.length+' isolated; unique IDs '+seen.size+'. Existing DMV records unchanged.';
    renderScenarioLedger();
  }catch(e){report(label,e)}
}

function calculatorBatchScript(){
  const tests=releaseEvidence.scenarios.filter(x=>x.kind==='mitchell_tech_manual')
    .map(x=>({id:x.id,expression:x.input}));
  return `(() => {
const calc=window.MitchellTech;
if(!calc||typeof calc.calculate!=='function')throw Error('Open Mitchell Tech V120.2 first');
const cases=${JSON.stringify(tests)}.map(q=>({...q,result:calc.calculate(q.expression)}));
const output=JSON.stringify({schema:'vdmv.mitchelltech.v1',source:'window.MitchellTech.calculate',cases},null,2);
console.log(output);
if(navigator.clipboard?.writeText)navigator.clipboard.writeText(output).catch(()=>{});
return output;
})();`;
}
async function copyCalculator(){
  const script=calculatorBatchScript();
  try{await navigator.clipboard.writeText(script);$('calculatorStatus').textContent='Batch script copied. Paste into the JavaScript console on Mitchell Tech (not this site).';}
  catch(e){$('calculatorResults').value=script;$('calculatorStatus').textContent='Clipboard unavailable; batch script placed in the text area so you can copy it manually.';}
}
function checkCalculator(){
  try{
    const raw=$('calculatorResults').value;
    if(raw.length>40000)throw Error('Imported calculator report too large');
    const data=JSON.parse(raw);
    if(data.schema!=='vdmv.mitchelltech.v1'||data.source!=='window.MitchellTech.calculate'||!Array.isArray(data.cases))throw Error('Wrong report format');
    const expected=releaseEvidence.scenarios.filter(x=>x.kind==='mitchell_tech_manual');
    const received=new Map();
    for(const item of data.cases){if(!item||typeof item.id!=='string'||received.has(item.id))throw Error('Duplicate or malformed calculator result');received.set(item.id,item)}
    if(received.size!==expected.length)throw Error('Expected exactly '+expected.length+' distinct calculator results');
    let passed=0;
    for(const spec of expected){
      const found=received.get(spec.id);
      if(!found||found.expression!==spec.input)throw Error('ID/expression mismatch: '+spec.id);
      const value=found.result?.value;
      const okay=found.result?.ok===true&&typeof value==='number'&&Number.isFinite(value)&&Math.abs(value-Number(spec.expected))<1e-8;
      if(okay)passed++;
      liveEvidence.set(spec.id,{status:okay?'passed':'failed',observed:okay?'Mitchell Tech user-imported '+value:'Unexpected result: '+JSON.stringify(found.result),execution:'operator-submitted-Mitchell-Tech-JSON'});
    }
    $('calculatorStatus').className=passed===expected.length?'pass':'fail';
    $('calculatorStatus').textContent=passed+'/'+expected.length+' unique arithmetic checks matched. USER-SUBMITTED OUTPUT: this page cannot authenticate the other site or the reporter.';
    renderScenarioLedger();
  }catch(e){report($('calculatorStatus'),e)}
}

async function runEconomics(comparison){
  const root=$('economicsView');root.replaceChildren();
  try{
    const values=comparison?[0,.25,.5,.75,1]:[Number($('adoption').value)/100];
    for(const adoption of values){
      const result=await command('economics',{rounds:200,seed:7,adoption});
      const row=document.createElement('div');row.className='paper';
      const heading=document.createElement('div');heading.className='flex-between';
      const title=document.createElement('strong');title.textContent=Math.round(adoption*100)+'% registered';
      const value=document.createElement('strong');value.textContent=result.accepted+'/200 admitted';heading.append(title,value);
      const bar=document.createElement('div');bar.className='chartbar';const fill=document.createElement('span');fill.style.width=result.accepted/2+'%';bar.append(fill);
      const caption=document.createElement('p');caption.className='small';caption.textContent='Synthetic gross utility '+result.gross_access_utility+'; registration cost '+result.registration_cost+'; modeled net '+result.net_model_utility;
      row.append(heading,bar,caption);root.appendChild(row);
    }
  }catch(e){report(root,e)}
}
function wire(){
  document.querySelectorAll('[data-tab]').forEach(el=>el.addEventListener('click',()=>activateTab(el.dataset.tab)));
  $('inspect').addEventListener('click',inspect);
  $('chooseAllow').addEventListener('click',()=>choose(true));$('chooseDeny').addEventListener('click',()=>choose(false));
  $('nextCase').addEventListener('click',()=>{caseIndex++;showCase()});$('resetGame').addEventListener('click',resetGame);
  $('gateRequest').addEventListener('click',()=>actionOperation('request',uiArgs()));
  $('issuePlate').addEventListener('click',()=>actionOperation('issue',uiArgs()));
  $('renewPlate').addEventListener('click',()=>actionOperation('renew',uiArgs()));
  $('transferPlate').addEventListener('click',()=>actionOperation('transfer',uiArgs()));
  $('revokePlate').addEventListener('click',()=>actionOperation('revoke',uiArgs()));
  $('auditNow').addEventListener('click',()=>actionOperation('audit'));
  $('addOwner').addEventListener('click',()=>actionOperation('owner',{name:$('addOwnerName').value.trim()}));
  $('exportState').addEventListener('click',()=>download('virtual-dmv-demo-state.json',pretty(state)));
  $('importButton').addEventListener('click',()=>$('importFile').click());
  $('importFile').addEventListener('change',()=>importState($('importFile').files[0]));
  $('resetLab').addEventListener('click',()=>{if(!confirm('Discard the local demo journal and reset all test identities?'))return;try{localStorage.removeItem(storeKey);state=null;const r=direct({op:'bootstrap'});if(!r.ok)throw Error(r.error);state=r.state;save();resetGame();refresh();$('operationOutput').textContent='Reset to fresh simulation.'}catch(e){report($('operationOutput'),e)}});
  $('runBench').addEventListener('click',runBench);
  $('runGameSuite').addEventListener('click',replayAllGameScenarios);
  for(const id of ['exportEvidence','exportEvidenceLedger'])$(id).addEventListener('click',()=>download('virtual-dmv-scenario-evidence.json',pretty(formatEvidence())));
  $('scenarioFilter').addEventListener('change',renderScenarioLedger);
  $('scenarioSearch').addEventListener('input',renderScenarioLedger);
  $('copyCalculator').addEventListener('click',copyCalculator);
  $('checkCalculator').addEventListener('click',checkCalculator);
  renderScenarioLedger();
  $('adoption').addEventListener('input',()=>{$('adoptionValue').textContent=$('adoption').value+'%'});
  $('runEconomic').addEventListener('click',()=>runEconomics(false));$('compareEconomic').addEventListener('click',()=>runEconomics(true));
}
const ready=new Promise((resolve,reject)=>{
  window.addEventListener('DOMContentLoaded',async()=>{
    enableControls(false);
    try{await loadReleaseEvidence();wire();await initializePython();resolve(true)}catch(e){status('Python failed to load');info('STARTUP FAILURE: '+e.message+' — Internet and a browser supporting WebAssembly are required for this CDN-loaded Python runtime. Refresh when available.');reject(e)}
  },{once:true});
});
window.VirtualDMV=Object.freeze({version:'0.6.0',ready:()=>ready,command:async(op,args)=>{await ready;return command(op,args)},snapshot:()=>structuredClone(state),help:()=>['roster','audit','owner','issue','renew','transfer','revoke','request','policy','policies','casebook','game_try','economics','bench'],
  warning:'This is a page-local test engine. Calling it does not authenticate to remote resource hosts.'});
})();
