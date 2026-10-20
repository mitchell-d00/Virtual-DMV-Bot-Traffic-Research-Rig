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
5. Open **Scenario ledger** to see the updated case ledger (Python unit tests, 22 rerunnable browser probes, 60 playable game cases, 168 unique signed policy-matrix tuples, and 5 pending Mitchell Tech cross-checks), including expected/observed outcomes and source links. Download JSON evidence if desired.
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
evaluation/              Evidence ledger, crypto/safety and traffic regression history
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

## v0.7 bug-hunt fixes (2026-10-20)

**415 recorded local passes:** 115 Python unit tests (20 new in `tests/test_bughunt_v07.py`), 22 probes, 60 game cases, 168 matrix cases and 50 ingress cases, with five calculator checks still pending.

This release fixes 12 defects found by an external test drill. Among them: a game oracle guard that a second click could skip; unvalidated host policies that could break page startup; audit replay that was looser than event creation; a reserved `anonymous` plate ID; non-JSON bridge failures; and ttl and clock handling in the browser.

Every finding was reproduced red before it was fixed. See `evaluation/BUGHUNT-V07.md` and `evaluation/BUGHUNT-RED-V07.txt`. The registry form now has **Simulated time** and **Plate lifetime** fields.

Current regenerated counts: [docs/CURRENT-TEST-RESULTS.md](docs/CURRENT-TEST-RESULTS.md).

## v0.6 verified security/traffic iteration (2026-10-20)

**395 recorded local passes / 400 unique evidence entries:** 95 Python unit tests, 22 Python probes, 60 isolated Bot Traffic decisions, 168 policy/receipt matrix cases, 50 unique ingress cases and five still-pending external Mitchell Tech calculator checks. Some behaviors overlap across banks; counts are not independent experiments. Browser UI wiring is tested with a stub interpreter, not a live Safari/Pyodide proof.

**New red→green:** rejected oversized and non-string plate IDs *before* challenge allocation, fail-closed handling of malformed resource types, no backdated issuer revocations or signed audit records, and exact-integer credential metadata (no `True` as revision `1`). See `evaluation/INPUT-BOUNDARIES-RED-V06.txt` (original failed assertions) and `evaluation/INPUT-BOUNDARIES-V06.md` (reproduction and limitations).

A new **50-case unique traffic ingress matrix** separately records invalid plate, resource and action types, 12 distinct unknown registered-shape plates, and an authorized positive control. Each case shows input, expected behavior, observed behavior and local-test provenance. All source papers are kept byte-identical. The local cryptography remains educational, the browser keys exportable, and browser runtime startup not independently checked on iPad hardware.

## v0.5 verified snapshot (2026-10-20)

**334 recorded local passes / 339 visible scenario entries:** 84 Python unit tests, 22 Python gate probes, 60 isolated Bot Traffic game outcomes, 168 unique signed policy/role/action requests, and five explicitly pending external Mitchell Tech calculator checks. These are overlapping synthetic checks, not 334 independent security experiments. The 390px/1280px Chromium UI smoke exercised controls with a stub interpreter; the live hosted Pyodide runtime and iPad Safari have **not** been verified here.

## Crypto and safety v0.5 — signed consent and fail-closed traffic

The v0.5 security pass adds 17 focused crypto/safety tests (14 in the initial red run, three further checks) plus an exhaustive 168-tuple synthetic resource × role × action matrix. It also protects the admission gate from poisoned imported pending-challenge entries and rejects Unicode look-alike owner/plate IDs. It fixes noncanonical signature/public-key encodings, strengthens signed ownership consent to bind every field of its exact successor credential, prevents invalid retroactive transfers from appending broken journal entries, and ensures malformed, cyclic, non-JSON, deep or oversized requests receive small signed denials instead of crashing receipt creation. A separate optional development test checks eight known-seed Ed25519 signatures against the mature `cryptography` package. Runtime and core tests still have no third-party dependency.

**Compatibility:** historical v1 owner-intent signatures remain readable; new transitions emit v2 successor hashes with both outgoing and incoming owner authorization. Earlier consent records are not retroactively upgraded. An issuer that can rewrite and re-sign all private local data and uncheckpointed history remains a privileged trust boundary, not a problem solved by this release. See `evaluation/CRYPTO-RED-V05.txt`, `evaluation/CRYPTO-SAFETY-V05.md`, and `docs/THREAT-MODEL.md`. **Never use browser-exported demo private keys as real credentials.**

## Bot Traffic v0.4 — traffic saturation and malformed-envelope red→green

**New distinct shift:** `GAME-037..060` exercises 24 new combinations of unknown/registered machine identity, resource scope, crawl versus indexing versus redistribution, and two hostile-packet cases. `GAME-001..036` are preserved. Expected allow, reason and attribution are independently declared; **60/60** scripted decisions passed when recorded locally. These are synthetic test vectors, not outside-world events.

**Reproduced baseline bugs:** the unmodified v0.3 gate raised `ProtocolError` without a denial receipt for a non-object challenge envelope. Creating requests without redeeming them accumulated unlimited pending challenges, and even stale expired challenges were never pruned from the map. The six new `tests/test_traffic_v04.py` methods failed before repairs (including six malformed-envelope subtest errors); see `evaluation/TRAFFIC-RED-V04.txt`.

**Fixed:** malformed envelopes now receive a host-signed `MALFORMED_CHALLENGE` denial, without invalidating valid outstanding requests. The *local demonstration* registry enforces **128 live pending challenges** and prunes expired challenges before new allocation. A saturated queue rejects further issuance until capacity is released; real admission of an existing request frees a slot. This is a per-registry reference limit, **not** network-layer rate limiting or protection from deliberate multi-identity abuse.

Current replay evidence: **62 local Python unit checks, 22 Python/browser-rerunnable gate probes, 60 independent-oracle game scripts, five pending Mitchell Tech checks** = **149 distinct scenario records**, with **144 local passes and five explicitly pending**. Behaviors overlap across banks; this is not 144 independent scientific findings. See `evaluation/TRAFFIC-TEST-MATRIX.md`, `evaluation/REGRESSION-HISTORY.md` and `docs/TESTING.md`.

## Traffic-focused adversarial shift and version history (v0.3)

**New, reproducible RED findings against published v0.2:** a JSON list/dictionary as the challenge `nonce` caused a Python `TypeError` before a denial receipt could be issued. A forced duplicate nonce overwrote a still-live pending challenge. The new `tests/test_traffic_v03.py` suite also initially failed because the game only contained 10 cases and the game oracles did not explicitly declare attribution. Its pre-fix run is retained in `evaluation/TRAFFIC-RED-V03.txt` and described in `evaluation/REGRESSION-HISTORY.md`.

**GREEN v0.3:** malformed nonce types receive a signed `MALFORMED_CHALLENGE` denial receipt without consuming a valid challenge; challenge issuance refuses nonce collisions (bounded retry, errors on exhaustion). The playable Bot Traffic shift now contains **36 unique scripted scenario tuples**, preserving `GAME-001` through `GAME-010` and introducing `GAME-011` through `GAME-036` for revocation, transfer, renewal, early/late access, credential freshness, replay, tampering, attribution, new role classes and unknown traffic. Gate answers are checked against separately declared admit/deny, reason **and attribution** expectations. The game remains isolated from the mutable DMV workspace.

The release evidence documents **56 local Python unit tests, 18 native Python probes, 36 individually playable game cases and 5 pending external Mitchell Tech calculator checks** (115 distinct IDs; 110 locally passed and 5 unrun). Duplicated behavior across banks is labeled as overlap, not independent scientific confirmation. A fresh-extraction ZIP test and mobile/desktop mock-interpreter smoke are required release gates. The full game can be replayed from the browser bench; `Run game oracles` compares every scripted expectation, not merely the player's score.

See `evaluation/TRAFFIC-TEST-MATRIX.md`, `evaluation/SCENARIO-RESULTS.json`, `evaluation/REGRESSION-HISTORY.md`, and `docs/TESTING.md`.

## Reproducible red→green work and public scenario ledger (v0.2)

**Red, reproduced from v0.1:** game cases were evaluated against the mutable DMV registry. Revoking a research plate made the first scripted "admit" case return denial, despite the unchanged written answer. The game also wrote host receipts to the player's DMV journal; negative indices silently wrapped around. The new regression tests were run *before* repair and failed.

**Green:** each `game_try` uses its own seeded, deterministic fixture, does not mutate live receipts, rejects out-of-range indices, and checks the independent game-case oracle. The release now has **51/51 passing local Python tests**, plus **12/12 Python gate probes** and **10/10 game oracles** in local runs. Browser UI wiring passed **390px and 1280px** using a stub Python interpreter, not a live Pyodide download or iPad test.

The v0.2 archived reference stored 78 unique IDs: 51 recorded unit cases, 12 rerunnable Python probes, 10 game cases, and **5 pending** Mitchell Tech arithmetic cross-checks. IDs and exact questions are deduplicated; overlapping *behavior* across test banks is not presented as independent evidence. The browser includes a visible searchable **Scenario ledger** and a JSON evidence export. `evaluation/REGRESSION-HISTORY.md` records the original failure and repair.

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
