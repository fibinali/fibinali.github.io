---
title: "Building a Reproducible Security Lab With Docker Compose"
description: "How I set up VulnLab — an isolated, disposable practice environment with intentionally vulnerable apps, so every exercise starts from a clean, known state."
category: "Projects"
tags: [Cybersecurity, Projects, EthicalHacking]
type: article
---

Practicing web security exercises against a machine you never reset teaches bad habits — you start remembering the answer instead of the method. VulnLab is a small Docker Compose stack that solves that by making every session start from a clean, disposable state.

::: security-note
Everything in this lab runs on an isolated bridge network with no route to the internet or to other machines on your LAN. Never expose intentionally vulnerable applications on a network you don't fully control.
:::

## The stack

```yaml
# docker-compose.yml
services:
  juice-shop:
    image: bkimminich/juice-shop
    ports: ["3000:3000"]
    networks: [labnet]

  dvwa:
    image: vulnerables/web-dvwa
    ports: ["3001:80"]
    networks: [labnet]

  webgoat:
    image: webgoat/webgoat
    ports: ["3002:8080"]
    networks: [labnet]

networks:
  labnet:
    driver: bridge
    internal: true   # no route out of this network
```

The `internal: true` flag is what makes this safe to leave running — the network has no path to the internet, so even a genuinely exploited container can't be used to pivot anywhere.

## Resetting to a known state

```bash
# reset.sh — tear down and recreate everything from scratch
docker compose down -v
docker compose up -d
echo "Lab reset. Targets: :3000 :3001 :3002"
```

Running this between exercises means every attempt starts from identical conditions — useful both for practicing methodically and for writing reproducible write-ups afterward.

## A minimal exercise log

Tracking what you tried and what worked turns a scattered practice session into something you can actually learn from later:

```text
## 2026-09-14 — DVWA, SQL Injection (low)
Target:   http://localhost:3001/vulnerabilities/sqli/
Payload:  ' OR '1'='1
Result:   returned all user rows instead of one
Fix:      parameterized queries (see OWASP Top 10 post, #3)
```

::: tip
Keep this log in the same repository as the Compose file. Months later, `git log` on the log file becomes a timeline of what you practiced and when — genuinely useful when writing up a learning journey.
:::

## Extending it

The current stack covers general web vulnerabilities. Planned additions:

- A deliberately misconfigured API (see the `PayloadLab API` project) for practicing authorization bugs specifically
- A small SIEM-style logging container to practice detection, not just exploitation
- A `Makefile` wrapping the reset script so onboarding is a single `make lab-reset`

The full Compose file and setup instructions are on GitHub — see the [VulnLab project entry](/projects/) for the repository link.
