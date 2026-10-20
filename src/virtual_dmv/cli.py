"""Portable, no-dependency CLI. Persists simulation state as human-reviewable JSON."""
import argparse
import json
import pathlib
import sys
from .engine import bootstrap, dispatch, audit_all


def _run(argv=None):
    parser=argparse.ArgumentParser(prog="virtual-dmv",description="Local virtual DMV research simulator")
    parser.add_argument("operation",choices=["new","roster","audit","issue","owner","request","transfer","renew","revoke","bench","economics","casebook","help"])
    parser.add_argument("--state",default="local/demo-state.json",help="Local JSON state path (contains DEMO private signing seeds)")
    parser.add_argument("--owner",default="alice")
    parser.add_argument("--role",default="research")
    parser.add_argument("--plate",default="VDMV-RESEARCH-01")
    parser.add_argument("--new-owner",default="bob")
    parser.add_argument("--resource",default="research-library")
    parser.add_argument("--action",default="crawl")
    parser.add_argument("--rounds",type=int,default=100)
    parser.add_argument("--adoption",type=float,default=0.5)
    parser.add_argument("--seed",type=int,default=7)
    parser.add_argument("--at",type=int,default=None,help="Simulation Unix time; defaults to the registry epoch")
    args=parser.parse_args(argv)
    path=pathlib.Path(args.state)
    if args.operation=="new":
        if path.exists(): parser.error("state already exists; refuse overwrite")
        state=bootstrap(now=args.at if args.at is not None else 1893456000)
        result={"created":str(path)}
    else:
        if not path.exists():parser.error("state missing; first run: python -m virtual_dmv new")
        state=json.loads(path.read_text(encoding="utf8"))
        ops={"roster":"roster","audit":"audit","owner":"owner","issue":"issue","request":"request","transfer":"transfer","renew":"renew","revoke":"revoke","bench":"bench","economics":"economics","casebook":"casebook","help":"help"}
        options={"name":args.owner,"owner":args.owner,"role":args.role,"plate_id":args.plate,
                 "old_owner":args.owner,"new_owner":args.new_owner,"resource":args.resource,
                 "action":args.action,"rounds":args.rounds,"adoption":args.adoption,"seed":args.seed,
                 "now": args.at if args.at is not None else state["created_at"]}
        if args.operation not in ("bench","help","casebook","economics"):
            audit_all(state)
        output=dispatch({"op":ops[args.operation],"state":state,"args":options})
        state,result=output["state"],output["result"]
    if args.operation in ("new","owner","issue","request","transfer","renew","revoke"):
        path.parent.mkdir(parents=True,exist_ok=True)
        import os,tempfile
        fd,tmp=tempfile.mkstemp(dir=path.parent,prefix=".vdmv-",text=True)
        try:
            os.fchmod(fd,0o600)
            with os.fdopen(fd,"w",encoding="utf8") as handle:
                json.dump(state,handle,indent=2,sort_keys=True);handle.write("\n");handle.flush();os.fsync(handle.fileno())
            os.replace(tmp,path)
        finally:
            if os.path.exists(tmp):os.unlink(tmp)
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0


def main(argv=None):
    """Entry point for `virtual-dmv`, `python -m virtual_dmv` and `python cli.py`.

    Protocol and input errors print one line and exit 2 instead of a traceback.
    """
    try:
        return _run(argv)
    except (KeyError,ValueError) as error:
        print("Error:",error,file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
