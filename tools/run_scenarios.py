"""Run unique, inspectable test scenarios; write a documented release snapshot.

Full unit suite runs on desktop Python. The public Pyodide lab replays the 12
Python browser probes and 10 game fixtures; desktop-only tests remain archived
as a versioned evidence snapshot, never implied to have run in the browser.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import unittest
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from virtual_dmv import engine as E

class EvidenceResult(unittest.TestResult):
    def __init__(self):
        super().__init__()
        self.outcomes={}
    def addSuccess(self,test):
        super().addSuccess(test)
        self.outcomes[test.id()]=('passed','All assertions passed')
    def addFailure(self,test,err):
        super().addFailure(test,err)
        self.outcomes[test.id()]=('failed',self._exc_info_to_string(err,test)[-1100:])
    def addError(self,test,err):
        super().addError(test,err)
        self.outcomes[test.id()]=('error',self._exc_info_to_string(err,test)[-1100:])
    def addSkip(self,test,reason):
        super().addSkip(test,reason)
        self.outcomes[test.id()]=('skipped',reason)

def hash_files(paths):
    digest=hashlib.sha256()
    for item in paths:
        digest.update(str(item).encode()+b'\0'+(ROOT/item).read_bytes()+b'\0')
    return digest.hexdigest()

def checked():
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_*.py',top_level_dir=str(ROOT/'tests'))
    def flatten(suite):
        for item in suite:
            if isinstance(item,unittest.TestSuite):yield from flatten(item)
            else:yield item
    tests=list(flatten(suite))
    result=EvidenceResult()
    for t in tests:t.run(result)
    if len(result.outcomes)!=len(tests):raise RuntimeError('Some unit tests lack results')
    units=[]
    for i,t in enumerate(tests,1):
        key=t.id()
        status,detail=result.outcomes[key]
        name=t._testMethodName.removeprefix('test_').replace('_',' ')
        units.append({'id':f'UNIT-{i:03d}','kind':'python_unittest','title':name,
          'intent':name.capitalize(),'input':key,'expected':'The named assertions in '+key+' all pass',
          'observed':detail,'status':status,'source':'tests/'+key.split('.')[0]+'.py',
          'execution':'recorded-local-python','overlap_note':'May test the same rule as a browser probe or game case'})
    bench=E.run_bench()
    probes=[{'id':p['id'],'kind':'browser_python_probe','title':p['name'],
       'intent':'Adversarial Python gate probe: '+p['name'],
       'input':p['name'],'expected':p['expected'],'observed':p['observed'],
       'status':'passed' if p['pass'] else 'failed','source':'src/virtual_dmv/engine.py#run_bench',
       'execution':'run-locally-and-rerunnable-in-browser'} for p in bench['cases']]
    game=[]
    for i,c in enumerate(E.traffic_cases()):
        a=E.dispatch({'op':'game_try','state':E.bootstrap(seed='archive',now=1893456000),'args':{'index':i}})['result']
        d=a['decision']
        good=a['scenario_matches_expectation']
        game.append({'id':c['id'],'kind':'playable_game','title':c['label'],
          'intent':c['truth'],'input':f"{c['plate']} / {c['resource']} / {c['action']}",
          'expected':c['expected']+' / '+c['expected_reason'],
          'observed':('ADMIT' if d['allow'] else 'DENY')+' / '+d['reason'],
          'status':'passed' if good else 'failed',
          'source':'src/virtual_dmv/engine.py#traffic_cases',
          'execution':'run-locally-and-rerunnable-in-browser'})
    all_cases=units+probes+game
    ids=[p['id'] for p in all_cases]
    if len(ids)!=len(set(ids)):raise RuntimeError('Duplicated public scenario ID')
    names=[(p['kind'],p['title'].casefold().strip()) for p in all_cases]
    if len(names)!=len(set(names)):raise RuntimeError('Duplicated public scenario title in one bank')
    # Make every numerical question distinct; calculator checks are NOT recorded as tested.
    formulas=[]
    for adoption in [0,.25,.5,.75,1]:
        r=E.economics_simulation(E.bootstrap(seed='calc',now=1893456000),rounds=200,seed=7,adoption=adoption)
        expr=f"{r['accepted']}*5-{r['registration_cost']}"
        formulas.append({'id':f'CALC-{len(formulas)+1:03d}','kind':'mitchell_tech_manual',
            'title':f"Economics net utility at {int(adoption*100)}% adoption",'input':expr,
            'expected':str(r['net_model_utility']),'observed':'not run in Mitchell Tech browser',
            'status':'pending','source':'evaluation/CALCULATOR-CROSSCHECK.md',
            'execution':'requires-console-in-Mitchell-Tech'})
    if len({x['input'] for x in formulas})!=len(formulas):raise RuntimeError('Calculator expressions are repeated')
    timestamp=datetime.now(timezone.utc).isoformat(timespec='seconds')
    artifact={'schema':'vdmv.scenarios.v1','generated_at_utc':timestamp,
        'source_sha256':hash_files([Path('src/virtual_dmv/engine.py'),Path('src/virtual_dmv/portable.py'),Path('tests/test_engine.py'),Path('tests/test_bundle.py'),Path('tools/run_scenarios.py')]),
        'summary':{'unit':len(units),'probe':len(probes),'game':len(game),'calculator_pending':len(formulas),
                   'recorded_passed':sum(c['status']=='passed' for c in all_cases),
                   'recorded_failed':sum(c['status'] in ('failed','error') for c in all_cases),
                   'unique_executed_scenario_ids':len(all_cases),
                   'notice':'Counts are distinct documented scenario IDs, NOT independent experimental findings. Cross-bank behavior overlaps.'},
        'scenarios':all_cases+formulas,
        'limits':{'unit':'Recorded on local Python at source_sha256; not executed in each visitor browser.',
                  'probe':'Browser reruns real Python using the embedded engine; results may differ if code changes.',
                  'game':'Synthetic isolated deterministic state; gameplay is not a field trial.',
                  'calculator':'Requires external Mitchell Tech app and a separate user-triggered manual console check. Pending does not count as a pass.'}}
    out=ROOT/'evaluation'/'SCENARIO-RESULTS.json'
    out.write_text(json.dumps(artifact,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f"Evidence: {len(units)} local unit, {len(probes)} Python browser, {len(game)} game, {len(formulas)} pending external calculator")
    print(f"Recorded passed: {artifact['summary']['recorded_passed']}, failures: {artifact['summary']['recorded_failed']}")
    return not(result.wasSuccessful() and not artifact['summary']['recorded_failed'])

if __name__=='__main__':sys.exit(checked())
