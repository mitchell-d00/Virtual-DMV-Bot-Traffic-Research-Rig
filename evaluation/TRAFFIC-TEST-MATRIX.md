# Bot Traffic v0.4 — New traffic-case matrix

Versioned successor to v0.3. The original 36 game IDs have been retained and 24 new unique tuples added (`GAME-037..060`). Each game case declares the expected allow/deny, specific reason and attribution flag *before* checking the gate result. Traffic dimensions:

- **Anonymous versus verified:** discover, crawl, index, summarize, redistribute, training, archival scope across `open-archive`, `open-index`, `research-library`, `licensed-training-data`.
- **Local resource owner rule:** public indexing does not imply redistribution; public discovery does not grant anonymous crawling; research library limits indexing and archives; training/crawling permissions remain separate.
- **Adversarial payloads:** a non-object challenge packet must be denied and receipted, retaining any real challenge; a genuinely expired challenge is invalid even if the requester knows the holder's key.
- **Saturation:** 128 pending active requests permitted in the local fixture, 129th rejected; redemption releases capacity, >120-second-expired slots are reclaimed.
- **Original v0.3 attack coverage:** nonce arrays and objects, forced collisions, revocation, transfer, renewal, forged proof, stale credentials, challenge replay and time boundaries.

Tests: `tests/test_traffic_v04.py`; native Python probes `PROBE-019..022`; playable new game `GAME-037..060`. Archived first failing run: `evaluation/TRAFFIC-RED-V04.txt`. Current values are synthetic local assertion outcomes, not measured third-party traffic.

---

# Bot Traffic v0.3 — Traffic Scenario Matrix

Date: 2026-10-20 · Mitchell D. McPhetridge · AI-assisted implementation/test operator.

## Source boundaries

The core executable gate lives in `src/virtual_dmv/engine.py`. The authoritative game oracle is a handwritten tuple in `traffic_cases()`; it is not derived from `policy_decision` or `request` at runtime. `game_try` creates a fresh signed, isolated fixture on each run. Browser-game feedback comes from the real Python gate via Pyodide when that runtime actually loads. DOM browser smoke uses a **mock**, not Pyodide; the browser suite must be run from the actual Pages deployment to establish live-runtime execution.

## No-repeats contract

Every game row must have a unique, stable `GAME-NNN` identifier and unique `(scenario, plate, owner, resource, action)` signature. Old `GAME-001..010` meanings remain intact. New records `GAME-011..036` add threat/temporal context as the `scenario` field; the page's evidence ledger displays that context rather than hiding repeated target names. Unit and probe IDs are distinct documented case identities but may overlap in behavioral coverage. External arithmetic checks remain pending until independently executed on Mitchell Tech.

## Attack and participation families

| Scenarios | Coverage | Expected observable boundary |
| --- | --- | --- |
| GAME-001..010 | Baseline 2026-10-20 cases | Verified identity is not necessarily permission; anonymous traffic depends on owner policy |
| GAME-011,031 | Revocations | Previously registered plate denies after revocation |
| GAME-012..013 | Transfer | Old private key denied, new signing key accepted |
| GAME-014..016 | Time window | Renewed accepted; expired/premature denied |
| GAME-017..018,033 | Stale/forged credential | Signed registry's latest revision required |
| GAME-019..021 | Replayed, modified, malformed challenges | Never admit replay/alteration; malformed nonce gives signed denial receipt |
| GAME-022..024 | Unknown ID and local scope | Unknown plate denied; class-only index denied; admitted summaries require attribution |
| GAME-025..028,035 | Role classes | Archival/agentic/commercial classes admit only resource-approved actions |
| GAME-029..030,036 | Unknown traffic | Explicit anonymous crawl allowed; undesignated actions/training denied |
| GAME-032,034 | Forged holder and redistribution | A genuine plate still requires a valid holder proof and action permission |

## Red→green traffic defects

- **TRAFFIC-REG-004 — malformed request type:** v0.2 unhashable JSON nonce crashed in `dict.pop`. v0.3 returns `MALFORMED_CHALLENGE`, records a host-signed receipt, leaves outstanding real challenges available.
- **TRAFFIC-REG-005 — duplicate nonce overwrites pending challenge:** v0.2 used one unguarded random nonce; forced collision overwrote the older unconsumed request. v0.3 retries up to eight times for a distinct nonce and errors without overwriting if exhausted.
- **TRAFFIC-REG-006 — narrow fixture:** v0.2 lacked temporal/forgery game cases and didn't assert attribution in the scenario oracle. v0.3 contains 36 context-unique cases, independent expectations across admit/reason/attribution, and semantic replay-stability checks.
- **TRAFFIC-REG-007 — reset of exported game history:** v0.2 reset the score but retained played-round history; v0.3 clears that in-memory history when starting a new shift.

## Reproduction

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 tools/run_scenarios.py
python3 tools/build_browser.py
python3 tests/browser_ui_smoke.py
```

The test runner records each case's name, Python identifier, expected assertion, observed outcome and source in `evaluation/SCENARIO-RESULTS.json`. Unit tests and game checks overlap: **scenario count is not independent scientific evidence**. A forced nonce collision in tests uses `unittest.mock.patch` to verify the branch; it does not estimate collision likelihood in nature.
