# Affordable Tags ownership transfer

To change a plate's owner, the current owner must sign an intent bound to the exact prior revision and the incoming public key, and the incoming owner must countersign acceptance. The trusted issuer signs the successor credential. The old holder's key cannot satisfy new holder challenges after transfer. Revocation terminates admission but does not erase history.

Registry history records *cryptographic authority transitions*, not proof of real-world property or beneficial ownership. Transfer of any accrued reputation is unimplemented, intentionally: designing reputation transfer without laundering prior harms remains a research problem.

**Source:** `PAPERS/04-Affordable-Tags.txt`.
