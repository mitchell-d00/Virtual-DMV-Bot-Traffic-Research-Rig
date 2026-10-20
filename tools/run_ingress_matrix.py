"""A deterministic, deduplicated invalid-input and valid-unknown-plate matrix.

The matrix checks request admission and safe denial, not remote HTTP handling.
Each case runs in an isolated registry and is labeled with explicit boundaries.
"""
from __future__ import annotations
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from virtual_dmv import engine as E

NOW=1893456000
GOOD='VDMV-RESEARCH-01'
CASES=[]
def case(label, plate=GOOD, resource='research-library', action='crawl', expected='reject'):
    CASES.append((label,plate,resource,action,expected))

for label,plate in [('null',None),('list',[]),('dict',{}),('zero',0),('bool',True),('empty',''),
  ('nul','VDMV\x00INJECT'),('whitespace','VDMV INJECT'),('newline','VDMV\nINJECT'),
  ('cyrillic','VDMV-\u0430BC'),('accent','VDMV-\u00e9'),('zero-width','VDMV-\u200bLAB')]:
    case('bad plate '+label,plate=plate)
for k in range(73,86):
    case('oversized plate '+str(k),plate='P'*k)
for label,resource in [('list',[]),('dict',{}),('null',None),('bool',True),('integer',7),('missing','unregistered-library')]:
    case('bad resource '+label,resource=resource)
for label,action in [('list',[]),('dict',{}),('null',None),('bool',True),('integer',42),('missing','exfiltrate')]:
    case('bad action '+label,action=action)
for i in range(12):
    case('safe unknown '+str(i),plate=f'VDMV-UNREGISTERED-{i:02d}',expected='unknown')
case('known research allowed',expected='allow')

def check_matrix():
    rows=[]
    for i,(label,plate,resource,action,expected) in enumerate(CASES,1):
        state=E.bootstrap(seed=f'ingress-matrix-v06-{i}',now=NOW)
        before=(len(state['challenges']),state['sequence_nonce'])
        observed={};ok=False
        try:
            c=E.challenge(state,plate,resource,action,now=NOW)
            d=E.decide(state,c,E.holder_proof(state,'alice',c) if expected=='allow' else '',now=NOW)
            observed={'allow':d['allow'],'reason':d['reason'],'signed_receipt':E.verify_receipts(state)['ok']}
            ok=(expected=='unknown' and not d['allow'] and d['reason']=='UNKNOWN_OR_REVOKED') or (expected=='allow' and d['allow'] and d['reason']=='POLICY_ALLOW')
        except E.ProtocolError as e:
            observed={'exception':'ProtocolError','message':str(e)}
            ok=(expected=='reject' and (len(state['challenges']),state['sequence_nonce'])==before)
        except Exception as e:
            observed={'exception':type(e).__name__,'message':str(e)}
        rows.append({'id':f'INGRESS-{i:03d}','kind':'traffic_ingress_matrix','title':label,
          'intent':'Check preallocation input validity and either deny unknown plate with signed receipt or admit a known plate.',
          'input':{'plate':plate,'resource':resource,'action':action},
          'expected':expected,'observed':observed,'status':'passed' if ok else 'failed',
          'source':'tools/run_ingress_matrix.py','execution':'recorded-local-python-security-matrix',
          'overlap_note':'Each deterministic local input is unique; these are protocol tests, not HTTP field measurements.'})
    keys=[json.dumps(r['input'],sort_keys=True,ensure_ascii=True) for r in rows]
    if len(set(keys))!=len(keys):raise AssertionError('Duplicate attack tuple in ingress matrix')
    if len({r['id'] for r in rows})!=len(rows):raise AssertionError('Duplicate ingress scenario ID')
    return rows

if __name__=='__main__':
    rows=check_matrix()
    Path(ROOT/'evaluation'/'INGRESS-MATRIX-V06.json').write_text(json.dumps({'schema':'vdmv.ingress.v1','scenarios':rows},indent=2,ensure_ascii=False)+'\n')
    passed=sum(x['status']=='passed' for x in rows)
    print(f'v0.6 ingress: {passed}/{len(rows)} distinct scenarios passed')
    if passed!=len(rows):sys.exit(1)
