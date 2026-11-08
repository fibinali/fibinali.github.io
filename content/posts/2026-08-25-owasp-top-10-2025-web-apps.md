---
title: "The OWASP Top 10, Explained for Working Developers"
description: "A practical tour of the ten most common web application vulnerability classes, what each one actually looks like in code, and the concrete fix for every one of them."
category: "Web Security"
tags: [Cybersecurity, WebSecurity, OWASP, EthicalHacking]
featured: true
type: article
---

The OWASP Top 10 gets cited constantly and read carefully rarely. This is a working developer's tour: what each category actually looks like in real code, and the specific fix — not just the category name.

::: security-note
Every example below is deliberately vulnerable code for illustration. Only run security tests against systems you own or have explicit written permission to test.
:::

## 1. Broken access control

The most common finding in real audits. A user can view or modify data that isn't theirs because the server trusts a client-supplied identifier without checking ownership.

```python
# vulnerable — trusts the client-supplied id
@app.get("/invoices/{invoice_id}")
def get_invoice(invoice_id: int, user: User = Depends(current_user)):
    return db.query(Invoice).get(invoice_id)
```

```python
# fixed — scoped to the authenticated user
@app.get("/invoices/{invoice_id}")
def get_invoice(invoice_id: int, user: User = Depends(current_user)):
    invoice = db.query(Invoice).filter_by(id=invoice_id, owner_id=user.id).first()
    if invoice is None:
        raise HTTPException(404)
    return invoice
```

## 2. Cryptographic failures

Storing passwords with fast hashes, rolling custom encryption, or sending secrets over plain HTTP all fall here. The fix is almost always "use the standard library, not your own":

::: mitigation
Use `bcrypt`, `scrypt` or `argon2` for password storage — never MD5, SHA-1, or unsalted SHA-256. For data in transit, enforce HTTPS with HSTS. For data at rest, use an established library rather than hand-rolled AES.
:::

## 3. Injection

SQL injection is the classic case, but the same pattern applies to shell commands, LDAP queries and NoSQL filters — untrusted input reaching an interpreter without escaping.

```sql
-- vulnerable: string concatenation
SELECT * FROM users WHERE email = '" + user_input + "'
```

```python
# fixed: parameterized query — the driver handles escaping
cursor.execute("SELECT * FROM users WHERE email = %s", (user_input,))
```

::: vulnerability
`' OR '1'='1` as the input turns the query above into `WHERE email = '' OR '1'='1'`, which matches every row. This is the single most-tested payload in any web security course for a reason — it works against anything using string concatenation.
:::

## 4. Insecure design

Not a single bug but a missing control — a password-reset flow with no rate limit, or a checkout process that trusts a client-side price field. This category is caught by threat modeling, not a scanner.

## 5. Security misconfiguration

Default credentials left in place, verbose error pages in production, directory listing enabled, unnecessary services exposed. Usually invisible until someone runs a basic scan.

```bash
# a five-minute check worth running against your own staging environment
nmap -sV --top-ports 100 staging.example.com
```

## 6. Vulnerable and outdated components

Using a dependency with a known CVE. Automate this rather than tracking it by hand:

::: command
`pip install pip-audit && pip-audit`
`npm audit --audit-level=high`
:::

## 7. Identification and authentication failures

Missing multi-factor authentication, session tokens that don't expire, predictable session identifiers. Session fixation — where an attacker sets a known session ID before login and reuses it after — is a common finding here.

## 8. Software and data integrity failures

Trusting a CI/CD pipeline, plugin, or auto-update mechanism without verifying its integrity. The Codecov and SolarWinds incidents both trace back to this category — a trusted supply-chain link that wasn't actually verified.

## 9. Security logging and monitoring failures

Not a vulnerability that gets exploited directly, but the reason breaches go undetected for months. If a login endpoint doesn't log failed attempts, credential-stuffing attacks are invisible until the damage is done.

## 10. Server-side request forgery (SSRF)

The server fetches a URL on the caller's behalf — an image proxy, a webhook validator, a PDF renderer — and the caller can point it at internal infrastructure.

```python
# vulnerable — fetches whatever URL the client provides
@app.post("/fetch-preview")
def fetch_preview(url: str):
    return requests.get(url).content
```

::: important
An attacker sets `url=http://169.254.169.254/latest/meta-data/` to reach a cloud provider's internal metadata endpoint and potentially extract instance credentials. Restrict outbound requests to an allow-list of domains and block requests to private IP ranges.
:::

## A short checklist

| Category | One-line fix |
|---|---|
| Broken access control | Always scope queries to the authenticated user |
| Cryptographic failures | Use vetted libraries, never hand-rolled crypto |
| Injection | Parameterized queries, always |
| Insecure design | Threat-model before you build |
| Misconfiguration | Automate config checks in CI |
| Vulnerable components | Run `pip-audit` / `npm audit` regularly |
| Auth failures | MFA, short-lived sessions, no fixation |
| Integrity failures | Verify signatures on dependencies and updates |
| Logging failures | Log auth events, alert on anomalies |
| SSRF | Allow-list outbound destinations |

None of these fixes are exotic. The Top 10 keeps reappearing not because the fixes are hard, but because they're easy to skip under deadline pressure.
