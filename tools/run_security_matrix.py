"""Enumerate a bounded, distinct resource/class/action access-control matrix.

This is specification conformance over synthetic traffic, NOT an independent
cryptographic audit, field observation or proof of legal usage rights.
"""
from __future__ import annotations
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from virtual_dmv import engine as E

NOW=1893456000


def check_matrix():
    state=E.bootstrap(seed='crypto-policy-matrix-v05',now=NOW)
    ids={}
    for role in E.CLASSES:
        ids[role]=f'VDMV-MATRIX-{role.upper()}'
        E.issue(state,'alice',role,plate_id=ids[role],now=NOW)
    rows=[]
    n=0
    for resource,policy in sorted(state['policies'].items()):
        for role in (*E.CLASSES,'anonymous'):
            for action in E.ACTIONS:
                n+=1
                plate='anonymous' if role=='anonymous' else ids[role]
                owner=None if role=='anonymous' else 'alice'
                decision=E.request(state,plate,resource,action,owner=owner,now=NOW)
                allowed=(action in policy['anonymous']) if role=='anonymous' else (role in policy['allows'].get(action,[]))
                attribution=bool(allowed and action in policy['attribution'])
                reason=('ANONYMOUS_POLICY_ALLOW' if allowed else 'ANONYMOUS_DEFAULT_DENY') if role=='anonymous' else ('POLICY_ALLOW' if allowed else 'POLICY_DENY')
                ok=(decision['allow']==allowed and decision['attribution_required']==attribution and decision['reason']==reason and 'receipt_hash' in decision)
                rows.append({'id':f'MATRIX-{n:03d}','kind':'security_policy_matrix',
                    'title':f'{resource} / {role} / {action}',
                    'intent':'Exercise resource, machine class and requested action with fresh signed challenge and receipt.',
                    'input':{'resource':resource,'role':role,'action':action},
                    'expected':{'allow':allowed,'reason':reason,'attribution':attribution},
                    'observed':{'allow':decision['allow'],'reason':decision['reason'],'attribution':decision['attribution_required'],'receipt_hash':decision['receipt_hash']},
                    'status':'passed' if ok else 'failed',
                    'source':'tools/run_security_matrix.py',
                    'execution':'recorded-local-python-security-matrix',
                    'overlap_note':'An exhaustively enumerated policy tuple, not an independent security study.'})
    evidence=E.verify_receipts(state)
    keys=[(r['input']['resource'],r['input']['role'],r['input']['action']) for r in rows]
    if len(set(keys))!=len(keys):raise AssertionError('duplicate traffic tuple')
    if not evidence['ok'] or evidence['count']!=len(rows):raise AssertionError('receipt chain mismatch')
    return rows


if __name__=='__main__':
    rows=check_matrix()
    passed=sum(row['status']=='passed' for row in rows)
    print(f'policy-matrix: {passed}/{len(rows)} pass, unique tuples={len(set(str(r["input"]) for r in rows))}')
    if passed!=len(rows):sys.exit(1)
