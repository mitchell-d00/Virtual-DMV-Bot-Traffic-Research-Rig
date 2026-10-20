"""Direct, inspectable governance exercise; no external files or network."""
import json
from virtual_dmv.engine import bootstrap,request,transfer,revoke,audit_all

state=bootstrap(seed='public-demo-fixture',now=1893456000)
print('Research crawl:',request(state,'VDMV-RESEARCH-01','research-library','crawl',owner='alice',now=1893456000)['reason'])
print('Crawler train:',request(state,'VDMV-CRAWLER-02','licensed-training-data','train',owner='bob',now=1893456000)['reason'])
print('Unknown open:',request(state,'anonymous','open-index','crawl',now=1893456000)['reason'])
transfer(state,'VDMV-RESEARCH-01','alice','bob',now=1893456000)
print('Old owner:',request(state,'VDMV-RESEARCH-01','research-library','crawl',owner='alice',now=1893456000)['reason'])
print('New owner:',request(state,'VDMV-RESEARCH-01','research-library','crawl',owner='bob',now=1893456000)['reason'])
revoke(state,'VDMV-RESEARCH-01',now=1893456000)
print('Revoked:',request(state,'VDMV-RESEARCH-01','research-library','crawl',owner='bob',now=1893456000)['reason'])
print(json.dumps(audit_all(state),indent=2))
