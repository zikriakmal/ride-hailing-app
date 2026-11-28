# 028: Pre-launch security review and DAST

- **Status:** todo   <!-- todo | in-progress | blocked | done -->
- **Depends on:** 016, 027
- **PRD flow:** all (security baseline, ADR 0016)

## Goal

Before real users, we have evidence the deployed system meets `docs/SECURITY.md`: an automated scan, a walk through the checklists, and every finding fixed or recorded as an accepted exception.

## Scope

**In:**
- OWASP ZAP **baseline** scan (passive) against `https://api.<domain>` (with the OpenAPI spec imported) and `https://admin.<domain>`; then an **API scan** against a test account on production data that's safe to touch, or a local prod-like stack
- Walk the OWASP API Top 10 and Top 10 tables in `docs/SECURITY.md`: for each row, link the test or config that proves it (fill a "Verified by" column with file paths)
- ASVS L2 spot-check for V2 (auth), V3 (session), V4 (access control), V5 (validation), V7 (logging), V8 (data protection), V9 (communications), V13 (API); record gaps
- MASVS L1 check on release builds of both apps: secure store, no cleartext, no secrets in the bundle (`apktool`/`strings` on the APK), permissions
- Manual BOLA/BFLA tries with two real accounts on production (another user's ride/ticket ids, consumer calling `/admin/*`, support calling admin-only routes)
- Findings: fix via `fix(security)`/`hotfix(...)` tasks, or record in `docs/security-exceptions.md` with owner and expiry

**Out (don't build here):**
- External paid pentest, bug bounty (backlog)

## API

- none

## Acceptance criteria

- [ ] ZAP baseline + API scan reports attached (Notes or artifacts) with no unaddressed High/Medium alerts
- [ ] Every row in the `docs/SECURITY.md` OWASP tables has a "verified by" link
- [ ] ASVS L2 spot-check results recorded; each gap is a backlog item or a task
- [ ] Release APK/IPA inspected: no tokens or secrets in the bundle, cleartext blocked, only needed permissions
- [ ] Manual BOLA/BFLA attempts all fail with `404`/`403`
- [ ] Incident-response steps rehearsed once: disable a staff account and rotate `JWT_SECRET` on production (everyone logged out, apps recover)

## Notes

