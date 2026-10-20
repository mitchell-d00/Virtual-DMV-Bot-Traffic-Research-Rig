# v0.6 — traffic ingress, revocation chronology, and type-safety gate

## Source-controlled red/green investigation

Baseline: verified v0.5 release, **before editing engine.py**. Nine new named unit tests were added in `tests/test_input_boundaries_v06.py` and executed against that baseline. The captured output in `evaluation/INPUT-BOUNDARIES-RED-V06.txt` contains **13 failed assertions and 2 exceptions/errors**, spread across the nine test methods and subtests. The counts include intentionally repeated subtests exercising *distinct input values*, not 15 independent vulnerabilities.

### Failure A — unbounded ingress plate IDs

`challenge()` accepted a 50,000-character plate ID and some malformed non-string IDs, placed them into pending-state memory and advanced the request counter. The final gate's v0.5 bound applied only to `decide()`, *after* challenge allocation. v0.6 validates `_named(plate_id)` **before** allocating a nonce. Unknown but syntactically valid plates remain allowed to request a challenge and are denied with a signed host receipt after verification.

### Failure B — bad resource type exception

A list/dictionary passed as the `resource` argument reached a dictionary membership test and caused a raw `TypeError`. The input now receives a bounded `ProtocolError` before any pending-state mutation. Invalid action types are also caught by existing protocol validation.

### Failure C — backdated signed revocation

The v0.5 `revoke()` method appended issuer-signed `revoke` events dated before the original plate issuance, and `audit()` would accept those semantically inconsistent but correctly signed records. v0.6 refuses retroactive revocations **before append** and rejects previously imported signed event chains containing an impossible `revoked_at` earlier than the latest credential's `issued_at`.

### Failure D — Python Boolean as credential revision

The v0.5 validation accepted `revision: true` as integer revision 1 because Python's `bool` is an `int` subclass. v0.6 requires exact integer types for credential revision and validity timestamps. This change is about byte-level schema semantics; it does not make locally exposed issuer keys secure.

## Reproduction and current limits

```sh
PYTHONPATH=src python -m unittest discover -s tests -p 'test_input_boundaries_v06.py' -v
PYTHONPATH=src python tools/run_ingress_matrix.py
PYTHONPATH=src python tools/run_scenarios.py
python tools/build_browser.py
PYTHONPATH=src python -m unittest discover -s tests -v
python tests/browser_ui_smoke.py
```

The unique `INGRESS-*` matrix includes 50 synthetic cases, with a unique structured input tuple for each case, and includes an admitted positive control. A failed challenge request must not advance the sequence or allocate a nonce. A safe unknown plate can obtain a challenge but cannot pass proof/admissibility. Local Python results do not establish remote network enforcement, CDN/Pyodide integrity, or actual iPad Safari behavior. Issuer and owner private keys in exported demo state remain a **non-production** trust model.
