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
