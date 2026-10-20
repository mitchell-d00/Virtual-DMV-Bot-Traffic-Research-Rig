# Virtual DMV plate lifecycle

A plate's signed claims bind issuer, plate ID, participation class, public owner key, revision and validity range. The holder answers a short-lived signed challenge containing nonce, resource and action. The gate checks the most recent replayed registry state and default-deny host policy. Tamper and replay tests are expected to fail closed.

Operational caveats: demo seeds are exported; simulated time is explicit; issued plates do not authenticate actual organizations; registration is not proof of compliance; signs of fraud depend on trusted issuer keys.

**Source:** `PAPERS/02-Virtual-DMV-Bot-Regeneration.txt`.
