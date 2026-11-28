# 022: Staff management

- **Status:** todo   <!-- todo | in-progress | blocked | done -->
- **Depends on:** 021
- **PRD flow:** 8. Staff log in (accounts); PRD rule "Staff permissions"

## Goal

An admin creates support and admin accounts, changes their role, and disables them from the back office. Every change is audited, and an admin can't lock themselves out.

## Scope

**In:**
- `GET/POST /admin/staff`, `PATCH /admin/staff/{userId}` (admin only)
- Disabling a staff member sets `suspended_at`; their next request gets `403 ACCOUNT_SUSPENDED` (shared suspension check in the auth middleware: implement it here, reused by 023)
- Audit: `staff.created`, `staff.updated` with reason
- Back office `features/staff`: list, create form (RHF + zod, password ≥ 12), change role, disable/enable with reason dialog; hidden for `support`

**Out (don't build here):**
- Password reset or self-service password change (backlog)
- 2FA (backlog)

## API

- `GET /admin/staff`, `POST /admin/staff`, `PATCH /admin/staff/{userId}`

## Acceptance criteria

- [ ] Admin creates a support account; it can log in to the back office; duplicate email → `409 EMAIL_TAKEN`
- [ ] Support calling any staff endpoint → `403 FORBIDDEN`
- [ ] Disabling a staff member makes their existing token fail on the very next request with `403 ACCOUNT_SUSPENDED`, and their login fails too
- [ ] An admin changing their own role or disabling themselves → `409 CANNOT_MODIFY_SELF`
- [ ] Each create/update writes one audit entry with actor, reason, and changed fields
- [ ] Unit tests added for every new/changed function, handler, slice, endpoint, schema, hook, and component
- [ ] Tests cover the cases above and pass; coverage is 100% in every touched codebase (ADR 0013), output pasted in Notes

## Notes

