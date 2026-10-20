# Admissibility is a host relationship, not a model capability

Implementation rule: a particular issuer-verified plate, on a particular resource, requesting a particular action, is subjected to that resource's declared policy. "Known" is not the same as "allowed"; unknown traffic need not be denied on explicitly open resources.

Host policy is separate from issuer authority. No successful `request()` touches the outside internet or changes any real-world service permissions. Policy changes affect subsequent requests rather than mutating previously signed host receipts.

**Source:** `PAPERS/01-Machine-Consumption-Governance.txt`.
