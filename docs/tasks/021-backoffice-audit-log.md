# 021: Audit log

- **Status:** todo   <!-- todo | in-progress | blocked | done -->
- **Depends on:** 020
- **PRD flow:** 12. Audit log

## Goal

There is a tamper-resistant record of staff actions, written in the same transaction as each action, and staff can search it in the back office. Later tasks call one function to record every staff write.

## Scope

**In:**
- Migration: `audit_log` table + indexes + trigger rejecting `UPDATE`/`DELETE` (`docs/ARCHITECTURE.md`)
- `internal/audit`: `Record(tx, Entry)`: requires actor (or nil for CLI), action, target, reason where required; strips secret fields from `before`/`after`; diff helper that keeps only changed fields
- `create-admin` CLI now records `staff.created` with `actor: null`
- `GET /admin/audit-log` with filters + cursor pagination
- Back office `features/audit`: table (time, actor, action, target link, reason), filters, before/after diff view

**Out (don't build here):**
- The actions themselves (022–025)
- Retention/archiving (backlog)

## API

- `GET /admin/audit-log`

## Acceptance criteria

- [ ] `Record` inside a transaction that rolls back leaves no audit row; a failing `Record` makes the caller's transaction fail
- [ ] `UPDATE audit_log …` and `DELETE FROM audit_log …` raise errors at the DB level (test with raw SQL)
- [ ] `before`/`after` never contain `password_hash` or tokens, even if passed in
- [ ] Filters (`actorId`, `targetType`+`targetId`, `action`) and pagination work; consumer/rider → `403`
- [ ] Back office: entries render with links to the target; filters update the URL query (shareable)
- [ ] Security (docs/SECURITY.md): authz matrix tests for every endpoint touched (no token → `401`, wrong role → `403`, other user's resource → `404`, suspended → `403`, owner → success); input-abuse tests (oversized body, extra fields ignored, boundary values); no sensitive fields in raw responses
- [ ] Unit tests added for every new/changed function, handler, slice, endpoint, schema, hook, and component
- [ ] Tests cover the cases above and pass; coverage is 100% in every touched codebase (ADR 0013), output pasted in Notes

## Notes

