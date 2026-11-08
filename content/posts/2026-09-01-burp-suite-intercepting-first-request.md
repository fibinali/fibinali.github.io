---
title: "Burp Suite: Intercepting and Modifying Your First Request"
description: "A hands-on, step-by-step tutorial for setting up Burp Suite Community, configuring your browser proxy, and intercepting and modifying an HTTP request against a lab target."
category: "Ethical Hacking"
tags: [Cybersecurity, BurpSuite, EthicalHacking, WebSecurity]
type: tutorial
---

Burp Suite is the tool you'll open first in almost any web application security assessment. This tutorial gets you from a fresh install to intercepting and modifying a live request, using a safe local lab target throughout.

::: security-note
This tutorial uses OWASP Juice Shop, a deliberately vulnerable application built for practice. Only point Burp Suite at systems you own or are explicitly authorized to test — pointing an intercepting proxy at a site you don't control is unauthorized access in most jurisdictions.
:::

## Prerequisites

- Burp Suite Community Edition ([portswigger.net](https://portswigger.net/burp/communitydownload))
- A local lab target — this tutorial uses [OWASP Juice Shop](https://owasp.org/www-project-juice-shop/) run via Docker
- Firefox or Chrome, used only for this lab session

## Step 1 — Start the lab target

```bash
docker run --rm -p 3000:3000 bkimminich/juice-shop
```

Visit `http://localhost:3000` to confirm it's running before continuing.

## Step 2 — Configure the browser proxy

Burp listens on `127.0.0.1:8080` by default. Point your browser's proxy settings there — in Firefox: **Settings → Network Settings → Manual proxy configuration**, with both HTTP and HTTPS proxy set to `127.0.0.1` port `8080`.

::: tip
Use a separate Firefox profile for security testing (`firefox -P`) so your everyday browsing traffic never routes through the proxy by accident.
:::

## Step 3 — Install Burp's CA certificate

With the proxy active, visit `http://burp` in the configured browser and download the CA certificate. Import it into your browser's certificate store as a trusted authority — otherwise every HTTPS site will show a certificate warning.

## Step 4 — Turn on intercept and capture a request

In Burp, open the **Proxy** tab and make sure **Intercept is on**. Back in the browser, log in to Juice Shop with any test credentials. The login request will pause in Burp, waiting for you to forward, drop or edit it.

```http
POST /rest/user/login HTTP/1.1
Host: localhost:3000
Content-Type: application/json

{"email":"test@example.com","password":"test1234"}
```

## Step 5 — Modify the request

Right-click the intercepted request and choose **Send to Repeater**. Repeater lets you edit and resend a request repeatedly without re-triggering the whole flow — the standard way to probe how an endpoint reacts to different input.

Try changing the `email` field to a value with a single quote:

```json
{"email":"test'@example.com","password":"test1234"}
```

::: example
If the response changes shape — an unhandled server error instead of a clean "invalid credentials" — that's a signal the input isn't being sanitized before it reaches a query, worth investigating further with proper authorization.
:::

## Step 6 — Read the response

Repeater shows the raw response alongside your edited request. Compare status code, headers and body against the original request to see exactly what your change affected.

::: note
Community Edition's Repeater and Proxy are enough for most learning exercises. Automated scanning and the full Intruder attack types are Professional-only features.
:::

## What you've done

You've set up an intercepting proxy, captured live traffic between a browser and a target application, and used Repeater to modify and resend a request — the core workflow behind almost every manual web security assessment. From here, the natural next step is learning to read and interpret the responses systematically, which the next tutorial in this series covers.
