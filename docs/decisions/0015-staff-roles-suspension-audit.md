# 0015: Staff roles, immediate suspension, append-only audit log

- **Date:** 2026-11-28
- **Status:** proposed

## Context

Staff can see every user's phone number and ride history, cancel rides, and lock accounts. We need clear permissions, a suspension that works immediately even though JWTs are stateless (ADR 0006), and a trustworthy record of who did what.

## Decision

- **Roles** on `User.role`: `support` and `admin` join `consumer` and `rider`. Signup only accepts `consumer`/`rider`. Staff are created by an admin (`POST /admin/staff`); the very first admin with a server CLI: `docker compose run --rm api create-admin --email … --name …` (password read from stdin, never from flags or env).

| Action | support | admin |
|--------|:-------:|:-----:|
| View users, rides, tickets, audit log | ✓ | ✓ |
| Reply / internal note / assign / resolve tickets | ✓ | ✓ |
| Force-cancel an active ride | ✓ | ✓ |
| Edit user name, phone, vehicle | | ✓ |
| Suspend / unsuspend users | | ✓ |
| Create staff, change staff role, disable staff | | ✓ |

- **Route guards**: `/admin/*` group requires a staff role; admin-only handlers add a second guard. Both tested per endpoint.
- **Immediate suspension**: `users.suspended_at`. The auth middleware loads it on **every** authenticated request (primary-key lookup) and returns `403 ACCOUNT_SUSPENDED`; login checks it too. On suspend, the server also closes the user's WebSockets (`4003`) and sets a rider `offline`. A user with an active ride can't be suspended (`409 USER_HAS_ACTIVE_RIDE`) until staff force-cancel it, so no ride is left half-finished.
- **Staff sessions**: 12 h token expiry (others 7 days). Login is rate-limited at nginx (`5 r/min` per IP on `/api/auth/login`) and in the backend (per email, 10 failures / 15 min → `429 RATE_LIMITED`).
- **Audit log**: `audit.Record(tx, …)` inside the same DB transaction as the action; if it fails, the action rolls back. Reason is required for suspend, unsuspend, profile edits, staff changes, and force-cancel. `before`/`after` hold only changed fields; secrets (password hashes, tokens) are never recorded. A DB trigger rejects `UPDATE`/`DELETE` on `audit_log`. Reads are not audited.
- **Self-protection**: an admin can't change their own role or disable themselves (`409 CANNOT_MODIFY_SELF`), so the last admin can't lock everyone out.

## Alternatives considered

- **Token version / denylist** for suspension: avoids a DB read per request, but adds state that must be checked anyway; one indexed lookup is cheap at our scale.
- **Short tokens only (wait for expiry)**: up to 7 days of access after suspension. Rejected.
- **Fine-grained permissions (RBAC tables)**: flexible, but two fixed roles cover the PRD; revisit if roles multiply.
- **Audit via DB triggers on every table**: catches everything, but loses the "who" (staff id) and "why" (reason) unless passed through session variables; app-level writes are clearer.
- **Separate staff accounts table**: cleaner separation, but duplicates auth; one `users` table with roles keeps one login path.

## Consequences

- Every authenticated request costs one extra indexed query.
- ADR 0006's "no server-side revocation" no longer holds for suspension (it still holds for logout).
- Audit entries grow forever; at demo scale that's fine (backlog: retention/archiving).
- Support can see personal data; staff accounts must be few, named, and reviewed (admin's staff page).
