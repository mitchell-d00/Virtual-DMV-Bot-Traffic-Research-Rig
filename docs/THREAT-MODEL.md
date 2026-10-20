# Scope and threat model (v0.6)

## In-scope tests

- Unknown machine attempting a resource that requires a plate.
- Verifiable but unauthorized class and unapproved downstream use.
- Spoofed holder key, stale plate revision, expired plate, and replayed challenge.
- Wrong actor attempting transfer or renewal, and old actor after transfer.
- Issuer revocation and altered ledger/receipt payloads.
- Malformed IDs, duplicate issuance, unregistered resources and invalid requests.

## Out-of-scope risks; tests must NOT be described as solving them

- Key theft, malicious issuer or host, compromised browser or operator, JavaScript injected into page context.
- State exports that contain DEMO private seeds: no confidentiality, multi-party key custody or hardware root of trust.
- Equivocation, journal truncation and unpublished tails: without an independently trusted checkpoint, any party with key access can replace a history; signature replay does not prove global completeness.
- Non-cooperative bots that never present a plate, network/firewall controls, browser fingerprinting and large-scale scraping.
- Multiple resource owners and enforceable legal authority; ownership and copyright are resolved outside this lab.
- Privacy-preserving accountable pseudonymity and lawful disclosure of operator identities.
- Rate limiting, denial of service, concurrent issuer race handling, multi-device conflict resolution, federation and issuer trust bootstrap.
- Cryptographic security guarantees from variable-time pure-Python Ed25519 code; use a vetted implementation outside a research sandbox.
- Reputation transfer and fake-trust farming; this release transfers signing authority but does not assert portable trust/reputation.
- Behavior after access, model training usage audits, or contracts backed by real enforcement.

## Model architecture

Issuer signs plate + transition events. Owner signs challenge and ownership intent. A local host signs every allow/deny receipt. Host policies are data in the browser/CLI. No remote identity infrastructure exists. Treat its tests as structural, not deployment-ready.

## v0.5 changes and remaining boundaries

- Base64url decoding requires a unique canonical unpadded encoding, so alternate trailing padding-bit spellings of an otherwise identical signature/public key are refused.
- New owner intent (`vdmv.owner-intent.v2`) and new owner acceptance (`vdmv.acceptance.v2`) sign a digest of the exact successor plate payload (including expiry and owner key). Historical v1 intent records remain accepted but do not acquire new protections retroactively.
- Retroactive signed transitions are rejected *before* append; oversized, deep, cyclic, non-finite, non-JSON or non-object challenge envelopes fail closed with small host-signed receipts without consuming valid pending challenges.
- New gate tests include all 168 combinations of four demonstration resources, six roles (five plate classes plus anonymous) and seven actions; synthetic coverage does not establish field enforcement.
- Local browser `localStorage` contains issuer/host and owner demo signing seeds. Anyone running JavaScript in that page context or importing a copied state file effectively controls those keys; no actual multi-party isolation exists. This is a **development research rig**, not a secure credential wallet.
- Canonical JSON here is the Python implementation's internal `json.dumps(sort_keys=True,ensure_ascii=True)` format, **not** an interoperability-standard canonical JSON protocol. Implementations in other languages must agree on exact bytes; further cross-platform tests are mandatory.
- Pyodide loads from an external jsDelivr URL without a cryptographic SRI pin; packaging the source in HTML does **not** guarantee runtime supply-chain integrity. Real CDN/iPad startup and reload tests are required.
- Signed receipts do not prove an action was actually prevented or that downstream use respected conditions. Missing tail, key theft, issuer collusion, and selective denial of service remain out of scope.

## v0.6 ingress and audit chronology

- Bound challenge plate IDs and reject non-JSON identifier types **before pending-state allocation**. A well-formed unregistered plate may receive a challenge, but cannot gain admission simply by naming one.
- Reject malformed resource types with a protocol error, not a raw hashability exception. This is an API validation boundary, **not** a hosted-service request firewall.
- Enforce chronology for issuer revocations both when appended and during signed event-chain replay. A cryptographically valid event can still be semantically invalid.
- Exact integer metadata rejects Boolean/integer confusion in signed credential fields.
- The 50-case ingress matrix is synthetic and distinct by structured input. Real HTTP ingress limits, key secrecy, race conditions and actual Safari/Pyodide startup are **not** tested.
