# Virtual DMV / Machine Participation Governance Lab

**Mitchell D. McPhetridge — four-paper research corpus + executable reference rig.**

This repository explores a focused governance question: **Under what locally declared conditions may an identified machine consumer participate in a resource relationship?** It does not regulate machine intelligence, issue real credentials, or establish legal permissions.

Its executable demonstration includes a local virtual DMV registry, demonstration Ed25519 plates, proof-of-possession challenges, scope-aware host permissions, renewal, ownership transfer, revocation, signed audit receipts, a synthetic economic adoption model, and the playable **Bot Traffic** scenario bench.

The research proposal comes from the four supplied papers preserved byte-for-byte under `PAPERS/`. The code is a **new, falsifiable prototype**, not evidence that the papers' adoption or scalability predictions have already been established.

## Quick start — iPad / browser

1. Open the published [GitHub repository](https://github.com/mitchell-d00/Virtual-DMV-Bot-Traffic-Research-Rig) or upload a release ZIP's extracted contents to a fork.
2. In repository Settings → Pages, deploy `main` / root (`index.html`). Open that HTTPS link in Safari/Chrome.
3. Allow one-time loading of **Pyodide v0.27.7** from jsDelivr. The Python engine, policies, tests, and demo keys run in your browser; no account, paid LLM, backend, or API key is used by the lab.
4. Play **Bot Traffic**, visit **Virtual DMV** to issue/transfer/revoke plates, then run **Test bench**. The game is isolated from registry edits: it always exercises a declared deterministic fixture.
5. Open **Scenario ledger** to see all 78 cataloged cases (51 recorded CLI unit tests, 12 rerunnable browser probes, 10 playable game cases, and 5 pending Mitchell Tech cross-checks), including expected/observed outcomes and source links. Download JSON evidence if desired.
6. Export JSON if you need to move the demo workspace to another browser/iPad. Import it on the other device. There is **no automatic multi-user synchronization**.

`index.html` contains the entire interface, JavaScript transport and actual Python engine source. **Important:** its Pyodide Python/WebAssembly interpreter is downloaded at load time and is **not bundled**. Thus the first load and uncached reload require network access. This is a single-file *application source*, not a self-contained offline Python distribution. For a fully offline runtime, vendor and package Pyodide assets separately. The GitHub Pages URL runs code publicly; another person's browser storage is NOT remotely accessible just by knowing the URL.

## Quick start — Python

Requires Python 3.10+, **no third-party modules** for the core or tests.

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 tools/run_scenarios.py
python3 tools/build_browser.py
PYTHONPATH=src python3 -m virtual_dmv new --state local/demo-state.json
PYTHONPATH=src python3 -m virtual_dmv roster --state local/demo-state.json
PYTHONPATH=src python3 -m virtual_dmv request --state local/demo-state.json --plate VDMV-RESEARCH-01 --owner alice --resource research-library --action summarize
PYTHONPATH=src python3 -m virtual_dmv audit --state local/demo-state.json
PYTHONPATH=src python3 -m virtual_dmv bench --state local/demo-state.json
PYTHONPATH=src python3 -m virtual_dmv economics --state local/demo-state.json --rounds 200 --adoption .75
```

Optional: `python3 -m pip install -e .` then use the `virtual-dmv` command.

## Repository layout (MPLPB-style)

```text
PAPERS/                  Four original author-supplied .txt papers (unaltered)
CORPUS/                  Indexed architecture notes by research layer
SPECS/                   Example machine-readable host participation policies
src/virtual_dmv/         Canonical, standard-library Python engine
browser/                 Readable HTML template, JavaScript and CSS
index.html               Built single-file browser UI, embeds same Python source
examples/                Scriptable initial test scenario
tests/                   Full regression + cryptographic fixture tests
evaluation/              78-case evidence ledger, red→green history, calculator protocol
docs/                    Threat model, platform/API instructions, source byte pins
CONTENTS                  Human-readable corpus and code index
CITATION.cff             Attribution and software citation
LICENSE                  Code license; paper reuse reserved to paper author
```

## Five implementation boundaries

1. **Identity is not permission.** A verified plate is checked against a local host policy for a specific `resource` + `action` + `participation_class`. Default deny; an explicitly public resource may allow some anonymous actions.
2. **Owner control is demonstrated, not certified.** Plate renewal and transfer require the old demo owner's Ed25519 signature and the incoming owner's acceptance signature; the resource gate requires a fresh signed challenge. The registry issuer can revoke a plate. The new owner can use the transferred plate; the old owner cannot.
3. **Audit is only as trusted as its authority and checkpoints.** Hash chains and signatures detect ordinary alterations and invalid transitions under the demo keys. They cannot detect deletion of an entire uncheckpointed suffix or corruption by an actor controlling the issuer/host signing seeds.
4. **Permissions are illustrative.** HTML meta tags, robot hints, and the bundled JSON policy are local experiment proposals. They are not universal web standards and do not themselves confer legal rights or stop hostile bots.
5. **Economics are hypothetical.** Bot Traffic cases and the adoption payoff model are author-designed synthetic scenarios. Scores measure consistency with those rules, not predictions of actual companies' behavior.

## Browser JavaScript API

```js
await window.VirtualDMV.ready();
const roster = await window.VirtualDMV.command('roster');
const gate = await window.VirtualDMV.command('request', {
  plate_id: 'VDMV-RESEARCH-01', owner: 'alice',
  resource: 'research-library', action: 'summarize'
});
console.log(gate.allow, gate.reason, gate.receipt_hash);
await window.VirtualDMV.command('bench');
```

This JavaScript object calls the **same Python engine** through Pyodide. It is page-local and is not a remote HTTP endpoint. Scripts running in the page have access to the demo workspace; only use trusted scripts.

## Reproducible red→green work and public scenario ledger (v0.2)

**Red, reproduced from v0.1:** game cases were evaluated against the mutable DMV registry. Revoking a research plate made the first scripted "admit" case return denial, despite the unchanged written answer. The game also wrote host receipts to the player's DMV journal; negative indices silently wrapped around. The new regression tests were run *before* repair and failed.

**Green:** each `game_try` uses its own seeded, deterministic fixture, does not mutate live receipts, rejects out-of-range indices, and checks the independent game-case oracle. The release now has **51/51 passing local Python tests**, plus **12/12 Python gate probes** and **10/10 game oracles** in local runs. Browser UI wiring passed **390px and 1280px** using a stub Python interpreter, not a live Pyodide download or iPad test.

The file `evaluation/SCENARIO-RESULTS.json` stores 78 unique IDs: 51 recorded unit cases, 12 rerunnable Python probes, 10 game cases, and **5 pending** Mitchell Tech arithmetic cross-checks. IDs and exact questions are deduplicated; overlapping *behavior* across test banks is not presented as independent evidence. The browser includes a visible searchable **Scenario ledger** and a JSON evidence export. `evaluation/REGRESSION-HISTORY.md` records the original failure and repair.

### Use Mitchell Tech as a second arithmetic instrument

Under **Scenario ledger**, copy a unique five-expression batch script. Paste it into the JavaScript console on the [Mitchell Tech calculator's own website](https://mitchell-d00.github.io/Mitchell-Tech-V120.2-A-self-teaching-scientific-and-graphing-calculator-/), where `window.MitchellTech.calculate()` is exposed. Paste its JSON results back into Bot Traffic to compare the arithmetic. **These calculator checks remain pending in the published release until the other site actually runs them;** imported results are operator-submitted, not remotely attested. See `evaluation/CALCULATOR-CROSSCHECK.md`.

An experiment earns confidence by surviving constraints, not by a high mock score. RFC 8032 Ed25519 reference fixtures are tested, but the pure-Python implementation remains educational, non-production code. See `docs/TESTING.md` and `evaluation/REPLICATION-PROTOCOL.md`.

## Important security warning

**Do not deploy this as a real authentication, credential issuance, licensing, or payment system.** The pure-Python cryptographic reference is intentionally not side-channel hardened or independently audited. Demo signing seeds are stored in and exported from browser JSON. Real deployments need audited crypto and key custody, trusted issuer discovery, encrypted and authenticated state, rate limits, anti-abuse controls, secure network enforcement, and legal review.

## Build and check the single-file page

```sh
python3 tools/build_browser.py
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

See `docs/TESTING.md` for limits and the browser smoke status. Regenerate evidence before rebuilding the browser: `python3 tools/run_scenarios.py`, then `python3 tools/build_browser.py`. `docs/ENGINE-SOURCE-PINS.json` contains the exact hashes of the embedded Python source and the generated HTML.

## Attribution

Research papers: Mitchell D. McPhetridge. Code in this draft ZIP is provided as an AI-assisted starter implementation for the author's inspection, modification and testing. The original papers have not been edited. See `PAPERS/README.md` and `CITATION.cff`.
