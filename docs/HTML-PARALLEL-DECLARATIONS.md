# HTML-parallel declarations: illustration, not an adopted web standard

**Purpose:** Translate the Virtual DMV paper's permission handshake into web-adjacent, independently inspectable declarations. No meta tag or example header alone authenticates a crawler or grants a legal right. Hosts still need a real cryptographic gate in their server infrastructure.

## Suggested page-level metadata, draft only

```html
<meta name="machine-participation-policy" content="/.well-known/machine-participation.json">
<meta name="machine-participation-default" content="deny">
```

These names are **proposals**, not standardized browser behavior. They work only if a participating parser chooses to read and honor them.

## Suggested header, draft only

```http
Machine-Participation-Policy: /.well-known/machine-participation.json
```

Browsers and bot crawlers are not automatically obligated to honor it. The file under `SPECS/.well-known-bot-participation.example.json` is an example of proposed structured policy, not an approved schema from a standards body.

## Existing robots.txt

`robots.txt` has its own established scope and semantics; it does not implement identity, signature verification, permission to train on material, consent to transfer credentials, or cryptographically authenticated host policy. A Virtual DMV gateway would sit at the *resource admission* boundary in addition to declarative hints.

## Operating principle

Host policy is authoritative only within existing law and effective host control. Consumer identifiers are assertions until tied to public-key possession, issuer trust, and freshness. The experimental Python gate does these checks on invented demo resources; it does not intercept network traffic.
