# 0003: PostgreSQL with GORM, migrations with goose

- **Date:** 2026-11-28
- **Status:** proposed

## Context

We store users, riders, and rides, and need a race-free "first rider to accept wins" plus a "riders within 3 km" lookup. Data volume is tiny (a handful of riders). The backend is Go + Gin (ADR 0002).

## Decision

PostgreSQL, accessed through **GORM**. Locally and in CI it's a `postgres:16` container; in production it's the **existing Postgres server on the VPS** (ADR 0011), version 14+, with a dedicated `ride` database and role. Accessed (`gorm.io/gorm` + `gorm.io/driver/postgres`). Models live in `backend/internal/model/`.

- **Migrations** are versioned SQL files run by `goose` from `backend/migrations/`. GORM `AutoMigrate` is **not** used: it never drops or renames, and silent schema changes are hard to review. A test checks that the GORM models match the migrated schema.
- **First accept wins**: `db.Model(&Ride{}).Where("id = ? AND status = ?", id, "requested").Updates(...)`, then check `RowsAffected == 1`. Multi-row changes (ride + rider status) run in `db.Transaction`.
- **3 km lookup**: haversine in a `Where` clause over riders with `status = 'online'` and a fresh location.
- Repositories take `*gorm.DB` so tests can pass a transaction.

## Alternatives considered

- **sqlc + pgx**: type-safe hand-written SQL, but more boilerplate per query and less familiar than GORM.
- **GORM `AutoMigrate`**: zero migration files, but no history, no down migrations, no review of DDL.
- **PostgreSQL + PostGIS**: correct tool for geo queries at scale; overkill for a few riders. Parked in backlog.

## Consequences

- Less query code; simple CRUD is one line.
- Must watch for GORM pitfalls: zero values ignored by `Updates(struct)` (use `map` or `Select`), forgetting `RowsAffected` checks, N+1 with `Preload`. The reviewer agent should check these.
- Schema lives in two places (SQL migrations + GORM models); the model-vs-schema test keeps them aligned.
- Need Docker to run locally. In production the DB server is shared, so migrations must stay inside the `ride` database (no extensions or server-level settings without asking).
