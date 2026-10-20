# Security and cryptographic regression report — v0.5

## Scope

Synthetic local research reference. All signer seeds are locally available in browser state, Ed25519 is pure-Python and not timing hardened, and no production identity trust or legal enforcement is claimed.

## Actual RED bugs and fixes

| Item | Pre-fix | v0.5 fix | Falsifier |
| --- | --- | --- | --- |
| CRYPTO-001: noncanonical public key/signature base64url | Multiple spellings of identical bytes verified | Decode only if roundtrip encoding is identical | `test_noncanonical_signature_base64_is_rejected`, `test_noncanonical_public_key_is_rejected` |
| CRYPTO-002: owner consent not bound to exact expiry | Issuer could re-sign a modified successor with old owner intent | Outgoing intent v2 signs SHA-256 of successor payload | `test_owner_*_intent_rejects_issuer_only_expiry_change` |
| CRYPTO-003: new holder consent not bound to successor | Acceptance signed role/plate target but not all successor fields | Acceptance v2 signs same successor SHA-256 | `test_transfer_old_and_new_owners_sign_exact_successor` |
| CRYPTO-004: retroactive event appended despite audit failure | Transfer/renew with time before issuance modified signed journal before subsequent audit error | Reject invalid successor time **before** signed append | `test_retroactive_renewal_fails_before_append`, `test_retroactive_transfer_fails_before_append` |
| SAFETY-005: malformed, recursive and oversized traffic | Non-JSON, NaN, cyclic and very large packets could crash signing or inflate receipts | Validate bounded JSON envelope first; create small fail-closed receipt | `test_malformed_json_numbers_fail_closed_with_receipt`, `test_recursive_and_unserializable_challenges_fail_closed`, `test_oversize_packet_is_rejected_without_echoing_untrusted_body` |

## Independent cryptographic cross-check

The optional test compares canonical JSON message signatures and public keys from this educational implementation against `cryptography` Ed25519 on eight deterministic seeds. The independent package is used solely in development. Equality on these vectors does not make the pure-Python implementation constant-time or audited.

## Structured policy/traffic matrix

`tools/run_security_matrix.py` exercises four resources × six identities/classes × seven actions, 168 uniquely identified local requests. Each checks signed receipt presence plus precise decision and attribution against host policy. `evaluation/SCENARIO-RESULTS.json` records every vector, expected answer and observed answer. The scenario ledger browser view includes a **Policy matrix** filter. This is controlled specification conformance, not observed external bots or economic claims.

## Known residual risks

Historical signed owner intents v1 stay compatible but lack successor-bound consent; production migration would need independent trust checks. Browser exports include all demo signing seeds, a compromised page or issuer can impersonate all roles, unsigned host policy data may change locally, event history can be truncated without independent checkpoints, and an unknown agent can decline to use the protocol entirely. CDN runtime is not hash-pinned. See `docs/THREAT-MODEL.md`.

## Late v0.5 red→green: poisoned pending challenge

A malformed stored challenge matching a submitted minimal envelope could raise `KeyError` while retrieving `issued_at`/`expires_at`; see `evaluation/PENDING-RED-V05.txt`. The gate now checks the record type and integer timestamp fields before comparison, consumes the poisoned entry, and signs a denial receipt. Test: `tests/test_pending_integrity_v05.py`. This is a **local imported-state resilience** fix, not network authentication.

## Identifier homograph regression

Python Unicode `.isalnum()` admitted Cyrillic or otherwise visually confusable characters in plate and owner IDs. Both new tests failed before the correction. The v0.5 engine accepts only ASCII letters, ASCII digits, `-`, `_`, and `.` in these identifiers (1–72 characters), avoiding this particular class of look-alike labels. See `evaluation/IDENTIFIER-RED-V05.txt` and `tests/test_identifier_v05.py`. This does not solve every human naming ambiguity.
