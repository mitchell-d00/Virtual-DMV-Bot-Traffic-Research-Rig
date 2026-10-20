# v0.5 crypto/safety regression addendum

Identifier red→green: `_named()` accepted Cyrillic homoglyphs; two tests failed before restricting owner labels and plate IDs to ASCII. See `evaluation/IDENTIFIER-RED-V05.txt`.

Additional late failure: corrupted pending challenge with matching nonce raised a KeyError instead of returning a signed denial. Reproduced red in `evaluation/PENDING-RED-V05.txt`, fixed with validated pending timestamps, and covered by two new unit tests.

This security pass tested the local v0.4 baseline with 14 newly written crypto/safety tests. Pre-fix **24 failures and 3 errors**, most arising from 15 noncanonical base64 alias subcases. Original output: `evaluation/CRYPTO-RED-V05.txt`. Corrections changed `portable.py` and `engine.py` without modifying research papers, plus added a 168-tuple security matrix. See `evaluation/CRYPTO-SAFETY-V05.md`.

# Bot Traffic — red-to-green regression history

Date: 2026-10-20. Release target: v0.2. Research author: Mitchell D. McPhetridge. AI-assisted implementation and tests. This is an **observed software regression**, not external field validation.

## RED: reproduced against v0.1

In the original Python `dispatch(op='game_try')`, case selection used `% len(cases)` and requests ran in the **passed-in mutable registry**. This made the expected game answer change if the operator modified their DMV workspace, and added game receipts to the DMV's working audit journal.

Reproduction (with `PYTHONPATH=src` under the original v0.1):

```python
from virtual_dmv import engine as E
s=E.bootstrap(seed='failure-demonstration',now=1893456000)
print(E.dispatch({'op':'game_try','state':s,'args':{'index':0}})['result']['decision']['reason'])
E.revoke(s,'VDMV-RESEARCH-01',now=1893456000)
print(E.dispatch({'op':'game_try','state':s,'args':{'index':0}})['result']['decision']['reason'])
print('working DMV receipts:',len(s['receipts']))
print(E.dispatch({'op':'game_try','state':s,'args':{'index':-1}})['result']['case']['label'])
```

Observed: `POLICY_ALLOW` before revocation, `UNKNOWN_OR_REVOKED` after revocation; two additional receipts; negative index silently wrapped to last case. The game still displayed case 1's original "allow with attribution" explanation.

Three *new* named unit tests were added **before the fix**: `test_game_case_isolation_after_revocation`, `test_game_does_not_write_live_receipts`, `test_game_rejects_invalid_indices`. They failed, with five reported subtest assertion failures (one isolation, one receipt, three invalid indices). This red run is a local observation, not a cryptographic proof; see `tests/test_engine.py`.

## GREEN: fix and expanded evidence

- `dispatch(game_try)` builds a fresh deterministic, **separate** `bootstrap(seed='bot-traffic-game-v0.2')` fixture on each call.
- Game receipts stay in that fixture; they do **not** change the user's mutable DMV registry.
- Case indices must be integers in `[0, 9]`; invalid values raise `ProtocolError`.
- Each game case declares `expected_allow` and `expected_reason`, checked independently of actual gate output. Scoring refuses mismatched oracle results.
- Expanded regression cases cover post-revocation fixture isolation, local policy edits, all 10 game oracle outcomes, unique scenario signatures, and public evidence publication.
- The public scenario ledger includes individual unit, probe, game, and pending external calculator cases with stable IDs and sources.

## Measurement boundaries

The original 40 Python unit tests and 12 browser-native Python probes already had **overlapping coverage**. A new regression test does not create an independent field experiment. Green status means the documented assertions passed in the recorded local environment. The calculator checks require actual Mitchell Tech browser execution and stay pending until a user runs/imports them.

Browser UI tests using a mocked interpreter prove DOM interactions only, not real Pyodide startup, iPad Safari compatibility, production security, or the theories in the four papers.

## v0.3 traffic-only follow-up — 2026-10-20

This section is appended to v0.2, not retroactively changing the earlier published claim. New tests in `tests/test_traffic_v03.py` ran against the unmodified v0.2 challenge gate and 10-case game **before** repair. Their observed red run is retained verbatim as `evaluation/TRAFFIC-RED-V03.txt`. Four new unit methods failed with 2 failures and 13 individual errors/subtests, including unhashable nonce type crashes, a forced nonce overwrite, missing attribution oracle fields and insufficient adversarial traffic coverage.

A challenge with `nonce: []` or `nonce: {}` crashed `decide()` before a host receipt could be issued. This is a real robustness bug for malformed external JSON; it is not evidence of successful credential forgery. A collision injected with `unittest.mock.patch(secrets.token_hex, ...)` overwrote the first outstanding challenge. Cryptographic random collisions are ordinarily extremely improbable; the correctness requirement is still to preserve every pending request.

**GREEN:** malformed nonce returns `MALFORMED_CHALLENGE` with a host-signed denial receipt while retaining a legitimate pending challenge. Nonce issuance checks for existing keys, retrying boundedly. There are now 36 distinct game cases covering negative authorizations, time, transfers, key proof, replay and attribution; all game oracles are checked against independently declared `(allow, reason, attribution_required)`. The desktop green run, scene ledger and browser-mock smoke results appear in `docs/TESTING.md`.

Distinct scenario IDs are tracked for inspectability, not counted as independent natural trials. The public prototype still has no real issuer federation, legal access enforcement, or independent production security assessment.

## v0.4 — malformed traffic envelope and pending-queue saturation (2026-10-20)

A fresh `tests/test_traffic_v04.py` suite was run against the packaged, unmodified v0.3 Python gate **before making the fixes**. The raw diagnostic output lives in `evaluation/TRAFFIC-RED-V04.txt`.

1. **RED:** passing `None`, `[]`, a list payload, text, integer, or boolean to `decide()` raised `ProtocolError("invalid challenge shape")`. Unlike a malformed `nonce` *inside an object* (fixed in v0.3), these malformed envelopes produced no host-signed denial receipt. Six subtest errors reproduced this failure.
2. **RED:** after 128 unopened requests, a 129th challenge was issued without a cap. An expired backlog of 128 pending entries was retained even when 121 seconds had passed, because challenge allocation did not prune old requests. Other new assertions detected both.
3. **RED:** the new 60-case scenario requirements did not exist in v0.3, as expected. The game previously had 36 cases.
4. **GREEN:** `decide()` produces `MALFORMED_CHALLENGE` denial receipts for non-object packet values, preserves legitimate outstanding challenges, verifies the signed receipt chain, and retains normal request admission.
5. **GREEN:** challenge issuance prunes expired map entries, limits the number of *active* requests to 128 per local registry, preserves existing nonexpired requests on overflow, and recovers capacity after redemption. The saturation test deliberately exhausts the bound.
6. **GREEN:** all 60 unique five-field scripted game scenarios match separately written allow/deny, reason and attribution expectations. `GAME-037..060` add new locally declared host-permission and malformed packet cases without changing the original 36 identifiers.

**Limits:** simulated queue tests are not performance throughput measurements; they do not establish real service capacity. A 128-request limit does not protect from signed-receipt flood, transport flooding, or multi-registry abuse. Some scenarios overlap, and counted unit/probe/game results are not independent evaluations. External Mitchell Tech calculator checks remain pending.

### Browser smoke harness v0.4 fixture correction

The first mobile Chromium mock test reported **18/22** because the JavaScript fixture in `tests/browser_ui_smoke.py` still used `passed:18` while the new test set comprised 22 distinct probes. `tests/browser_ui_smoke.py` was fixed to report the 22 synthetic results it actually constructs. Both 390px and 1280px stub-runtime browser smokes then passed, including all 60 game decisions. This demonstrates that the test harness was wrong, *not* that the real gate computed 18/22; the native Python 22-probe bench was checked separately.
