# Scope and threat model (v0.1)

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
