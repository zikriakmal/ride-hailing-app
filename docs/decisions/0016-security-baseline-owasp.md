# 0016: Security baseline: OWASP ASVS L2, API Top 10, MASVS L1, scanners in CI

- **Date:** 2026-11-28
- **Status:** proposed

## Context

The system holds personal data (phones, emails), live and historical locations, and support conversations, and gives staff strong powers. Most of it is built task by task, often by agents. Security can't be a final pass; it has to be part of every task, with checks that run automatically.

## Decision

- Follow **`docs/SECURITY.md`**, which maps our controls to **OWASP ASVS 4.0 Level 2**, the **OWASP API Security Top 10 (2023)**, the **OWASP Top 10 (2025)**, and **OWASP MASVS L1** for the mobile apps.
- Every endpoint task ships **authz matrix tests** (no token / wrong role / other user / suspended / owner) and input-abuse tests; they count toward 100% coverage (ADR 0013).
- **Automated checks in CI** block merges: `gitleaks`, `golangci-lint` with `gosec`, `govulncheck`, `osv-scanner`, Trivy (image + config), CodeQL; Dependabot keeps dependencies current. Exceptions need an entry with an expiry date in `docs/security-exceptions.md`.
- **Privacy by default**: counterpart phone numbers and live locations only during an active ride; masked phones in back-office lists; no personal data in logs.
- **Pre-launch DAST**: OWASP ZAP baseline scan and a checklist review before go-live (task 028).
- The reviewer agent runs the checklist in `docs/SECURITY.md` on every change.

## Alternatives considered

- **ASVS Level 1 only**: lighter, but L1 is aimed at low-risk apps; location data and staff powers justify L2 for the chapters we touch.
- **ASVS Level 3**: for high-value systems (banking, health); far more process than this project can carry.
- **External pentest only**: valuable later, but finds issues after the fact; doesn't stop regressions task to task.
- **Scanners without blocking**: easy to ignore.

## Consequences

- Each task takes a bit longer (authz tests, limits).
- CI is slower by a few minutes; scanner false positives need triage and exceptions.
- Contract change: `RideParty.phone` is `null` outside active rides.
- Some items are deferred to the backlog (2FA for staff, certificate pinning, breached-password checks, account deletion flow).
