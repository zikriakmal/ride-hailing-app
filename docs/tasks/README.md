# Tasks

> Roadmap. Status lives in each task file, not here. `/next-task` picks the lowest-numbered `todo` whose dependencies are `done`.
>
> Infra tasks 017–019 only need the scaffolds, so pull them in early with `/next-task 017` (then 018, 019) right after 002. That way CI guards every feature task.

| # | Task | Depends on | PRD flow |
|---|------|------------|----------|
| 001 | [Backend scaffold](001-setup-backend-scaffold.md) | — | foundation |
| 002 | [Mobile scaffold](002-setup-mobile-scaffold.md) | 001 | foundation |
| 003 | [Auth login](003-auth-login.md) | 001, 002 | 1 |
| 004 | [Auth signup](004-auth-signup.md) | 003 | 1 |
| 005 | [Session restore and logout](005-auth-session.md) | 003 | 1 |
| 006 | [Fare estimate](006-ride-fare-estimate.md) | 005 | 2 |
| 007 | [Rider online + location](007-rider-online-location.md) | 005 | 3 |
| 008 | [Realtime connection](008-realtime-connection.md) | 005 | 3, 4 |
| 009 | [Request ride + dispatch](009-ride-request-dispatch.md) | 006, 007, 008 | 2, 3 |
| 010 | [Rider accepts](010-ride-accept.md) | 009 | 4 |
| 011 | [Live rider location](011-ride-live-location.md) | 010 | 4 |
| 012 | [Arrive / start / complete](012-trip-lifecycle.md) | 011 | 5 |
| 013 | [Cancel](013-ride-cancel.md) | 012 | 5 |
| 014 | [Trip history](014-trip-history.md) | 012 | 6 |
| 015 | [Dev simulate rider](015-dev-simulate-rider.md) | 011 | testing aid |
| 016 | [Two-device E2E run](016-e2e-two-device-run.md) | 013, 014, 015, 019 | success criteria |
| 017 | [Backend Docker image + prod compose](017-infra-docker-image.md) | 001 | infra |
| 018 | [CI pipeline](018-infra-ci-pipeline.md) | 001, 002, 017 | infra |
| 019 | [VPS setup + continuous deploy](019-infra-vm-deploy.md) | 017, 018 | infra |
| 020 | [Back office scaffold + staff login](020-backoffice-scaffold-login.md) | 013, 014, 015 | 8 |
| 021 | [Audit log](021-backoffice-audit-log.md) | 020 | 12 |
| 022 | [Staff management](022-backoffice-staff-management.md) | 021 | 8 |
| 023 | [User and rider management](023-backoffice-user-management.md) | 022, 007, 008 | 9 |
| 024 | [Ride assistance](024-backoffice-ride-assistance.md) | 021, 011, 013 | 10 |
| 025 | [Support tickets](025-backoffice-support-tickets.md) | 021 | 7, 11 |
| 026 | [Report a problem in the apps](026-app-report-a-problem.md) | 025, 014 | 7 |
| 027 | [Deploy back office + staff E2E](027-infra-deploy-backoffice.md) | 019, 023, 024, 025, 026 | 8–12 |

```
001 → 002 → 003 ─┬→ 004
                 └→ 005 ─┬→ 006 ─┐
                         ├→ 007 ─┼→ 009 → 010 → 011 ─┬→ 012 ─┬→ 013 ─┐
                         └→ 008 ─┘                   │       └→ 014 ─┼→ 016
                                                     └→ 015 ─────────┘
001 → 017 ─┐
001, 002 ──┴→ 018 → 019 ───────────────────────────────────────────────→ 016

Back office (after the core ride flow):
013, 014, 015 → 020 → 021 ─┬→ 022 → 023 ─────────────┐
                      ├→ 024 (needs 011, 013) ──┼→ 027 (needs 019)
                      └→ 025 → 026 (needs 014) ─┘
```
