# v0.7 bug hunt: findings, reproductions and fixes (2026-10-20)

Twelve defects were found by an external test drill of v0.6. All of them slipped past the
existing 95 unit tests, 22 probes, 60 game cases, 168 matrix cases and 50 ingress cases.
Each finding has a regression class in `tests/test_bughunt_v07.py`.

Those tests were run against unmodified v0.6 first. The red log is in
`evaluation/BUGHUNT-RED-V07.txt`: 30 failed assertions or errors across all 12 findings.

| # | Finding | Where | Fix |
|---|---|---|---|
| 1 | Game "oracle mismatch" guard skipped on a second click. `verdict` was assigned before the check threw, so a retry went straight to scoring and recorded the case as PASSED. | `browser/client.js` `inspect()`, `choose()` | Assign `verdict` only after `scenario_matches_expectation === true`. |
| 2 | Host policies were neither validated nor reported by `audit`. A malformed policy passed import, then broke every page load with a misleading "Internet required" message. In the engine, `decide()` raised `KeyError` after consuming the nonce and wrote no receipt. | `engine.py` `audit_all`, `decide`, `policy_decision`; `client.js` | Added `_validate_policies` (exact fields, known actions and classes) to `audit_all` and `policy_decision`. `audit_all` now reports `policies_match_release` and `policy_changes`, and the import screen shows a warning when they differ. The anonymous branch of `decide()` now sits inside the fail-closed `try`. Startup failures after Python has loaded no longer blame the network and keep Reset, Export and Import usable. |
| 3 | `audit()` accepted signed renew/transfer events that `_transition` refuses to create: dated after the predecessor expired, or with an arbitrary `requested_at` / `accepted_at`. | `engine.py` `audit` | Replay enforces `issued_at <= predecessor.expires_at`. v2 intents and acceptances must carry an integer time equal to the successor's `issued_at`. v1 historical records are unchanged. |
| 4 | `anonymous` could be issued as a real plate ID. The gate always treated it as anonymous traffic, and revocation had no effect. | `engine.py` `issue`, `_validate_credential` | Reserved (case-insensitive) at issue time and on replay. |
| 5 | `bridge()` could raise instead of returning JSON. Examples: `state` or `args` sent as a list or string, deeply nested JSON. | `engine.py` `dispatch`, `bridge` | `dispatch` type-checks `state` and `args`. `bridge` also catches `AttributeError`, `RecursionError` and `OverflowError`. |
| 6 | Non-dict or malformed pending-challenge entries were never pruned. 128 of them blocked new challenges permanently. | `engine.py` `challenge` | Malformed entries are pruned along with expired ones. |
| 7 | `request()` with an unknown owner allocated a challenge and then raised. This leaked a queue slot and wrote no receipt. | `engine.py` `request` | The owner is validated before any challenge is allocated. |
| 8 | Browser and `dispatch` clock frozen at `created_at`, and `ttl` never passed through for renew/transfer. As a result, "Renew" never extended validity. | `engine.py` `dispatch`; `client.js`; `template.html` | `ttl` is forwarded. The registry form gains "Simulated time" and "Plate lifetime" fields (defaults: epoch and 86400, so existing behavior is unchanged). |
| 9 | Two owner labels could share one signing key, so a second label could use the first owner's plate. | `engine.py` `add_owner`, `audit_all` | Duplicate keys are rejected at registration and on audit. The owner seed must also match its public key. |
| 10 | CLI: `--at 0` was silently replaced by the default epoch. The installed `virtual-dmv` command and `python -m virtual_dmv` bypassed the error handler and printed tracebacks. | `cli.py` | `is not None` check. The error handling moved into `main()`, which all entry points use. |
| 11 | Challenge comparison used Python `==`, so `1893456000.0` matched the integer `1893456000`. | `engine.py` `decide` | Compares canonical JSON bytes. |
| 12 | Scenario evidence was timestamped with wall-clock time, so every rebuild changed the HTML and its pins. | `tools/run_scenarios.py` | Honors `SOURCE_DATE_EPOCH`. |

## Remaining limits (not fixed, by design)

- **The 168-tuple policy matrix still differs between runs.** It records receipt hashes, and those include random challenge nonces. Making nonces deterministic would weaken the replay protection being tested, so `SOURCE_DATE_EPOCH` fixes only the timestamp.
- **Policies are still unsigned local data.** A well-formed but altered policy is accepted, with a visible warning. Anyone who can edit the state can also re-sign it with the in-state host seed, which is the existing trust boundary in `docs/THREAT-MODEL.md`.
- **The browser checks used a stub interpreter.** It forwarded every call to the real Python engine, but that is still not a live Pyodide or iPad Safari run.

## Reproduce

```sh
PYTHONPATH=src python3 -m unittest tests.test_bughunt_v07 -v
SOURCE_DATE_EPOCH=1792526400 python3 tools/run_scenarios.py && python3 tools/build_browser.py
```
