# Adversarial replication / kill tests

## Claim C1: identity does not imply resource permission

**Intervention:** Issue a correctly signed crawler plate. Try training on `licensed-training-data`. **Expected:** `POLICY_DENY`. **Kill:** code grants solely because identity verifies.

## Claim C2: ownership can transfer without silent duplication

**Intervention:** Issue research plate to Alice; transfer by her signed intent to Bob; sign subsequent challenge first with Alice's key, then Bob's. **Expected:** old signature rejected; new signature accepted if host policy permits. **Kill:** Alice still admitted after transfer.

## Claim C3: ledger manipulation is detectable under declared keys

**Intervention:** Change one field in signed journal or host receipt without updating signatures. **Expected:** verifier rejects it. **Kill:** mutated record passes.

## Claim C4: unknown traffic creates an incentive only under exclusion

**Intervention:** Sweep adoption under a host that denies anonymous research crawling, then repeat under a fully open host policy. Measure access, utility, credential overhead, error rates. **Expected:** registration advantage disappears if everyone is admitted anonymously and registration costs remain positive. **Kill:** instrument reports universal registration benefit regardless of resources' terms. The present toy model only implements the first sweep; the second is next work.

## Claim C5: actual operators have incentives

Recruit consenting resource owners and participating agents. Compare voluntary registration under real admission advantages with anonymous baseline under identical resources; measure costs, false denials, interoperability, and privacy burden. No field study has been performed in this release. A favorable synthetic score is not evidence for C5.

## Negative controls

- Legitimate unknown traffic to deliberately open resource should be admitted.
- Bad actor with valid credentials but unauthorized purpose should still be denied.
- Signed identity that has expired should not remain active.
- A proxy with the correct public ID but no secret key should not authenticate.
- Old owner's credential must not survive replacement as current.
- Denial after a malformed challenge cannot let the same nonce be used again.

## Reporting

Record exact source pins, hardware/browser/Python version, scenario definitions, sampling protocol, synthetic-versus-live provenance, all failures, and every aborted/modified pre-registration. External studies need independent review of legal and privacy assumptions.
