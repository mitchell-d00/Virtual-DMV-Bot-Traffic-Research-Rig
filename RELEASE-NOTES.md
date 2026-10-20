# Virtual DMV / Bot Traffic — ingress/signed-timeline v0.6 (2026-10-20)

- **RED:** Nine targeted regression methods against v0.5 produced 13 failed assertions and two errors, archived in `evaluation/INPUT-BOUNDARIES-RED-V06.txt`.
- **FIXED:** Validate plate identifier and resource shape *before* challenge allocation. Refuse oversized or malformed plate identifiers without consuming a nonce, but preserve signed denials for valid-shaped unknown plates. Reject retroactive issuer revocation events on creation and on signed-chain replay. Require exact integer types for credential revision and timestamps.
- **TEST:** 95/95 local Python unit tests, 22/22 Python probes, 60/60 Bot Traffic cases, 168/168 signed policy/role/action checks, and 50/50 unique hostile-ingress cases (395 passes; five external calculator cases pending).
- **RELEASE PROCESS:** First ledger run found two expected packaging-test failures because `index.html` and source pins still described the old engine. Regenerated browser sources, reran the complete ledger (395/395 recorded local passes), then rebuilt the final HTML from the green ledger. This mismatch was packaging-order, not an admission bypass.
- **BUILD:** Full 399-entry evidence record retained in `evaluation/SCENARIO-RESULTS.json`; compact single-file HTML embeds a lossless gzip/Base64 copy. The browser requires `DecompressionStream` and separately loads Pyodide. Source-mismatch packaging checks ran RED before regeneration; final builds were checked for equivalent decoded records.
- **BOUNDARY:** Neither this release nor any local test proves secure real-world registration, legal permission enforcement, actual bot use, or live Safari/Pyodide execution. The issuer keys and private seeds remain demo-local and copyable.

# Virtual DMV / Bot Traffic — crypto/safety v0.5 (2026-10-20)

- **RED:** 14 targeted security tests initially produced 24 failures and three errors (one differential crypto control already passed). The red test file had intentionally generated multiple noncanonical signatures, an owner-intent successor mismatch and unsafe malformed traffic; see `evaluation/CRYPTO-RED-V05.txt` for the original run.
- **GREEN:** enforce canonical unpadded base64url for Ed25519 public keys and signatures; bind renew/transfer owner signatures and new-owner acceptance to the exact SHA-256 of the successor credential; reject retroactive transitions before event append; validate/cap hostile traffic envelopes before copying and signing small fail-closed receipts.
- **Verification:** 14/14 new focused crypto checks; eight external-library Ed25519 vector comparisons pass when `cryptography` is installed (development only). Added 168 distinct signed policy/role/action request tuples with independently declared expected permit/reason/attribution; all pass locally.
- Two additional adversarial identifier tests caught accepted Cyrillic look-alike owner and plate labels; the ID syntax is now ASCII-only (recorded red→green).
- A separate late regression also found and corrected a poisoned pending-challenge `KeyError` (two integrity tests; archived red evidence).
- Historical `vdmv.owner-intent.v1` and `vdmv.acceptance.v1` events remain readable under a documented weaker consent binding; *new* transitions use v2. Trust in local issuer/host seed custody, real legal permissions, CDN loading and live iPad/browser runtime are not proven.
- **Final v0.5 release gate:** 84/84 local unit tests, 22/22 Python probes, 60/60 isolated game oracles, 168/168 role/resource/action policy checks; five external calculator checks remain pending. Browser stub UI smoke passes at 390px and 1280px.
- v0.4 and v0.3 remain included below as traceable local development milestones; this v0.5 snapshot is intended to supersede the previously published v0.2 on GitHub after a verified push.

# Virtual DMV / Bot Traffic — prototype v0.4 (2026-10-20)

**Traffic-only red→green iteration.** The v0.3 packaged release was used as the local test baseline; this v0.4 release incorporates both v0.3 and v0.4 changes over the previously published v0.2 GitHub code.

- Reproduced unhandled **non-object challenge envelope** exceptions and **unbounded/stale pending traffic queue** against v0.3. Pre-fix test output archived under `evaluation/TRAFFIC-RED-V04.txt`.
- Added six versioned `tests/test_traffic_v04.py` regression methods. Corrected signed denials, a 128-live-challenge per-registry limit, expired request cleanup, and capacity restoration after request consumption.
- Expanded playable Bot Traffic to **60 unique cases**; retained `GAME-001..036`, added `GAME-037..060`. Expanded Python gate probes from 18 to 22.
- Full release evidence: **62 Python tests + 22 Python probes + 60 game scripts locally passing; 5 distinct external calculator cases pending** (149 unique scenario IDs, 144 recorded passes).
- Each case has a distinct ID, scope, input, expected outcome, observed outcome, status and origin. Prior release records remain in the documentation; unknown bot behavior and real-world adoption are not demonstrated.
- Mobile and desktop UI smoke performed with an explicitly stubbed Python interpreter. An initial mock-fixture 18/22 mismatch was corrected and rerun at both widths; not claimed as deployed Pyodide or Safari hardware validation.
- Original four papers byte-for-byte preserved. Rebuild hashes and fresh extraction checks accompany the release.

## Previous release notes

# Virtual DMV / Bot Traffic — prototype v0.3 (2026-10-20)

**Traffic-first red→green release.** The four original papers are unchanged.

- Reproduced malformed challenge nonce crashes and forced duplicate nonce overwrites on the v0.2 engine. Captured pre-fix failures in `evaluation/TRAFFIC-RED-V03.txt`.
- Fixed signed denial receipts for malformed nonces without consuming real pending requests; bounded nonce uniqueness check on issuance.
- Expanded from 10 to 36 individually documented, uniquely identified Bot Traffic game scenarios; baseline `GAME-001..010` is preserved. Scenarios include revocation, transfer, renewal, expiry, forged/stale plates, proof, replay, privacy and locally declared permissions.
- Expanded from 12 to 18 browser-rerunnable Python adversarial probes; the game asserts admit/deny, reason and attribution.
- Added semantic repeated-run stability regression and reset of exported shift history; expanded desktop/mobile stub-browser game and evidence ledger smoke.
- 115 distinct scenario records: 56 local Python tests + 18 Python probes + 36 game oracles + 5 external calculator checks pending. Different banks overlap in behavior. No empirical adoption/production claims.
- Python engine, HTML, release hashes and freshly extracted ZIP rebuilt for this release. Browser mock checks **do not** prove live Pyodide/iPad execution.

## Earlier version history

# Virtual DMV / Bot Traffic — prototype v0.2 (2026-10-20)

## Reproduced v0.1 failure and correction

- **RED:** mutable shared DMV registry changed the result of the same scripted game case after user revocation. Game traffic added receipts to the user's working registry; invalid negative/overflow case indices wrapped through modulus.
- **GREEN:** three named tests failed *before* the fix; game logic now uses isolated deterministic fixtures, leaves the DMV workspace unchanged, rejects invalid indices, and checks case oracle expectations. See [the actual reproduction and validation](evaluation/REGRESSION-HISTORY.md).

## Release features

- **51/51 local Python unit tests passed**, **12/12 synthetic Python browser-capable probes**, **10/10 local Bot Traffic replay oracles**.
- **78 visible scenario records**, individually indexed: 51 local Python unit cases, 12 Python probes, 10 playable game cases, five externally pending Mitchell Tech arithmetic questions.
- Full recorded source labels, inputs, expected/observed outcomes, statuses, unique test IDs, a browsable search/filter UI, and downloadable JSON result evidence.
- Mitchell Tech V120.2 numerical cross-check workflow and import: five deduplicated expressions, copy JavaScript batch snippet into calculator's own tab, paste results back. Checks are marked PENDING until run; imported claims are not independently attested.
- Source and original research papers preserved; original-paper SHA-256 unchanged.
- Single-file HTML embeds exact Python source and scenario snapshot, uses Pyodide v0.27.7 via CDN at runtime. Python and browser JavaScript are readable in repository.

## Validation boundaries

Browser DOM tests ran with a *mock Python interpreter* at mobile and desktop viewports; live Pyodide startup and Safari/iPad hardware are not claimed. Local Python/Ed25519 and synthetic scenarios are not production security or observed field behavior. Scenario banks overlap in coverage and are not independent evidence for 73 novel claims.
