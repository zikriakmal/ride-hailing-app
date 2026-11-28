# 023: User and rider management

- **Status:** todo   <!-- todo | in-progress | blocked | done -->
- **Depends on:** 022, 007, 008
- **PRD flow:** 9. User and rider management

## Goal

Staff search consumers and riders and open a full profile. Admins edit profiles and suspend or unsuspend accounts, with immediate effect in the apps.

## Scope

**In:**
- `GET /admin/users` (search `q` on name/email/phone/plate, role/status filters, pagination) + search indexes migration
- `GET /admin/users/{userId}` with stats and `activeRideId`
- `PATCH /admin/users/{userId}` (admin; reason required; `vehicle` only for riders) → audit `user.updated`
- `POST /admin/users/{userId}/suspend` / `unsuspend` (admin) → audit; suspend closes WebSockets (`4003`), sets a rider `offline`, refuses with an active ride (`409 USER_HAS_ACTIVE_RIDE`)
- Consumer and Rider apps: on `403 ACCOUNT_SUSPENDED` or close code `4003` → log out and show "Your account is suspended. Contact support."
- Back office `features/users`: search page (debounced, URL query), profile page (details, vehicle, stats, ride history via `GET /admin/rides?userId=`, tickets, audit history), edit form, suspend/unsuspend dialog with reason; edit/suspend hidden for support

**Out (don't build here):**
- Deleting accounts or exporting user data (backlog)

## API

- `GET /admin/users`, `GET /admin/users/{userId}`, `PATCH /admin/users/{userId}`
- `POST /admin/users/{userId}/suspend`, `POST /admin/users/{userId}/unsuspend`

## Acceptance criteria

- [ ] Search finds a user by partial name, email, phone, or plate; staff accounts never appear in results
- [ ] Suspending a consumer: their app is logged out within 5 s (socket `4003`), their token gets `403 ACCOUNT_SUSPENDED`, login is refused; unsuspend restores login
- [ ] Suspending an online rider sets them `offline` and they stop receiving offers
- [ ] Suspend with an active ride → `409 USER_HAS_ACTIVE_RIDE`; suspend twice → `409 INVALID_TRANSITION`
- [ ] Support calling edit/suspend → `403`; missing reason → `400`; each admin action writes one audit entry with before/after
- [ ] Security (docs/SECURITY.md): authz matrix tests for every endpoint touched (no token → `401`, wrong role → `403`, other user's resource → `404`, suspended → `403`, owner → success); input-abuse tests (oversized body, extra fields ignored, boundary values); no sensitive fields in raw responses
- [ ] Unit tests added for every new/changed function, handler, slice, endpoint, schema, hook, and component
- [ ] Tests cover the cases above and pass; coverage is 100% in every touched codebase (ADR 0013), output pasted in Notes

## Notes

