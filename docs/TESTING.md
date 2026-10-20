# Validation and replication status

## Verified in this generated ZIP environment

- `PYTHONPATH=src python3 -m unittest discover -s tests -v` — 40 unit tests passing in the build environment.
- `virtual_dmv.engine.run_bench()` — 12 author-constructed gate probes passing.
- Ed25519 SHA-512 implementation checked against the RFC 8032 empty-message reference vector.
- Browser page generator embeds the same Python source bytes and creates `docs/ENGINE-SOURCE-PINS.json`.
- JavaScript browser client syntax checked with Node.js.

## Not independently verified

- Pyodide bootstrap on actual iPad 9 hardware, Safari or GitHub Pages deployment.
- HTML behavior in a fully loaded real Pyodide browser runtime in the build environment. External runtime downloads are unavailable here.
- Persistent private state across Safari private-mode or iCloud handoff.
- True production key-management security, a federated trust network, or any real resource owner.
- Predictions in the four papers. The economic model has assumed payoffs and host policies.

## Next investigations

1. Host `index.html` under HTTPS, wait for `Python engine ready` and run 12/12 probes. Record browser OS/version, runtime URL and snapshot hash.
2. Run `python3 -m unittest discover ...` from extracted ZIP, not an unrelated checkout.
3. Independently reproduce issuer signature vector in a vetted Ed25519 library; verify cross-language interchange and reject malformed points.
4. Inject invalid certificate versions, challenge races, silent journal tails and rotating issuer keys. Document new kill tests.
5. Compare same host's anonymized traffic with and without voluntary registration; report consent, registration cost, false denial and false acceptance.
6. Add external signed ledger checkpoints and transparency logs before any real federation tests.
7. If a researcher investigates real devices, do not use user data or live production identities until governance/privacy reviews are in place.
