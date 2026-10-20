# Validation, source pins and replication status — v0.2

## Verified here on 2026-10-20

- 51/51 standard-library Python unit tests on locally rebuilt source, including the new game fixture isolation/strict-index regressions.
- Original RED reproduction is documented in `evaluation/REGRESSION-HISTORY.md`: three new tests failed before repair, with five failing subtest assertions.
- 12/12 independent-invocation Python gate probes from `run_bench()`. These overlap with unit-test coverage; do not sum as independent validations.
- 10/10 game-script expected decisions match the Python gate in a fresh seeded game fixture; the game suite does not mutate live DMV receipts.
- Public release scenario ledger 78 unique IDs: 51 unit, 12 browser probes, 10 game, five pending Mitchell Tech checks. No duplicate calculator arithmetic expression strings.
- Source embedding and SHA-256 pin checks passed, original paper hashes unchanged, Node.js syntax check passed.
- Chromium wiring smoke at 390px and 1280px with stubbed Pyodide; game, ledger filtering, bench, and operator-submitted calculator JSON ingestion exercised. **Not a live-Pyodide or deployed-site test.**

## Reproduce from checkout or extracted ZIP

```sh
python3 tools/run_scenarios.py        # real Python suites + public JSON evidence
python3 tools/build_browser.py        # regenerates index.html with source/evidence snapshot
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 tests/browser_ui_smoke.py    # optional Playwright / Chromium mock-UI smoke
```

`evaluation/SCENARIO-RESULTS.json` is a **recorded** unit-suite result from the exact source digest in that document; it does not prove visitors have rerun the suite. Browser probes and game cases are rerunnable from the web page. External Mitchell Tech checks are marked pending until a user executes the separate-origin calculator and submits JSON.

## Not yet verified

- Real Pyodide bootstrap from CDN in Safari on the user's iPad 9 or deployed GitHub Pages; cross-browser/mobile hardware results.
- Actual Mitchell Tech browser-origin execution of external numeric probes. User-submitted JSON does not authenticate its origin.
- Production key security, issuer federation, real-world permissions, or economic adoption predictions.
- Independent replication of 51 local-unit pass results or objective correctness beyond the given cases.

## Next falsifiers

- Measure reproducibility across sessions and platforms, record Safari/WebAssembly errors, and compare source pins to deployed release.
- Run known-key signature interoperability against a vetted Ed25519 implementation; simulate external checkpoint loss/replay attacks.
- Model competing registries, identity cloning and false attribution, run real resource-owner consented trials with reported denominators.
