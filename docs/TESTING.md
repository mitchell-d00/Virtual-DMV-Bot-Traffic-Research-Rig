# Validation and regression record — v0.6

**Completed v0.6 evidence generation:** 94/95 Python unit tests, 22/22 Python probes, 60/60 Bot Traffic oracles, 168/168 host policy tuples and 50/50 unique ingress cases. Five external calculator cases remain pending. The first pre-build evidence attempt recorded two obsolete embedded-source/pin failures; rebuilding source and rerunning produced 395 local passes, zero recorded failures.

The standalone browser embeds a gzip-compressed, base64-encoded copy of the **exact** scenario JSON, validated by `test_embedded_compressed_scenarios_are_exact`. No scenarios are removed. It requires a browser with built-in `DecompressionStream` and still downloads Pyodide on first load; neither an HTTP test nor a real iPad runtime test is claimed. This compact encoding avoids oversized upload payloads while retaining the complete public evidence in the ZIP and on GitHub.

The v0.6 tests are additive to all previous v0.5 tests, with a separate `evaluation/INPUT-BOUNDARIES-RED-V06.txt` preserving failures observed before fixes. See `evaluation/INPUT-BOUNDARIES-V06.md`. A new 50-case ingress matrix checks preallocation safety, typed protocol denials and valid but unknown plates. All historical 60 Bot Traffic scripted cases remain unchanged, and the 168 signed policy tuples are retained. Unit/pass counts are updated in the release record after full-suite completion.

Browser UI smoke uses an explicitly **stubbed** Python loader and measures wiring/visibility, not real Pyodide execution or iPad hardware compatibility. External calculator cases remain unexecuted and must be marked pending.

# Validation, release evidence and limits — v0.5

**v0.5 final gate:** 84/84 local unit tests passed; 22/22 native Python probes, 60/60 synthetic game oracles, 168/168 signed policy-matrix cases. Five Mitchell Tech checks remain pending. Chromium desktop/mobile viewport smoke passed with mocked Pyodide startup, not the live runtime. Full source and environment should be independently retested before field use.

The new `tests/test_crypto_v05.py` contains 17 crypto/traffic safety cases (14 in the archived pre-fix run and three additional compatibility/boundary/fuzz checks) with an archived **pre-fix red** result in `evaluation/CRYPTO-RED-V05.txt`. The optional external differential uses `cryptography` only in the developer's test environment, and never changes the shipping standard-library engine.

`tests/test_pending_integrity_v05.py` adds two tests for maliciously corrupted local pending request entries, including a red `KeyError` reproduction before a fail-closed denial fix.

`tests/test_identifier_v05.py` records two red→green regressions rejecting Cyrillic look-alike owner and plate identifiers, with the original failures archived under `evaluation/IDENTIFIER-RED-V05.txt`.

`tools/run_security_matrix.py` enumerates **168 distinct signed synthetic requests**, every combination of four resources, five registered classes plus anonymous, and seven actions. Every row checks expected allow/deny, reason, attribution and receipt hash; receipts form a verified signed chain. The 168 combinations are **not independent field findings**.

Repeat the release gates in this order:

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 tools/run_security_matrix.py
PYTHONPATH=src python3 tools/run_scenarios.py
python3 tools/build_browser.py
python3 tests/browser_ui_smoke.py
```

Run the same commands after extracting the release ZIP. The UI smoke uses mocked Python startup; do not report it as live Pyodide/CDN/Safari execution. A real iPad test needs the hosted release and explicit storage/refresh, transfer, and real Python checks. Review `docs/THREAT-MODEL.md` before using the result.

# Validation, release evidence and limits — v0.4

## New traffic saturation test (2026-10-20)

Reproduce the red→green sequence in `evaluation/REGRESSION-HISTORY.md` with archived red output `evaluation/TRAFFIC-RED-V04.txt` and the new `tests/test_traffic_v04.py` tests. The v0.3 baselines were tested locally; the prior GitHub published main was v0.2 when this work began.

- **RED:** non-object traffic envelopes raised exceptions instead of returning signed denial receipts; pending challenges were unbounded and stale expired entries never pruned.
- **GREEN:** non-object packets produce `MALFORMED_CHALLENGE` and an intact host-signed receipt. At most 128 nonexpired pending challenges are held per local demo state; overflows are rejected at issuance and expired slots reclaimed. This is *not* a substitute for network/IP rate limits, distributed admission controls, or secure server-side storage.
- **Python checks:** 62/62 unit checks, 22/22 browser-rerunnable native Python probes, 60/60 game oracles with `(allow, reason, attribution)` expectations, unique scenario IDs and no repeated 5-field traffic tuples within the game bank.
- **Archive:** 149 recorded IDs (62 unit + 22 probe + 60 game + five pending external Mitchell Tech questions). Archive outcomes are local developer-authored tests, not independently reproduced evidence. A UI running mock-Pyodide does not count as a Python runtime validation.
- **Browser:** local Chromium smoke at 390px and 1280px with fake `loadPyodide()` injected; all 60 game buttons, bench controls, scenario filtering and calculator import wiring exercised. The first v0.4 smoke failed because its **mock fixture** still claimed `passed:18` while declaring 22 cases; the fake response was corrected to 22/22 and the smoke reran green at both widths. This was an integration test-fixture mismatch, not an observed Python gate failure. Real Safari/iPad or hosted Pyodide use remains untested unless a separate documented real-runtime run is attached.

Rebuild in order:

```sh
python3 tools/build_browser.py
PYTHONPATH=src python3 -m unittest discover -s tests -q
python3 tools/run_scenarios.py
python3 tools/build_browser.py
PYTHONPATH=src python3 -m unittest discover -s tests -q
python3 tests/browser_ui_smoke.py
```

# Validation, release evidence and limits — v0.3

## v0.3 traffic smoke and regression (2026-10-20)

- RED from v0.2 is captured in `evaluation/TRAFFIC-RED-V03.txt`, after adding new adversarial tests and before modifying the production gate.
- GREEN local Python unit suite: 56/56 tests, including adversarial malformed-nonce rejection with signed receipts, forced nonce-collision preservation, 36 unique traffic signatures and stable replay semantics.
- In-process native Python bench: 18/18 probes. Game oracle bench: 36/36 cases; each case checks allow/deny, reason and attribution. These overlap with unit cases and are synthetic, not independent trials.
- Scenario ledger contains 115 records: 56 unit + 18 gate probes + 36 game + 5 pending external Mitchell Tech arithmetic cases. Each has ID, source, input, expected, observed and execution provenance.
- Freshly extracted release ZIP and SHA-256 manifest verified; single-file HTML embeds the exact source code. UI smoke tests performed at 390px/1280px with a **stubbed Python loader**, including a full 60-round game traversal and ledger filtration. Stub checks are browser wiring only, **not real Pyodide**.

## Reproduction

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 tools/run_scenarios.py
python3 tools/build_browser.py
python3 tests/browser_ui_smoke.py
```

Run `tools/run_scenarios.py` and `tools/build_browser.py` to refresh the trace after changing source; validate the release ZIP from a fresh extraction before publishing. The external calculator cross-checks are not counted as passes unless executed in Mitchell Tech's distinct browser origin. Operator-submitted JSON is not an authenticated cross-origin statement.

## Limitations

No deployed-site/Safari iPad 9 Pyodide execution is claimed. The app downloads Pyodide v0.27.7 at runtime and uses demo local keys and state; these are not production identity assets. Browser mock tests do not execute the Python engine. No multi-jurisdiction policy or independent adversarial security/field validation has been conducted. A forced nonce collision is an engineered regression test, not a measured real-world frequency.

---

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
