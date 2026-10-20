"""Virtual DMV: local reference engine for experimental machine participation.

All permissions are DEMO decisions over invented resources. Signed demo plates
are NOT real authorization, legal contracts, website rights, or real identities.
This code is intended for offline testing and falsification, not production.
"""
import copy
import hashlib
import json
import secrets
import time
from .portable import b64, canonical, make_seed, public_key, sha256, sign, verify

SCHEMA = "virtual-dmv.lab.v1"
CLASSES = ("crawler", "research", "commercial", "archival", "agentic")
ACTIONS = ("discover", "crawl", "index", "summarize", "train", "redistribute", "archive")
Z = "0" * 64

POLICIES = {
 "open-archive": {"description":"Public discovery with scoped machine use; attribution for summaries.",
   "anonymous":["discover"], "allows":{"discover":list(CLASSES),"crawl":["crawler","research","archival"],"index":["crawler","archival"],"summarize":["research","archival","agentic"]}, "attribution":["summarize"]},
 "research-library": {"description":"Research library: registered research crawling; archival conservation.",
   "anonymous":[], "allows":{"crawl":["research"],"summarize":["research"],"archive":["archival"]}, "attribution":["summarize","archive"]},
 "licensed-training-data": {"description":"Training is reserved to registered research plates (demo only).",
   "anonymous":[], "allows":{"train":["research"],"crawl":["research"]},"attribution":[]},
 "open-index": {"description":"Open and explicitly permissionless discovery and indexing.",
   "anonymous":["discover","crawl","index"],"allows":{"discover":list(CLASSES),"crawl":list(CLASSES),"index":list(CLASSES)},"attribution":[]}
}

class ProtocolError(ValueError):
    pass


def _need(condition, message):
    if not condition:
        raise ProtocolError(message)


def _named(value):
    return isinstance(value, str) and 1 <= len(value) <= 72 and all(c.isalnum() or c in "-_." for c in value)


def _clock(now=None):
    v = int(time.time() if now is None else now)
    _need(0 <= v <= 4102444800, "invalid demo timestamp")
    return v


def new_state(*, seed=None, now=None):
    """Private demo keys live IN state, and are exported with it. Never use real keys."""
    if seed is not None:
        # For reproducible test fixtures only: NOT SECURE OR PRIVATE.
        def derived(label):
            return b64(hashlib.sha256((str(seed)+"/"+label).encode()).digest())
        issuer_seed, host_seed = derived("issuer"), derived("host")
    else:
        issuer_seed, host_seed = make_seed(), make_seed()
    return {"schema":SCHEMA,"created_at":_clock(now),
      "issuer":{"id":"virtual-dmv-lab", "seed":issuer_seed,"public_key":public_key(issuer_seed)},
      "host":{"id":"local-resource-owner", "seed":host_seed,"public_key":public_key(host_seed)},
      "owners":{},"policies":copy.deepcopy(POLICIES),"events":[],"receipts":[],"challenges":{},"sequence_nonce":0,
      "note":"Research simulation. All secrets in state; no real authorization or production security."}


def add_owner(state, label, *, seed=None):
    _need(_named(label), "owner label must be 1-72 safe characters")
    _need(label not in state["owners"], "owner label already registered")
    key = seed or make_seed()
    state["owners"][label] = {"seed":key,"public_key":public_key(key)}
    return {"owner":label,"public_key":state["owners"][label]["public_key"]}


def _signed(seed, body):
    return {"payload":body,"signature":sign(seed,body)}


def _event(state, kind, details):
    body={"schema":"vdmv.event.v1","sequence":len(state["events"])+1,
       "previous_hash":state["events"][-1]["hash"] if state["events"] else Z,
       "kind":kind,"data":copy.deepcopy(details)}
    event={**body,"signature":sign(state["issuer"]["seed"],body)}
    event["hash"]=sha256(event)
    state["events"].append(event)
    return event


def _validate_credential(credential, issuer_public, issuer_id):
    _need(isinstance(credential,dict) and isinstance(credential.get("payload"),dict), "malformed plate")
    p=credential["payload"]
    _need(p.get("schema")=="vdmv.plate.v1" and p.get("issuer")==issuer_id, "invalid plate schema/issuer")
    _need(_named(p.get("plate_id")) and p.get("participation_class") in CLASSES, "invalid plate ID/class")
    _need(isinstance(p.get("revision"),int) and p["revision"]>=1,"invalid plate revision")
    _need(isinstance(p.get("issued_at"),int) and isinstance(p.get("expires_at"),int) and p["expires_at"]>p["issued_at"],"invalid plate validity")
    _need(isinstance(p.get("owner_public_key"),str),"owner key missing")
    _need(verify(issuer_public,p,credential.get("signature")),"bad plate signature")
    return p


def audit(state):
    """Replay complete authenticated transition chain from public issuer key.

    Does not prove chain completeness without a published external checkpoint;
    compromised issuer or private state is out of scope.
    """
    _need(state.get("schema")==SCHEMA,"invalid registry schema")
    issuer = state["issuer"]["public_key"]
    _need(public_key(state["issuer"]["seed"])==issuer, "issuer seed/public mismatch")
    known={}
    last=Z
    for n,e in enumerate(state.get("events",[]),1):
        _need(isinstance(e,dict),"bad event")
        core={k:v for k,v in e.items() if k not in ("signature","hash")}
        _need(e.get("sequence")==n and e.get("previous_hash")==last, "event chain sequence/parent mismatch")
        _need(e.get("hash")==sha256({**core,"signature":e.get("signature")}),"event hash mismatch")
        _need(verify(issuer,core,e.get("signature")),"event issuer signature invalid")
        kind,data=e.get("kind"),e.get("data")
        _need(isinstance(data,dict),"event data invalid")
        if kind=="issue":
            plate=data.get("credential")
            p=_validate_credential(plate,issuer,state["issuer"]["id"])
            ident=p["plate_id"]
            _need(p["revision"]==1 and ident not in known,"duplicate or invalid issue")
            known[ident]={"status":"active","credential":plate,"events":n}
        elif kind in ("renew","transfer"):
            plate=data.get("credential")
            p=_validate_credential(plate,issuer,state["issuer"]["id"])
            old=known.get(p["plate_id"])
            _need(old is not None and old["status"]=="active","inactive transition")
            previous=old["credential"]["payload"]
            _need(p["revision"]==previous["revision"]+1 and p["participation_class"]==previous["participation_class"],"invalid successor revision/class")
            _need(p["issued_at"]>=previous["issued_at"],"nonmonotonic transition time")
            if kind=="renew":
                _need(p["owner_public_key"]==previous["owner_public_key"],"renew altered owner")
            else:
                _need(p["owner_public_key"]!=previous["owner_public_key"],"transfer must change owner")
            intent=data.get("owner_intent",{})
            intent_payload=intent.get("payload",{}) if isinstance(intent,dict) else {}
            _need(intent_payload.get("schema")=="vdmv.owner-intent.v1" and intent_payload.get("kind")==kind
              and intent_payload.get("plate_id")==p["plate_id"] and intent_payload.get("from_revision")==previous["revision"],"owner intent mismatch")
            if kind=="transfer":
                _need(intent_payload.get("new_owner_public_key")==p["owner_public_key"],"transfer target mismatch")
                acceptance=data.get("new_owner_acceptance",{})
                accept_payload=acceptance.get("payload",{}) if isinstance(acceptance,dict) else {}
                _need(accept_payload.get("schema")=="vdmv.acceptance.v1"
                  and accept_payload.get("plate_id")==p["plate_id"]
                  and accept_payload.get("from_revision")==previous["revision"]
                  and accept_payload.get("new_owner_public_key")==p["owner_public_key"],"incoming owner acceptance mismatch")
                _need(verify(p["owner_public_key"],accept_payload,acceptance.get("signature")),"new owner did not accept transfer")
            _need(verify(previous["owner_public_key"],intent_payload,intent.get("signature")),"owner authorization failed")
            known[p["plate_id"]]={"status":"active","credential":plate,"events":n}
        elif kind=="revoke":
            ident=data.get("plate_id"); old=known.get(ident)
            _need(old is not None and old["status"]=="active","invalid revocation")
            _need(data.get("from_revision")==old["credential"]["payload"]["revision"],"stale revocation")
            known[ident]={**old,"status":"revoked","events":n}
        else:
            raise ProtocolError("unknown signed event type")
        last=e["hash"]
    return known


def issue(state, owner, role, *, now=None, ttl=86400, plate_id=None):
    known=audit(state)
    _need(owner in state["owners"],"owner not registered")
    _need(role in CLASSES,"unknown participation class")
    _need(isinstance(ttl,int) and 0<ttl<=31536000,"invalid credential lifetime")
    stamp=_clock(now)
    plate_id=plate_id or ("VDMV-"+secrets.token_hex(7).upper())
    _need(_named(plate_id) and plate_id not in known,"duplicate or invalid plate identifier")
    payload={"schema":"vdmv.plate.v1","plate_id":plate_id,"issuer":state["issuer"]["id"],
      "participation_class":role,"owner_public_key":state["owners"][owner]["public_key"],
      "revision":1,"issued_at":stamp,"expires_at":stamp+ttl}
    credential=_signed(state["issuer"]["seed"],payload)
    _event(state,"issue",{"credential":credential})
    return credential


def _transition(state, kind, plate_id, old_owner, *, new_owner=None, now=None, ttl=86400):
    current=audit(state).get(plate_id)
    _need(current is not None and current["status"]=="active","inactive plate")
    old=current["credential"]["payload"]
    stamp=_clock(now)
    _need(stamp<=old["expires_at"],"expired plate cannot be transferred/renewed")
    _need(isinstance(ttl,int) and 0<ttl<=31536000,"invalid lifetime")
    _need(old_owner in state["owners"],"missing current owner")
    _need(state["owners"][old_owner]["public_key"]==old["owner_public_key"],"old owner does not hold plate")
    if kind=="transfer":
        _need(new_owner in state["owners"],"missing new owner")
        target=state["owners"][new_owner]["public_key"]
        _need(target!=old["owner_public_key"],"self-transfer unsupported")
    else:
        target=old["owner_public_key"]
    intent_payload={"schema":"vdmv.owner-intent.v1","kind":kind,"plate_id":plate_id,
        "from_revision":old["revision"],"requested_at":stamp}
    if kind=="transfer":
        intent_payload["new_owner_public_key"]=target
    intent=_signed(state["owners"][old_owner]["seed"],intent_payload)
    new_payload={**old,"owner_public_key":target,"revision":old["revision"]+1,
                 "issued_at":stamp,"expires_at":stamp+ttl}
    new_plate=_signed(state["issuer"]["seed"],new_payload)
    data={"credential":new_plate,"owner_intent":intent}
    if kind=="transfer":
        acceptance_payload={"schema":"vdmv.acceptance.v1","plate_id":plate_id,
            "from_revision":old["revision"],"new_owner_public_key":target,"accepted_at":stamp}
        data["new_owner_acceptance"]=_signed(state["owners"][new_owner]["seed"],acceptance_payload)
    _event(state,kind,data)
    return new_plate


def transfer(state, plate_id, old_owner, new_owner, *, now=None, ttl=86400):
    return _transition(state,"transfer",plate_id,old_owner,new_owner=new_owner,now=now,ttl=ttl)


def renew(state, plate_id, owner, *, now=None, ttl=86400):
    return _transition(state,"renew",plate_id,owner,now=now,ttl=ttl)


def revoke(state, plate_id, *, now=None):
    latest=audit(state).get(plate_id)
    _need(latest is not None and latest["status"]=="active","plate inactive or unknown")
    _event(state,"revoke",{"plate_id":plate_id,"from_revision":latest["credential"]["payload"]["revision"],"revoked_at":_clock(now)})
    return {"plate_id":plate_id,"status":"revoked"}


def _policy(state, resource):
    _need(resource in state["policies"],"unknown resource")
    return state["policies"][resource]


def policy_decision(state, resource, action, role=None, anonymous=False):
    _need(action in ACTIONS,"unknown action")
    p=_policy(state,resource)
    allowed=action in p["anonymous"] if anonymous else role in p["allows"].get(action,[])
    return {"allow":allowed,"attribution_required":allowed and action in p["attribution"],
       "policy_hash":sha256({"resource":resource,"policy":p})}


def challenge(state, plate_id, resource, action, *, now=None):
    _policy(state,resource)
    _need(action in ACTIONS,"invalid action")
    stamp=_clock(now)
    state["sequence_nonce"]+=1
    nonce="CH-"+secrets.token_hex(12)
    body={"schema":"vdmv.challenge.v1","nonce":nonce,"plate_id":plate_id,
      "resource":resource,"action":action,"issued_at":stamp,"expires_at":stamp+120}
    state["challenges"][nonce]=body
    return copy.deepcopy(body)


def holder_proof(state, owner, challenge_body):
    _need(owner in state["owners"],"unknown owner")
    return sign(state["owners"][owner]["seed"],challenge_body)


def _receipt(state, result, request, now):
    body={"schema":"vdmv.receipt.v1","sequence":len(state["receipts"])+1,
      "previous_hash":state["receipts"][-1]["hash"] if state["receipts"] else Z,
      "at":now,"request":copy.deepcopy(request),"decision":copy.deepcopy(result)}
    packet={**body,"signature":sign(state["host"]["seed"],body)}
    packet["hash"]=sha256(packet)
    state["receipts"].append(packet)
    return {**result,"receipt_hash":packet["hash"],"receipt_sequence":packet["sequence"]}


def decide(state, challenge_body, signed_proof, *, now=None, credential_override=None):
    """One-time challenge, current registry, proof-of-possession, then host policy.

    Unknown traffic can be allowed only when host policy explicitly permits it.
    Failed challenges also consume their nonce. Every decision has a host receipt.
    """
    stamp=_clock(now)
    received=copy.deepcopy(challenge_body)
    _need(isinstance(received,dict),"invalid challenge shape")
    nonce=received.get("nonce")
    expected=state["challenges"].pop(nonce,None)
    request={"challenge":received,"proof_fingerprint":hashlib.sha256(str(signed_proof).encode()).hexdigest()[:16]}
    result={"allow":False,"reason":"INVALID_OR_REPLAYED_CHALLENGE","attribution_required":False}
    if not expected or received!=expected or stamp<expected["issued_at"] or stamp>expected["expires_at"]:
        return _receipt(state,result,request,stamp)
    plate_id=expected["plate_id"]
    resource=expected["resource"]
    action=expected["action"]
    if plate_id=="anonymous":
        d=policy_decision(state,resource,action,anonymous=True)
        result={"allow":d["allow"],"reason":"ANONYMOUS_POLICY_ALLOW" if d["allow"] else "ANONYMOUS_DEFAULT_DENY",
          "attribution_required":d["attribution_required"],"policy_hash":d["policy_hash"]}
    else:
        try:
            existing=audit(state).get(plate_id)
            if not existing or existing["status"]!="active":
                result["reason"]="UNKNOWN_OR_REVOKED"
            else:
                current=existing["credential"]
                if credential_override is not None and credential_override != current:
                    result["reason"]="STALE_OR_FORGED_CREDENTIAL"
                else:
                    p=_validate_credential(current,state["issuer"]["public_key"],state["issuer"]["id"])
                    if not p["issued_at"]<=stamp<=p["expires_at"]:
                        result["reason"]="EXPIRED_OR_NOT_YET_VALID"
                    elif not verify(p["owner_public_key"],expected,signed_proof):
                        result["reason"]="INVALID_HOLDER_PROOF"
                    else:
                        d=policy_decision(state,resource,action,p["participation_class"])
                        result={"allow":d["allow"],"reason":"POLICY_ALLOW" if d["allow"] else "POLICY_DENY",
                          "attribution_required":d["attribution_required"],"plate_id":plate_id,
                          "participation_class":p["participation_class"],"policy_hash":d["policy_hash"]}
        except (ValueError,KeyError,TypeError) as error:
            result["reason"]="MALFORMED_CREDENTIAL_OR_REGISTRY"
    return _receipt(state,result,request,stamp)


def request(state, plate_id, resource, action, *, owner=None, now=None, proof_override=None, credential_override=None):
    """Convenience test driver; the gate itself never trusts the owner label."""
    c=challenge(state,plate_id,resource,action,now=now)
    proof=proof_override if proof_override is not None else ("" if owner is None else holder_proof(state,owner,c))
    return decide(state,c,proof,now=now,credential_override=credential_override)


def verify_receipts(state):
    _need(public_key(state["host"]["seed"])==state["host"]["public_key"],"host key mismatch")
    last=Z
    for i,packet in enumerate(state["receipts"],1):
        core={k:v for k,v in packet.items() if k not in ("signature","hash")}
        _need(packet.get("sequence")==i and packet.get("previous_hash")==last,"receipt sequence/link invalid")
        _need(packet.get("hash")==sha256({**core,"signature":packet.get("signature")}),"receipt hash invalid")
        _need(verify(state["host"]["public_key"],core,packet.get("signature")),"receipt signature invalid")
        last=packet["hash"]
    return {"ok":True,"count":len(state["receipts"]),"tip":last}


def audit_all(state):
    plates=audit(state)
    receipts=verify_receipts(state)
    return {"ok":True,"plates":len(plates),"active":sum(x["status"]=="active" for x in plates.values()),
      "events":len(state["events"]),"event_tip":state["events"][-1]["hash"] if state["events"] else Z,
      "receipts":receipts["count"],"receipt_tip":receipts["tip"],
      "note":"Integrity under demo local issuer/host trust; missing-tail and compromised-key attacks not excluded."}


def roster(state):
    known=audit(state)
    return [{"plate_id":pid,"status":v["status"],"class":v["credential"]["payload"]["participation_class"],
      "revision":v["credential"]["payload"]["revision"],"owner":next((name for name,obj in state["owners"].items() if obj["public_key"]==v["credential"]["payload"]["owner_public_key"]),"unknown"),
      "expires_at":v["credential"]["payload"]["expires_at"]} for pid,v in known.items()]


def bootstrap(*, seed=None, now=1893456000):
    state=new_state(seed=seed, now=now)
    for name in ("alice","bob","mallory"):
        owner_seed=b64(hashlib.sha256((str(seed)+"/"+name).encode()).digest()) if seed is not None else None
        add_owner(state,name,seed=owner_seed)
    issue(state,"alice","research",now=now,plate_id="VDMV-RESEARCH-01")
    issue(state,"bob","crawler",now=now,plate_id="VDMV-CRAWLER-02")
    return state


def traffic_cases():
    """Fixed constructed scenarios; scoring is not empirical validation."""
    cases = [
       {"label":"Known researcher requests a summary","plate":"VDMV-RESEARCH-01","owner":"alice","resource":"research-library","action":"summarize","truth":"Identity verified; allow with attribution."},
       {"label":"Unregistered crawler tries the private library","plate":"anonymous","owner":None,"resource":"research-library","action":"crawl","truth":"Unknown traffic; deny."},
       {"label":"Known crawler indexes public archive","plate":"VDMV-CRAWLER-02","owner":"bob","resource":"open-archive","action":"index","truth":"Verified crawler; allow."},
       {"label":"Known crawler requests model training","plate":"VDMV-CRAWLER-02","owner":"bob","resource":"licensed-training-data","action":"train","truth":"Verified but lacks this use permission."},
       {"label":"Unknown discovery bot visits public archive","plate":"anonymous","owner":None,"resource":"open-archive","action":"discover","truth":"Anonymous discovery is explicitly allowed."},
       {"label":"Mallory presents research plate without its key","plate":"VDMV-RESEARCH-01","owner":"mallory","resource":"research-library","action":"crawl","truth":"Correct plate ID, wrong private key; deny."},
       {"label":"Known researcher trains on licensed sample","plate":"VDMV-RESEARCH-01","owner":"alice","resource":"licensed-training-data","action":"train","truth":"Allowed under the demonstration policy only."},
       {"label":"Anonymous indexing at open index","plate":"anonymous","owner":None,"resource":"open-index","action":"index","truth":"Host explicitly permits anonymous indexing."},
       {"label":"Known crawler attempts prohibited redistribution","plate":"VDMV-CRAWLER-02","owner":"bob","resource":"open-archive","action":"redistribute","truth":"No redistribution grant."},
       {"label":"Known researcher archives without archival class","plate":"VDMV-RESEARCH-01","owner":"alice","resource":"research-library","action":"archive","truth":"Wrong participation class; deny."},
    ]

    # Independently declared expected results, separate from the current Python gate verdict.
    expected=[
      (True,"POLICY_ALLOW"),(False,"ANONYMOUS_DEFAULT_DENY"),
      (True,"POLICY_ALLOW"),(False,"POLICY_DENY"),
      (True,"ANONYMOUS_POLICY_ALLOW"),(False,"INVALID_HOLDER_PROOF"),
      (True,"POLICY_ALLOW"),(True,"ANONYMOUS_POLICY_ALLOW"),
      (False,"POLICY_DENY"),(False,"POLICY_DENY")]
    _need(len(cases)==len(expected),"scenario oracle count mismatch")
    return [{**case,"id":f"GAME-{i+1:03d}","expected_allow":allow,
       "expected_reason":reason,"expected":"ADMIT" if allow else "DENY"}
       for i,(case,(allow,reason)) in enumerate(zip(cases,expected))]


def economics_simulation(state, *, rounds=100, seed=7, adoption=0.5):
    """Illustrative incentive model, not observed human/bot behavior."""
    import random
    _need(isinstance(rounds,int) and 1<=rounds<=5000,"round count out of bounds")
    _need(isinstance(adoption,(int,float)) and 0<=adoption<=1,"invalid adoption fraction")
    rng=random.Random(seed)
    accepted=0; denied=0; revenue=0; registration_cost=0
    for _ in range(rounds):
        registered=rng.random()<adoption
        if registered:
            registration_cost+=1
        resource=rng.choice(["research-library","open-index"])
        role="research" if registered else None
        accepted_now=policy_decision(state,resource,"crawl",role,anonymous=not registered)["allow"]
        if accepted_now:
            accepted+=1; revenue+=5
        else:
            denied+=1
    return {"kind":"synthetic_economic_model","rounds":rounds,"adoption":adoption,"accepted":accepted,"denied":denied,
      "gross_access_utility":revenue,"registration_cost":registration_cost,"net_model_utility":revenue-registration_cost,
      "assumptions":"Uniform synthetic site draw; registration costs 1, admission utility 5. Not evidence that real actors adopt plates."}


def run_bench():
    """Small browser-native falsification bench. Full tests live in tests/."""
    tests=[]
    def check(label, func):
        try:
            func();tests.append({"name":label,"pass":True})
        except Exception as exc:
            tests.append({"name":label,"pass":False,"error":str(exc)})
    now=1893456000
    def setup():return bootstrap(seed="bench",now=now)
    def passes():
        s=setup(); r=request(s,"VDMV-RESEARCH-01","research-library","summarize",owner="alice",now=now);_need(r["allow"] and r["attribution_required"],"expected attributed admission")
    def wrong_key():
        s=setup();r=request(s,"VDMV-RESEARCH-01","research-library","crawl",owner="mallory",now=now);_need(not r["allow"] and r["reason"]=="INVALID_HOLDER_PROOF","wrong key accepted")
    def forbidden_use():
        s=setup();r=request(s,"VDMV-CRAWLER-02","licensed-training-data","train",owner="bob",now=now);_need(not r["allow"] and r["reason"]=="POLICY_DENY","wrong permission allowed")
    def anonymous_open():
        s=setup();r=request(s,"anonymous","open-index","crawl",now=now);_need(r["allow"],"open policy denied anonymous")
    def anonymous_closed():
        s=setup();r=request(s,"anonymous","research-library","crawl",now=now);_need(not r["allow"],"closed policy admitted anonymous")
    def revoked():
        s=setup();revoke(s,"VDMV-RESEARCH-01",now=now);r=request(s,"VDMV-RESEARCH-01","research-library","crawl",owner="alice",now=now);_need(r["reason"]=="UNKNOWN_OR_REVOKED","revocation ineffective")
    def transfer_old_key():
        s=setup();transfer(s,"VDMV-RESEARCH-01","alice","bob",now=now);r=request(s,"VDMV-RESEARCH-01","research-library","crawl",owner="alice",now=now);_need(r["reason"]=="INVALID_HOLDER_PROOF","old owner retained rights")
    def transfer_new_key():
        s=setup();transfer(s,"VDMV-RESEARCH-01","alice","bob",now=now);r=request(s,"VDMV-RESEARCH-01","research-library","crawl",owner="bob",now=now);_need(r["allow"],"new owner denied")
    def event_tamper():
        s=setup();s["events"][0]["data"]["credential"]["payload"]["participation_class"]="commercial"
        try:audit(s)
        except ProtocolError:return
        raise AssertionError("modified event accepted")
    def receipt_tamper():
        s=setup();request(s,"anonymous","open-index","crawl",now=now);s["receipts"][0]["decision"]["allow"]=False
        try:verify_receipts(s)
        except ProtocolError:return
        raise AssertionError("modified receipt accepted")
    def replay():
        s=setup();c=challenge(s,"VDMV-RESEARCH-01","research-library","crawl",now=now);proof=holder_proof(s,"alice",c)
        good=decide(s,c,proof,now=now);bad=decide(s,c,proof,now=now)
        _need(good["allow"] and bad["reason"]=="INVALID_OR_REPLAYED_CHALLENGE","replay not rejected")
    def expiry():
        s=setup();r=request(s,"VDMV-RESEARCH-01","research-library","crawl",owner="alice",now=now+86500)
        _need(r["reason"]=="EXPIRED_OR_NOT_YET_VALID","expired credential accepted")
    for name,fn in [("Valid proof + allowed action",passes),("Wrong-holder signature",wrong_key),("Authenticated but forbidden training",forbidden_use),("Anonymous open resource",anonymous_open),("Anonymous protected resource",anonymous_closed),("Issuer revocation",revoked),("Old owner rejected after transfer",transfer_old_key),("New owner admitted after transfer",transfer_new_key),("Issuer event tamper detection",event_tamper),("Host receipt tamper detection",receipt_tamper),("One-use challenge replay",replay),("Credential expiration",expiry)]:
        check(name,fn)
    for i,test in enumerate(tests,1):
        test["id"]=f"PROBE-{i:03d}"
        test["expected"]="Python assertion(s) for this named adversarial test must hold"
        test["observed"]="All asserted conditions held" if test["pass"] else test.get("error","Unexpected behavior")
    return {"passed":sum(x["pass"] for x in tests),"total":len(tests),"cases":tests,
      "notice":"Developer-authored synthetic correctness checks; not an independent security audit or real-world validation."}


def dispatch(input_data):
    """Shared JSON interface used by both Python CLI and embedded Pyodide lab."""
    _need(isinstance(input_data,dict),"command must be an object")
    op=input_data.get("op")
    state=input_data.get("state") or bootstrap(now=_clock(input_data.get("now",1893456000)))
    args=input_data.get("args") or {}
    if op=="bootstrap": state=bootstrap(now=_clock(args.get("now",1893456000))); outcome={"ready":True}
    elif op=="roster":outcome=roster(state)
    elif op=="audit":outcome=audit_all(state)
    elif op=="owner":outcome=add_owner(state,args["name"])
    elif op=="issue":outcome=issue(state,args["owner"],args["role"],now=args.get("now",state["created_at"]),ttl=args.get("ttl",86400),plate_id=args.get("plate_id"))
    elif op=="renew":outcome=renew(state,args["plate_id"],args["owner"],now=args.get("now",state["created_at"]))
    elif op=="transfer":outcome=transfer(state,args["plate_id"],args["old_owner"],args["new_owner"],now=args.get("now",state["created_at"]))
    elif op=="revoke":outcome=revoke(state,args["plate_id"],now=args.get("now",state["created_at"]))
    elif op=="request":outcome=request(state,args["plate_id"],args["resource"],args["action"],owner=args.get("owner"),now=args.get("now",state["created_at"]))
    elif op=="policy":outcome=policy_decision(state,args["resource"],args["action"],args.get("role"),args.get("anonymous",False))
    elif op=="policies":outcome=copy.deepcopy(state["policies"])
    elif op=="casebook":outcome=traffic_cases()
    elif op=="game_try":
        cases=traffic_cases()
        index=args.get("index")
        _need(type(index) is int and 0<=index<len(cases),"game case index out of range")
        case=cases[index]
        # The game is a REPLAYABLE test instrument; never use the player's mutable DMV workspace.
        # Do not place game receipts into the user's registry or score against a changed policy.
        fixture=bootstrap(seed="bot-traffic-game-v0.2",now=1893456000)
        decision=request(fixture,case["plate"],case["resource"],case["action"],owner=case["owner"],now=fixture["created_at"])
        outcome={"case":case,"decision":decision,"isolated":True,"workspace_unchanged":True,
          "scenario_matches_expectation":decision["allow"]==case["expected_allow"] and decision["reason"]==case["expected_reason"]}
    elif op=="economics":outcome=economics_simulation(state,rounds=int(args.get("rounds",100)),adoption=float(args.get("adoption",.5)),seed=int(args.get("seed",7)))
    elif op=="bench":outcome=run_bench()
    elif op=="help":outcome={"ops":["bootstrap","roster","audit","owner","issue","renew","transfer","revoke","request","policies","policy","casebook","game_try","economics","bench","help"],"schema":SCHEMA}
    else:raise ProtocolError("unknown command: "+str(op))
    return {"state":state,"result":outcome}


def bridge(json_input):
    try:
        output=dispatch(json.loads(json_input))
        return json.dumps({"ok":True,**output},sort_keys=True,ensure_ascii=True)
    except (KeyError,TypeError,ValueError) as e:
        return json.dumps({"ok":False,"error":str(e)})
