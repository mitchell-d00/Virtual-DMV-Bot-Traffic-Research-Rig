"""Virtual DMV: local reference engine for experimental machine participation.

All permissions are DEMO decisions over invented resources. Signed demo plates
are NOT real authorization, legal contracts, website rights, or real identities.
This code is intended for offline testing and falsification, not production.
"""
import copy
import hashlib
import json
import math
import secrets
import time
from .portable import b64, canonical, make_seed, public_key, sha256, sign, verify

SCHEMA = "virtual-dmv.lab.v1"
CLASSES = ("crawler", "research", "commercial", "archival", "agentic")
ACTIONS = ("discover", "crawl", "index", "summarize", "train", "redistribute", "archive")
Z = "0" * 64
MAX_PENDING_CHALLENGES = 128  # bounded per local demo registry, not per remote client

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
    return type(value) is str and 1 <= len(value) <= 72 and all(("A"<=c<="Z") or ("a"<=c<="z") or ("0"<=c<="9") or c in "-_." for c in value)


def _clock(now=None):
    v = int(time.time()) if now is None else now
    _need(type(v) is int and 0 <= v <= 4102444800, "invalid demo timestamp")
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
            intent_schema=intent_payload.get("schema")
            _need(intent_schema in ("vdmv.owner-intent.v1","vdmv.owner-intent.v2") and intent_payload.get("kind")==kind
              and intent_payload.get("plate_id")==p["plate_id"] and intent_payload.get("from_revision")==previous["revision"],"owner intent mismatch")
            # V2 binds the *entire* successor credential, including new validity.
            # V1 remains readable only for historical fixtures released before v0.5.
            if intent_schema=="vdmv.owner-intent.v2":
                _need(intent_payload.get("successor_sha256")==sha256(p),"owner intent successor mismatch")
            if kind=="transfer":
                _need(intent_payload.get("new_owner_public_key")==p["owner_public_key"],"transfer target mismatch")
                acceptance=data.get("new_owner_acceptance",{})
                accept_payload=acceptance.get("payload",{}) if isinstance(acceptance,dict) else {}
                required_accept="vdmv.acceptance.v2" if intent_schema=="vdmv.owner-intent.v2" else "vdmv.acceptance.v1"
                _need(accept_payload.get("schema")==required_accept
                  and accept_payload.get("plate_id")==p["plate_id"]
                  and accept_payload.get("from_revision")==previous["revision"]
                  and accept_payload.get("new_owner_public_key")==p["owner_public_key"],"incoming owner acceptance mismatch")
                if required_accept=="vdmv.acceptance.v2":
                    _need(accept_payload.get("successor_sha256")==sha256(p),"new owner acceptance successor mismatch")
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
    _need(type(ttl) is int and 0<ttl<=31536000,"invalid credential lifetime")
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
    # Reject impossible retroactive transitions *before* appending any event.
    _need(old["issued_at"]<=stamp<=old["expires_at"],"transition outside credential validity")
    _need(type(ttl) is int and 0<ttl<=31536000,"invalid lifetime")
    _need(old_owner in state["owners"],"missing current owner")
    _need(state["owners"][old_owner]["public_key"]==old["owner_public_key"],"old owner does not hold plate")
    if kind=="transfer":
        _need(new_owner in state["owners"],"missing new owner")
        target=state["owners"][new_owner]["public_key"]
        _need(target!=old["owner_public_key"],"self-transfer unsupported")
    else:
        target=old["owner_public_key"]
    new_payload={**old,"owner_public_key":target,"revision":old["revision"]+1,
                 "issued_at":stamp,"expires_at":stamp+ttl}
    successor_hash=sha256(new_payload)
    new_plate=_signed(state["issuer"]["seed"],new_payload)
    intent_payload={"schema":"vdmv.owner-intent.v2","kind":kind,"plate_id":plate_id,
        "from_revision":old["revision"],"requested_at":stamp,"successor_sha256":successor_hash}
    if kind=="transfer":
        intent_payload["new_owner_public_key"]=target
    intent=_signed(state["owners"][old_owner]["seed"],intent_payload)
    data={"credential":new_plate,"owner_intent":intent}
    if kind=="transfer":
        acceptance_payload={"schema":"vdmv.acceptance.v2","plate_id":plate_id,
            "from_revision":old["revision"],"new_owner_public_key":target,
            "accepted_at":stamp,"successor_sha256":successor_hash}
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
    # Prune expired, already-unusable traffic before enforcing a hard memory bound.
    # Pending requests must not be overwritten under queue saturation.
    for key, item in list(state["challenges"].items()):
        if isinstance(item, dict) and type(item.get("expires_at")) is int and item["expires_at"] < stamp:
            del state["challenges"][key]
    _need(len(state["challenges"]) < MAX_PENDING_CHALLENGES, "pending challenge limit reached")
    state["sequence_nonce"]+=1
    # Even an improbable nonce collision must never overwrite a pending request.
    nonce=None
    for _ in range(8):
        candidate="CH-"+secrets.token_hex(12)
        if candidate not in state["challenges"]:
            nonce=candidate
            break
    _need(nonce is not None,"could not allocate unique challenge nonce")
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



def _bounded_traffic(value):
    """Constrain a JSON-like traffic envelope before copying or signing it.

    The demo has no network ingress; this protects Python and browser adapters
    from non-JSON, recursive, oversized or non-finite test inputs.
    """
    count=0
    active=set()
    def walk(item,depth):
        nonlocal count
        count+=1
        if count>128 or depth>9:
            return False
        if item is None or type(item) in (bool,int):
            return True
        if type(item) is float:
            return math.isfinite(item)
        if type(item) is str:
            return len(item)<=2048
        if type(item) in (list,dict):
            if id(item) in active or len(item)>64:
                return False
            active.add(id(item))
            if type(item) is dict:
                valid=all(type(k) is str and len(k)<=128 and walk(v,depth+1) for k,v in item.items())
            else:
                valid=all(walk(v,depth+1) for v in item)
            active.remove(id(item))
            return valid
        return False
    if not walk(value,0):
        return False
    try:
        return len(canonical(value))<=4096
    except (TypeError,ValueError,RecursionError,OverflowError):
        return False

def decide(state, challenge_body, signed_proof, *, now=None, credential_override=None):
    """One-time challenge, current registry, proof-of-possession, then host policy.

    Unknown traffic can be allowed only when host policy explicitly permits it.
    Failed challenges also consume their nonce. Every decision has a host receipt.
    """
    stamp=_clock(now)
    # Keep the audit receipt small and serializable even for hostile payloads.
    fingerprint_input=signed_proof if type(signed_proof) is str and len(signed_proof)<=512 else "<invalid-proof>"
    fingerprint=hashlib.sha256(fingerprint_input.encode("utf-8")).hexdigest()[:16]
    if not isinstance(challenge_body,dict) or not _bounded_traffic(challenge_body):
        safe_request={"challenge":{"rejected_type":type(challenge_body).__name__},"proof_fingerprint":fingerprint}
        return _receipt(state,{"allow":False,"reason":"MALFORMED_CHALLENGE","attribution_required":False},safe_request,stamp)
    received=copy.deepcopy(challenge_body)
    request={"challenge":received,"proof_fingerprint":fingerprint}
    nonce=received.get("nonce")
    # JSON clients can send arrays/objects as nonce values. Never crash before
    # issuing a denial receipt or let malformed traffic consume a valid nonce.
    if not isinstance(nonce,str) or not nonce.startswith("CH-") or len(nonce)>80:
        return _receipt(state,{"allow":False,"reason":"MALFORMED_CHALLENGE","attribution_required":False},request,stamp)
    expected=state["challenges"].pop(nonce,None)
    result={"allow":False,"reason":"INVALID_OR_REPLAYED_CHALLENGE","attribution_required":False}
    if (not isinstance(expected,dict) or received!=expected
        or type(expected.get("issued_at")) is not int or type(expected.get("expires_at")) is not int
        or stamp<expected["issued_at"] or stamp>expected["expires_at"]):
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

    # Expected decisions and attribution are independently specified; no oracle
    # is generated by evaluating the gate that it is supposed to test.
    expected=[
      (True,"POLICY_ALLOW",True),(False,"ANONYMOUS_DEFAULT_DENY",False),
      (True,"POLICY_ALLOW",False),(False,"POLICY_DENY",False),
      (True,"ANONYMOUS_POLICY_ALLOW",False),(False,"INVALID_HOLDER_PROOF",False),
      (True,"POLICY_ALLOW",False),(True,"ANONYMOUS_POLICY_ALLOW",False),
      (False,"POLICY_DENY",False),(False,"POLICY_DENY",False)]
    _need(len(cases)==len(expected),"scenario oracle count mismatch")
    full=[{**case,"scenario":"baseline","expected_allow":allow,
       "expected_reason":reason,"expected_attribution":attribution}
       for case,(allow,reason,attribution) in zip(cases,expected)]
    def extra(label,plate,owner,resource,action,scenario,allow,reason,attribution=False,truth=""):
        full.append({"label":label,"plate":plate,"owner":owner,
          "resource":resource,"action":action,"scenario":scenario,
          "expected_allow":allow,"expected_reason":reason,
          "expected_attribution":attribution,"truth":truth or reason})
    r="VDMV-RESEARCH-01"; c="VDMV-CRAWLER-02"
    extra("Revoked researcher tries library crawling",r,"alice","research-library","crawl","revoke",False,"UNKNOWN_OR_REVOKED",truth="Previously verified identity is now revoked.")
    extra("Transferred research plate: old key denied",r,"alice","research-library","crawl","transfer_old",False,"INVALID_HOLDER_PROOF",truth="Prior owner lost signing authority after transfer.")
    extra("Transferred research plate: new key admitted",r,"bob","research-library","crawl","transfer_new",True,"POLICY_ALLOW",truth="Current owner can prove control of the transferred plate.")
    extra("Renewed research plate continues beyond old expiry",r,"alice","research-library","crawl","renew",True,"POLICY_ALLOW",truth="Signed renewal makes a fresh time window admissible.")
    extra("Expired research plate rejected",r,"alice","research-library","crawl","expired",False,"EXPIRED_OR_NOT_YET_VALID",truth="Expired credentials cannot access protected content.")
    extra("Premature research plate use rejected",r,"alice","research-library","crawl","not_yet",False,"EXPIRED_OR_NOT_YET_VALID",truth="Credential may not operate before its issuance time.")
    extra("Old transferred credential cannot override registry",r,"bob","research-library","crawl","stale_transfer",False,"STALE_OR_FORGED_CREDENTIAL",truth="Stale credential is denied even with a valid new-holder proof.")
    extra("Modified signed credential is rejected",r,"alice","research-library","crawl","forged_credential",False,"STALE_OR_FORGED_CREDENTIAL",truth="Credential bytes must match the current signed registry plate.")
    extra("Consumed request nonce cannot be replayed",r,"alice","research-library","crawl","replay",False,"INVALID_OR_REPLAYED_CHALLENGE",truth="One-time challenges cannot be reused.")
    extra("Altered challenge action is rejected",r,"alice","research-library","crawl","swapped_challenge",False,"INVALID_OR_REPLAYED_CHALLENGE",truth="The presented challenge must match the issued challenge exactly.")
    extra("Malformed list-valued challenge nonce denied with receipt",r,"alice","research-library","crawl","malformed_nonce",False,"MALFORMED_CHALLENGE",truth="Malformed traffic is a denied request, not an engine crash.")
    extra("Unissued plate tries protected library", "VDMV-UNISSUED-00","alice","research-library","crawl","baseline",False,"UNKNOWN_OR_REVOKED",truth="No plate registration exists.")
    extra("Research class cannot index archived collection",r,"alice","open-archive","index","baseline",False,"POLICY_DENY",truth="Registration alone does not imply indexing rights.")
    extra("Research summaries of open archive require attribution",r,"alice","open-archive","summarize","baseline",True,"POLICY_ALLOW",True,"Resource terms require attribution after admission.")
    extra("Archival registrant may archive research library","VDMV-ARCHIVAL-03","alice","research-library","archive","issue_archival",True,"POLICY_ALLOW",True,"Archive action requires the archival plate class and attribution.")
    extra("Agentic registrant may summarize open archive","VDMV-AGENTIC-04","alice","open-archive","summarize","issue_agentic",True,"POLICY_ALLOW",True,"Agentic summary requires verifiable identity and attribution.")
    extra("Commercial registrant may discover public archive","VDMV-COMMERCIAL-05","alice","open-archive","discover","issue_commercial",True,"POLICY_ALLOW",False,"Commercial role is admissible for discovery only.")
    extra("Commercial registrant cannot crawl open archive","VDMV-COMMERCIAL-05","alice","open-archive","crawl","issue_commercial",False,"POLICY_DENY",False,"Discovery permission does not imply crawling permission.")
    extra("Anonymous bot cannot summarize open index","anonymous",None,"open-index","summarize","baseline",False,"ANONYMOUS_DEFAULT_DENY",False,"Public indexing does not confer summary rights.")
    extra("Anonymous bot can crawl explicitly open index","anonymous",None,"open-index","crawl","baseline",True,"ANONYMOUS_POLICY_ALLOW",False,"Host expressly allows anonymous crawl.")
    extra("Revoked crawler blocked even from registered open-archive index",c,"bob","open-archive","index","revoke_crawler",False,"UNKNOWN_OR_REVOKED",truth="Revoked registered identity loses role-based permissions.")
    extra("Forged owner proof denied despite valid plate",r,"alice","research-library","crawl","forged_proof",False,"INVALID_HOLDER_PROOF",truth="Bad signatures do not establish holder control.")
    extra("Pre-renewal credential rejected after rotation",r,"alice","research-library","crawl","stale_renew",False,"STALE_OR_FORGED_CREDENTIAL",truth="Renewal rotates current credential revision.")
    extra("Research plate cannot redistribute licensed training",r,"alice","licensed-training-data","redistribute","baseline",False,"POLICY_DENY",truth="Training permission is separate from redistribution.")
    extra("Unverified commercial plate cannot request training","VDMV-COMMERCIAL-05","alice","licensed-training-data","train","issue_commercial",False,"POLICY_DENY",truth="Signed class does not grant unlicensed training.")
    extra("Anonymous crawler cannot train on licensed data","anonymous",None,"licensed-training-data","train","baseline",False,"ANONYMOUS_DEFAULT_DENY",truth="No anonymous training permission.")
    # v0.4: NEW distinct resource/class combinations and hostile packet traffic.
    # Oracles below are hand-written, not calculated by asking the engine.
    extra("Anonymous crawler cannot crawl the public archive", "anonymous",None,"open-archive","crawl","baseline",False,"ANONYMOUS_DEFAULT_DENY",truth="Public discovery is not public crawling.")
    extra("Anonymous indexer cannot index the public archive", "anonymous",None,"open-archive","index","baseline",False,"ANONYMOUS_DEFAULT_DENY",truth="Index permission requires a registered crawler or archival plate.")
    extra("Unknown participant can discover open index", "anonymous",None,"open-index","discover","baseline",True,"ANONYMOUS_POLICY_ALLOW",truth="Open index grants anonymous discovery.")
    extra("Unknown participant cannot redistribute open index", "anonymous",None,"open-index","redistribute","baseline",False,"ANONYMOUS_DEFAULT_DENY",truth="Open indexing does not authorize redistribution.")
    extra("Crawler may discover open index",c,"bob","open-index","discover","baseline",True,"POLICY_ALLOW",truth="Registered crawler is allowed discovery.")
    extra("Crawler may crawl open index",c,"bob","open-index","crawl","baseline",True,"POLICY_ALLOW",truth="Open-index crawler access is explicit.")
    extra("Crawler may index open index",c,"bob","open-index","index","baseline",True,"POLICY_ALLOW",truth="Crawler indexing permitted by local owner.")
    extra("Researcher may discover open index",r,"alice","open-index","discover","baseline",True,"POLICY_ALLOW",truth="Research class can discover open index.")
    extra("Researcher may crawl open index",r,"alice","open-index","crawl","baseline",True,"POLICY_ALLOW",truth="Host allows the research class.")
    extra("Researcher may index open index",r,"alice","open-index","index","baseline",True,"POLICY_ALLOW",truth="Locally open indexing grants all five registered classes.")
    extra("Crawler may crawl public archive",c,"bob","open-archive","crawl","baseline",True,"POLICY_ALLOW",truth="Archive allows recognized crawler role.")
    extra("Crawler may discover public archive",c,"bob","open-archive","discover","baseline",True,"POLICY_ALLOW",truth="Archive discovery available to registered classes.")
    extra("Researcher may crawl public archive",r,"alice","open-archive","crawl","baseline",True,"POLICY_ALLOW",truth="Researcher receives archival crawl access.")
    extra("Researcher may discover public archive",r,"alice","open-archive","discover","baseline",True,"POLICY_ALLOW",truth="Discovery and crawling remain separate actions.")
    extra("Researcher may crawl library",r,"alice","research-library","crawl","baseline",True,"POLICY_ALLOW",truth="Library expressly admits signed research crawlers.")
    extra("Researcher may not index restricted library",r,"alice","research-library","index","baseline",False,"POLICY_DENY",truth="Allowed crawling does not imply indexing.")
    extra("Crawler may not summarize restricted library",c,"bob","research-library","summarize","baseline",False,"POLICY_DENY",truth="Wrong class and action; deny.")
    extra("Crawler may not archive restricted library",c,"bob","research-library","archive","baseline",False,"POLICY_DENY",truth="Archive permission is reserved to archival class.")
    extra("Researcher may crawl licensed training sample",r,"alice","licensed-training-data","crawl","baseline",True,"POLICY_ALLOW",truth="Registered research crawl is allowed separately from training.")
    extra("Crawler cannot crawl licensed training sample",c,"bob","licensed-training-data","crawl","baseline",False,"POLICY_DENY",truth="Crawler plate lacks licensed sample crawl rights.")
    extra("Anonymous machine cannot crawl licensed training sample","anonymous",None,"licensed-training-data","crawl","baseline",False,"ANONYMOUS_DEFAULT_DENY",truth="Unknown machines have no licensed-sample crawl rights.")
    extra("Archival plate can index the public archive","VDMV-ARCHIVAL-03","alice","open-archive","index","issue_archival",True,"POLICY_ALLOW",truth="Archival class can index the public archive.")
    extra("Non-object traffic packet receives a denial receipt",r,"alice","research-library","crawl","malformed_envelope",False,"MALFORMED_CHALLENGE",truth="Malformed envelope is a signed denial, not an exception or lost request.")
    extra("Expired host challenge is denied before owner proof",r,"alice","research-library","summarize","expired_challenge",False,"INVALID_OR_REPLAYED_CHALLENGE",truth="A valid holder key cannot redeem an expired request challenge.")
    _need(len(full)==len({(x["scenario"],x["plate"],x["owner"],x["resource"],x["action"]) for x in full}),"repeated traffic tuple")
    return [{**case,"id":f"GAME-{i+1:03d}",
             "expected":"ADMIT" if case["expected_allow"] else "DENY"}
            for i,case in enumerate(full)]


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
    def malformed_nonce():
        s=setup();ch=challenge(s,"VDMV-RESEARCH-01","research-library","crawl",now=now)
        invalid=copy.deepcopy(ch);invalid["nonce"]=[ch["nonce"]]
        out=decide(s,invalid,"wrong",now=now)
        _need(out["reason"]=="MALFORMED_CHALLENGE" and out.get("receipt_hash") and ch["nonce"] in s["challenges"],"malformed nonce crashed or destroyed valid challenge")
    def stale_transfer():
        s=setup();old=copy.deepcopy(audit(s)["VDMV-RESEARCH-01"]["credential"])
        transfer(s,"VDMV-RESEARCH-01","alice","bob",now=now)
        out=request(s,"VDMV-RESEARCH-01","research-library","crawl",owner="bob",now=now,credential_override=old)
        _need(out["reason"]=="STALE_OR_FORGED_CREDENTIAL","stale transferred plate accepted")
    def summary_attribution():
        s=setup();out=request(s,"VDMV-RESEARCH-01","open-archive","summarize",owner="alice",now=now)
        _need(out["allow"] and out["attribution_required"],"summary admitted without attribution notice")
    def unknown_plate():
        s=setup();out=request(s,"VDMV-ABSENT-999","research-library","crawl",owner="alice",now=now)
        _need(out["reason"]=="UNKNOWN_OR_REVOKED","missing plate admitted")
    def no_training_anonymously():
        s=setup();out=request(s,"anonymous","licensed-training-data","train",now=now)
        _need(out["reason"]=="ANONYMOUS_DEFAULT_DENY","anonymous training admitted")
    def challenge_timeout():
        s=setup();ch=challenge(s,"VDMV-RESEARCH-01","research-library","crawl",now=now)
        proof=holder_proof(s,"alice",ch)
        out=decide(s,ch,proof,now=now+121)
        _need(out["reason"]=="INVALID_OR_REPLAYED_CHALLENGE","timed-out challenge admitted")
    def malformed_envelope():
        s=setup();ch=challenge(s,"VDMV-RESEARCH-01","research-library","crawl",now=now)
        result=decide(s,[ch],"untrusted",now=now)
        _need(result["reason"]=="MALFORMED_CHALLENGE" and ch["nonce"] in s["challenges"],"malformed packet consumed a live challenge")
        _need(verify_receipts(s)["ok"],"no signed denial receipt")
    def saturated_queue():
        s=setup()
        for _ in range(MAX_PENDING_CHALLENGES):challenge(s,"VDMV-RESEARCH-01","research-library","crawl",now=now)
        try:challenge(s,"VDMV-RESEARCH-01","research-library","crawl",now=now)
        except ProtocolError:pass
        else:raise AssertionError("unbounded pending challenge allocation")
        _need(len(s["challenges"])==MAX_PENDING_CHALLENGES,"pending challenge limit altered active requests")
    def reclaimed_expired_queue():
        s=setup()
        for _ in range(MAX_PENDING_CHALLENGES):challenge(s,"VDMV-RESEARCH-01","research-library","crawl",now=now)
        latest=challenge(s,"VDMV-RESEARCH-01","research-library","crawl",now=now+121)
        _need(len(s["challenges"])==1,"stale challenges remain after expiry")
        _need(decide(s,latest,holder_proof(s,"alice",latest),now=now+121)["allow"],"new valid request not admitted")
    def traffic_tuples_unique():
        cases=traffic_cases()
        _need(len(cases)==60,"unexpected v0.4 game count")
        sig={(case["scenario"],case["plate"],case["owner"],case["resource"],case["action"]) for case in cases}
        _need(len(sig)==len(cases),"repeated traffic configuration")
    for name,fn in [("Valid proof + allowed action",passes),("Wrong-holder signature",wrong_key),("Authenticated but forbidden training",forbidden_use),("Anonymous open resource",anonymous_open),("Anonymous protected resource",anonymous_closed),("Issuer revocation",revoked),("Old owner rejected after transfer",transfer_old_key),("New owner admitted after transfer",transfer_new_key),("Issuer event tamper detection",event_tamper),("Host receipt tamper detection",receipt_tamper),("One-use challenge replay",replay),("Credential expiration",expiry),
        ("Malformed traffic produces receipt",malformed_nonce),("Stale transfer plate denied",stale_transfer),
        ("Summary attribution enforced",summary_attribution),("Unknown plate cannot crawl",unknown_plate),
        ("Anonymous training denied",no_training_anonymously),("Challenge timeout denied",challenge_timeout),
        ("Non-object traffic denied with signed receipt",malformed_envelope),
        ("Pending challenge flood denied at cap",saturated_queue),
        ("Expired challenge slots recycled",reclaimed_expired_queue),
        ("Game traffic tuples unique across 60 cases",traffic_tuples_unique)]:
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
        fixture=bootstrap(seed="bot-traffic-game-v0.3",now=1893456000)
        stamp=fixture["created_at"]
        scenario=case["scenario"]
        plate=case["plate"]
        prior=None
        if scenario in ("revoke","revoke_crawler"):
            revoke(fixture,plate,now=stamp)
        elif scenario in ("transfer_old","transfer_new","stale_transfer"):
            prior=copy.deepcopy(audit(fixture)[plate]["credential"])
            transfer(fixture,plate,"alice","bob",now=stamp)
        elif scenario in ("renew","stale_renew"):
            prior=copy.deepcopy(audit(fixture)[plate]["credential"])
            renew(fixture,plate,"alice",now=stamp+300,ttl=100000)
            if scenario=="renew":stamp+=86500
            else:stamp+=300
        elif scenario=="expired":stamp+=86401
        elif scenario=="not_yet":stamp-=60
        elif scenario.startswith("issue_"):
            role=scenario.removeprefix("issue_")
            issue(fixture,"alice",role,now=stamp,plate_id=plate)
        elif scenario not in ("baseline","forged_credential","replay","swapped_challenge","malformed_nonce","malformed_envelope","expired_challenge","forged_proof"):
            raise ProtocolError("unknown game scenario")
        if scenario in ("stale_transfer","stale_renew"):
            decision=request(fixture,plate,case["resource"],case["action"],owner=case["owner"],now=stamp,credential_override=prior)
        elif scenario=="forged_credential":
            forged=copy.deepcopy(audit(fixture)[plate]["credential"])
            forged["payload"]["participation_class"]="commercial"
            decision=request(fixture,plate,case["resource"],case["action"],owner=case["owner"],now=stamp,credential_override=forged)
        elif scenario=="forged_proof":
            decision=request(fixture,plate,case["resource"],case["action"],owner=case["owner"],now=stamp,proof_override="forged-signature")
        elif scenario in ("replay","swapped_challenge","malformed_nonce","malformed_envelope","expired_challenge"):
            ch=challenge(fixture,plate,case["resource"],case["action"],now=stamp)
            if scenario=="replay":
                first=decide(fixture,ch,holder_proof(fixture,"alice",ch),now=stamp)
                _need(first["allow"],"replay setup failed to admit first use")
                decision=decide(fixture,ch,holder_proof(fixture,"alice",ch),now=stamp)
            elif scenario=="swapped_challenge":
                tampered=copy.deepcopy(ch);tampered["action"]="train"
                decision=decide(fixture,tampered,holder_proof(fixture,"alice",tampered),now=stamp)
            elif scenario=="malformed_envelope":
                decision=decide(fixture,[ch],"forged-signature",now=stamp)
                _need(ch["nonce"] in fixture["challenges"],"malformed packet consumed a valid challenge")
            elif scenario=="expired_challenge":
                decision=decide(fixture,ch,holder_proof(fixture,"alice",ch),now=stamp+121)
            else:
                tampered=copy.deepcopy(ch);tampered["nonce"]=[ch["nonce"]]
                decision=decide(fixture,tampered,"forged-signature",now=stamp)
                _need(ch["nonce"] in fixture["challenges"],"malformed traffic consumed a valid challenge")
        else:
            decision=request(fixture,plate,case["resource"],case["action"],owner=case["owner"],now=stamp)
        outcome={"case":case,"decision":decision,"isolated":True,"workspace_unchanged":True,
          "scenario_matches_expectation":decision["allow"]==case["expected_allow"]
            and decision["reason"]==case["expected_reason"]
            and decision["attribution_required"]==case["expected_attribution"]}
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
