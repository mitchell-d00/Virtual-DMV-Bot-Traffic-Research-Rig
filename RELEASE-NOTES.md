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
