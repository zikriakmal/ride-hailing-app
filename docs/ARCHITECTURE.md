# Architecture

> Stack, data model, folder structure. Update this file in the same change that alters any of them.

## Terminology

- **Consumer**: the passenger. Uses the **Consumer app**. API role `consumer`.
- **Rider**: the motorbike driver (Gojek/Grab naming). Uses the **Rider app**. API role `rider`.
- **Ride**: one trip from request to completion. Not to be confused with *rider*.
- **Staff**: back-office users with role `support` or `admin`. Use the **Back office** web app at `admin.<domain>`.
- **Ticket**: a problem report from a consumer or rider, handled by staff.

## Stack

All choices are **proposed** until their ADR is set to `accepted`.

| Layer | Choice | ADR |
|-------|--------|-----|
| Mobile | React Native + Expo (TypeScript), expo-router | [0001](decisions/0001-mobile-expo-react-native.md) |
| Mobile state + HTTP | Redux Toolkit + RTK Query over axios (`axiosBaseQuery` unwraps the envelope) | [0007](decisions/0007-mobile-state-rtk-query-axios.md) |
| Mobile forms | React Hook Form + zod (`@hookform/resolvers/zod`) | [0008](decisions/0008-mobile-forms-rhf-zod.md) |
| Mobile structure | Feature folders + atomic UI (atoms → molecules → organisms → templates → pages) | [0009](decisions/0009-mobile-structure-features-atomic.md) |
| Back office | React + Vite + TypeScript web app in the same workspace, reusing `@ride/core`; react-router, CSS Modules, react-leaflet (OSM tiles); polling, no WebSocket | [0014](decisions/0014-backoffice-web-app.md) |
| Staff roles & audit | `support` / `admin` roles, immediate suspension, append-only audit log | [0015](decisions/0015-staff-roles-suspension-audit.md) |
| Mobile apps | Two Expo apps (Consumer, Rider) + shared packages `@ride/ui`, `@ride/core`, `@ride/features` in a pnpm workspace | [0010](decisions/0010-two-apps-pnpm-monorepo.md) |
| Backend | Go 1.23 + Gin, `oapi-codegen` (gin strict server) + OpenAPI request validator | [0002](decisions/0002-backend-go.md) |
| Database | PostgreSQL (16 locally/CI; existing server ≥ 14 on the VPS) via GORM, SQL migrations with `goose`; local DB in Docker Compose | [0003](decisions/0003-database-postgres-gorm.md) |
| Realtime (rider location, ride status) | Plain WebSocket (`coder/websocket`), server → client pushes only | [0004](decisions/0004-realtime-websocket-push-only.md) |
| Maps / geocoding | react-native-maps; device geocoder via expo-location; haversine distance | [0005](decisions/0005-maps-device-geocoding-haversine.md) |
| Auth | Email + password (bcrypt), JWT access token (7 days, no refresh) | [0006](decisions/0006-auth-jwt-access-token.md) |
| Hosting | Shipped with Docker Compose (`deploy/docker-compose.prod.yml`) to the existing VPS: host nginx (certbot TLS) → api container (host network, `127.0.0.1:3000`) → existing host Postgres `127.0.0.1:5432` (own `ride` DB + role); daily encrypted `pg_dump` kept on VPS storage. Details in [`docs/INFRA.md`](INFRA.md) | [0011](decisions/0011-hosting-single-vm-docker.md) |
| CI/CD | GitHub Actions: lint + test on PRs; on `main` build the Docker image, push to GHCR, deploy over SSH, smoke test | [0012](decisions/0012-ci-cd-github-actions-ghcr.md) |
| API types | Generated from `docs/api/openapi.yaml`: `oapi-codegen` (Go), `openapi-typescript` (mobile) | [0002](decisions/0002-backend-go.md) |

## System overview

```
┌──────────────┐  REST (all writes + reads)   ┌──────────────┐     ┌────────────┐
│ Consumer app │ ───────────────────────────> │              │ ──> │ PostgreSQL │
│ (passenger)  │ <─── WebSocket pushes ────── │  Backend API │     └────────────┘
└──────────────┘                              │  (Go, REST + │
┌──────────────┐  REST (+ location every 3s)  │  /ws hub)    │
│  Rider app   │ ───────────────────────────> │              │
│ (driver)     │ <─── WebSocket pushes ────── │              │
└──────────────┘                              └──────────────┘
      │ device geocoder / GPS (expo-location), map tiles (react-native-maps)
```

Rule of thumb: **clients write over REST, the server pushes over WebSocket.** Every state change goes through a REST endpoint (testable against the OpenAPI spec); the socket only tells the other party something changed. Message shapes are in [`docs/api/realtime.md`](api/realtime.md).

## Ride lifecycle

```
             accept (rider)       arrive (rider)      start (rider)        complete (rider)
requested ─────────────────> accepted ─────────> arrived ─────────> in_progress ──────────> completed
    │                           │                   │
    │ 60 s, no accept           │ cancel            │ cancel
    ▼                           │ (consumer         │ (consumer only)
 expired                        │  or rider)        │
                                ▼                   ▼
    ▲ cancel (consumer) ────> cancelled <───────────┘
```

| From | To | Who | Endpoint |
|------|----|-----|----------|
| — | `requested` | consumer | `POST /rides` |
| `requested` | `accepted` | rider (first wins) | `POST /rides/{id}/accept` |
| `requested` | `expired` | server, 60 s after creation | — |
| `requested` | `cancelled` | consumer | `POST /rides/{id}/cancel` |
| `accepted` | `arrived` | assigned rider | `POST /rides/{id}/arrive` |
| `accepted` | `cancelled` | consumer or assigned rider | `POST /rides/{id}/cancel` |
| `arrived` | `in_progress` | assigned rider | `POST /rides/{id}/start` |
| `arrived` | `cancelled` | consumer | `POST /rides/{id}/cancel` |
| any active | `cancelled` | staff (`support`/`admin`), reason required | `POST /admin/rides/{id}/cancel` |
| `in_progress` | `completed` | assigned rider | `POST /rides/{id}/complete` |

Any other transition → `409 INVALID_TRANSITION`. Transitions use a conditional update (GORM `Where("id = ? AND status = ?").Updates(...)` + `RowsAffected` check) so two concurrent accepts can't both win.

"Active" ride = `requested`, `accepted`, `arrived`, or `in_progress`.

Rider status follows the ride: accept → `on_trip`; complete or cancel → `online`.

## Data model

Money is integer IDR. Coordinates are `double` degrees (WGS84). Timestamps are UTC.

**User**
| Field | Type | Notes |
|-------|------|-------|
| id | uuid | PK |
| role | enum `consumer` \| `rider` \| `support` \| `admin` | staff roles never via signup |
| name | text | |
| email | text | unique, lowercased |
| phone | text | `+62…` |
| password_hash | text | bcrypt |
| suspended_at | timestamptz? | set → account can't log in or call the API ("disabled" for staff) |
| suspend_reason | text? | |
| created_at | timestamptz | |

**Rider** (1:1 with a `rider` User)
| Field | Type | Notes |
|-------|------|-------|
| user_id | uuid | PK, FK → User |
| vehicle_plate | text | e.g. `B 1234 XYZ` |
| vehicle_model | text | e.g. `Honda Beat` |
| status | enum `offline` \| `online` \| `on_trip` | default `offline` |
| last_lat, last_lng | double? | |
| last_location_at | timestamptz? | offers skip riders whose location is older than 30 s |

**Ride**
| Field | Type | Notes |
|-------|------|-------|
| id | uuid | PK |
| consumer_id | uuid | FK → User |
| rider_id | uuid? | FK → User, set on accept |
| pickup_lat, pickup_lng, pickup_address | double, double, text? | |
| dropoff_lat, dropoff_lng, dropoff_address | double, double, text? | |
| distance_meters | int | estimated, see ADR 0005 |
| fare_estimate | int | IDR |
| fare_final | int? | IDR, set on complete (= estimate) |
| status | enum, see lifecycle | |
| cancelled_by | enum `consumer` \| `rider` \| `support`? | |
| cancel_reason | text? | staff force-cancel only |
| requested_at, accepted_at, arrived_at, started_at, completed_at, cancelled_at | timestamptz? | one per transition |

**Ticket**
| Field | Type | Notes |
|-------|------|-------|
| id | uuid | PK |
| number | bigserial | human-friendly, unique |
| created_by | uuid | FK → User (consumer or rider) |
| ride_id | uuid? | FK → Ride; must involve `created_by` |
| category | enum, see PRD | |
| priority | enum `normal` \| `urgent` | `safety` → `urgent` |
| status | enum `open` \| `in_progress` \| `resolved` | |
| assignee_id | uuid? | FK → User (staff) |
| created_at, updated_at, resolved_at | timestamptz | |

**TicketMessage**
| Field | Type | Notes |
|-------|------|-------|
| id | uuid | PK |
| ticket_id | uuid | FK → Ticket |
| author_id | uuid | FK → User |
| body | text | ≤ 2 000 chars |
| internal | bool | staff note; never returned by `/tickets/*` |
| created_at | timestamptz | |

**AuditLog** (append-only)
| Field | Type | Notes |
|-------|------|-------|
| id | uuid | PK |
| actor_id | uuid? | FK → User (staff); null = server CLI |
| action | text | see `AuditAction` in the spec |
| target_type, target_id | text, uuid | `user` \| `ride` \| `ticket` \| `staff` |
| reason | text? | required for suspend/unsuspend/edit/force-cancel |
| before, after | jsonb? | changed fields only; never secrets |
| created_at | timestamptz | |

A migration adds a trigger that raises on `UPDATE` or `DELETE` of `audit_log`, so entries can't be changed even by a bug. Audit rows are written in the same transaction as the action they describe.

Indexes: `ride(consumer_id, requested_at desc)`, `ride(rider_id, requested_at desc)`, `ride(status)`, `rider(status)`, `ticket(status, priority, updated_at)`, `ticket(created_by)`, `audit_log(target_type, target_id, created_at desc)`, `audit_log(actor_id, created_at desc)`, trigram or `lower()` indexes on user name/email/phone and vehicle plate for staff search. At demo scale the 3 km lookup is a haversine filter over online riders; PostGIS is in the backlog.

## Folder structure

Proposed; created by tasks 001 and 002.

```
/
├── CLAUDE.md
├── README.md
├── .env.example
├── docker-compose.yml          # local dev: postgres + migrate + api (`docker compose up --build`)
├── .github/workflows/          # ci.yml, deploy.yml (ADR 0012)
├── deploy/                     # production compose, nginx server block, backup.sh, provision.md (docs/INFRA.md)
├── docs/
│   ├── PRD.md
│   ├── ARCHITECTURE.md
│   ├── INFRA.md                # hosting, CI/CD, runbook
│   ├── BACKLOG.md
│   ├── api/
│   │   ├── openapi.yaml        # REST contract (source of truth)
│   │   └── realtime.md         # WebSocket messages
│   ├── decisions/              # ADRs
│   └── tasks/                  # NNN-*.md + README.md (roadmap)
├── backend/
│   ├── go.mod
│   ├── Dockerfile              # multi-stage → distroless; binary has `serve`, `migrate`, `healthcheck`
│   ├── oapi-codegen.yaml
│   ├── cmd/api/main.go         # wires config, db, hub, Gin router; starts server
│   ├── migrations/             # goose SQL migrations
│   └── internal/
│       ├── config/             # reads env, fails fast
│       ├── api/                # api.gen.go (oapi-codegen, committed)
│       ├── httpapi/            # Gin router + groups, auth/validator/logger/recovery middleware, envelope writer
│       ├── model/              # GORM models (User, Rider, Ride, Ticket, TicketMessage, AuditLog)
│       ├── db/                 # GORM connection setup
│       ├── auth/               # handlers, service, repository, password, jwt
│       ├── riders/
│       ├── rides/              # handlers, service, repository, fare.go, lifecycle.go, dispatch.go
│       ├── realtime/           # hub.go (userID → conns), /ws handler, CloseUser(userID) on suspend
│       ├── tickets/            # user-side ticket handlers + service (shared with admin)
│       ├── audit/              # audit.Record(tx, entry) writer + list query
│       ├── admin/              # /admin/* handlers: users, rides, tickets, audit, staff; role guards
│       ├── cli/                # `api create-admin` (first admin account)
│       └── testutil/           # test DB setup, contract response validator
│                               # tests live next to code: *_test.go
└── frontend/                           # pnpm workspace (ADR 0010)
    ├── package.json                  # workspace root scripts: lint, test, typecheck (all packages)
    ├── pnpm-workspace.yaml           # apps/*, packages/*
    ├── tsconfig.base.json
    ├── eslint.config.js              # import boundaries for apps/packages/features
    ├── packages/
    │   ├── ui/                       # @ride/ui — atomic UI, no domain, no store
    │   │   └── src/
    │   │       ├── theme/            # colors, spacing, typography tokens
    │   │       ├── atoms/            # Button, Text, TextInput, Icon, Spinner, Badge, Avatar
    │   │       ├── molecules/        # FormField, SearchBar, InfoRow, Toast, CountdownLabel
    │   │       ├── organisms/        # ConfirmDialog, EmptyState, ErrorBanner, AppHeader
    │   │       ├── templates/        # ScreenTemplate, FormTemplate, MapTemplate (map + bottom sheet)
    │   │       └── index.ts
    │   ├── core/                     # @ride/core — plumbing + shared logic, no components, platform-neutral (RN + web)
    │   │   └── src/
    │   │       ├── http/client.ts    # axios instance + auth/401 interceptors
    │   │       ├── api/              # baseApi, axiosBaseQuery, ApiError, tags, shared endpoints (auth, rides)
    │   │       │   └── generated/    # openapi-typescript output (gitignored)
    │   │       ├── auth/             # authSlice, loginSchema, baseSignupSchema (zod)
    │   │       ├── realtime/         # WebSocket client, backoff, dispatches realtime/<event> actions
    │   │       ├── storage/          # TokenStorage interface; each app injects its own (secure store / sessionStorage)
    │   │       ├── form/             # applyServerErrors
    │   │       ├── utils/            # formatIdr, formatDate
    │   │       └── index.ts
    │   └── features/                 # @ride/features — domain UI shared by both apps
    │       └── src/
    │           ├── auth/             # LoginForm, SignupForm (base fields + slot), useSessionBootstrap(role)
    │           ├── history/          # RideHistoryList organism, HistoryScreen page (task 014)
    │           ├── trip-map/         # TripMap organism: pickup, dropoff, rider marker (011)
    │           └── index.ts          # one export per feature; no deep imports
    └── apps/
        ├── backoffice/               # Back office web app for staff (ADR 0014), served at admin.<domain>
        │   ├── index.html
        │   ├── vite.config.ts        # dev proxy /api → localhost:3000
        │   ├── Dockerfile            # build → nginx:alpine serving dist/ with security headers
        │   └── src/                  # imported as `@/…`
        │       ├── main.tsx          # Redux Provider, router, session bootstrap (staff roles only)
        │       ├── routes.tsx        # react-router: /login, /users, /users/:id, /rides, /rides/:id, /tickets, /tickets/:id, /audit, /staff
        │       ├── store/            # configureStore: core reducers + ui slice
        │       ├── shared/ui/        # web atomic UI (atoms, molecules, organisms, templates); CSS Modules
        │       └── features/
        │           ├── auth/         # staff LoginScreen, role gate, logout (020)
        │           ├── audit/        # audit log table + filters (021)
        │           ├── staff/        # staff list, create, change role, disable — admin only (022)
        │           ├── users/        # search, profile, edit, suspend/unsuspend (023)
        │           ├── rides/        # active rides list + live map (Leaflet), ride timeline, force-cancel (024)
        │           └── tickets/      # queue, ticket thread, reply/note, assign, resolve (025)
        ├── consumer/                 # Consumer app (passenger), bundle com.ridehailing.consumer
        │   ├── app.config.ts
        │   ├── app/                  # expo-router routes: one-line re-exports of feature screens
        │   │   ├── _layout.tsx       # Redux Provider, theme, useSessionBootstrap('consumer')
        │   │   ├── (auth)/           # login, signup
        │   │   └── (main)/           # index (request), ride, history
        │   └── src/                  # imported as `@/…`
        │       ├── store/            # configureStore: core reducers + rideLive slice
        │       └── features/
        │           ├── auth/         # LoginScreen, SignupScreen (consumer signupSchema) (003, 004)
        │           ├── ride-request/ # pick points, estimate, request, searching (006, 009)
        │           ├── trip/         # rider on the way, live map, status, cancel, summary (010–013)
        │           ├── history/      # route wrapper over @ride/features history (014)
        │           └── support/      # report a problem, my tickets, thread (026)
        └── rider/                    # Rider app (motorbike driver), bundle com.ridehailing.rider
            ├── app.config.ts
            ├── app/
            │   ├── _layout.tsx       # Redux Provider, theme, useSessionBootstrap('rider')
            │   ├── (auth)/           # login, signup
            │   └── (main)/           # index (online + offers), ride, history
            └── src/
                ├── store/            # configureStore: core reducers + availability + offers slices
                └── features/
                    ├── auth/         # LoginScreen, SignupScreen with VehicleFields (003, 004)
                    ├── availability/ # online toggle, location sender every 3 s (007)
                    ├── offers/       # offer cards, countdown, accept (009, 010)
                    ├── trip/         # arrive / start / complete, cancel (012, 013)
                    ├── history/      # route wrapper over @ride/features history (014)
                    ├── support/      # report a problem, my tickets, thread (026)
                    └── dev-tools/    # simulate rider movement, __DEV__ only (015)
    # tests live next to code: *.test.ts(x)
```

## Cross-cutting concerns

- **Response envelope**: every HTTP response body, success or error, is `{ "status": <HTTP code>, "data": <payload | null>, "errors": <Error[] | null> }`. The backend writes it through one helper per case (`writeData`, `writeErrors`); no handler builds JSON by hand. There are no `204` responses; "nothing" is `data: null`.
  ```json
  { "status": 200, "data": { "distanceMeters": 4200, "fareIdr": 19000 }, "errors": null }
  { "status": 400, "data": null, "errors": [
      { "code": "VALIDATION_ERROR", "field": "email", "message": "must be a valid email" },
      { "code": "VALIDATION_ERROR", "field": "vehicle.plate", "message": "is required" } ] }
  { "status": 409, "data": null, "errors": [ { "code": "RIDE_NOT_AVAILABLE", "message": "ride was already taken" } ] }
  ```
- **Errors**: each item is `{ code, message, field? }` (the `Error` schema); codes are listed in `docs/api/openapi.yaml` under `Error.code`. Validation reports **all** invalid fields at once, one item each, with `field` as a dot path. Other errors have a single item and no `field`. Unknown routes, panics (`500 INTERNAL_ERROR`, no stack trace), and the `/ws` auth failure use the same envelope.
- **Auth**: `Authorization: Bearer <jwt>` on every endpoint except signup/login. JWT payload: `{ sub: userId, role }`, HS256, 7-day expiry, secret in `JWT_SECRET`. Mobile stores it in `expo-secure-store`. The WebSocket upgrade sends the same `Authorization` header; invalid token → `401`, no upgrade. Role checks: consumer-only, rider-only, and staff-only (`/admin/*`) endpoints return `403 FORBIDDEN` to the wrong role; admin-only actions reject `support`. Staff tokens expire after 12 h. **Suspension**: the auth middleware loads the user's `suspended_at` on every request (one indexed lookup) and returns `403 ACCOUNT_SUSPENDED`, so suspension takes effect immediately despite stateless JWTs (ADR 0015).
- **Validation**: the `oapi-codegen` Gin request validator (`kin-openapi` underneath) checks every request (body, params, query) against `openapi.yaml` before it reaches a handler (multi-error mode on); Gin binding tags are not used; each failure becomes one `VALIDATION_ERROR` item in a `400` envelope. Rules the spec can't express (e.g. rider must send `vehicle`) are checked in the handler and reported the same way. Handlers implement the `oapi-codegen` strict interface, so request/response types can't drift from the spec.
- **Config**: env vars, documented in `.env.example`. Backend fails fast on startup if a required one is missing.
- **Time**: server is the clock. Expiry (60 s) runs on the server (`time.AfterFunc`, plus a sweep on startup); clients only display.
- **Logging**: `log/slog` JSON logs via a small Gin middleware (replaces `gin.Logger()`), one line per request (method, path, status, duration). `gin.Recovery()` is replaced by one that writes the `500` envelope. Never log passwords or tokens.
- **Testing**:
  - Backend: `go test ./...` calling the Gin router via `ServeHTTP` + `httptest.NewRecorder` against a real Postgres test database (`DATABASE_URL_TEST`, goose-migrated, each test in a rolled-back GORM transaction). Contract tests validate every response, envelope included, against `openapi.yaml` with `kin-openapi`. Run with `-race`.
  - Realtime: integration tests dial `/ws` on an `httptest.Server` with `coder/websocket`.
  - Time: services take a clock interface so expiry tests don't sleep 60 s.
  - Mobile: Jest + React Native Testing Library, rendering with a real Redux store (`renderWithStore` helper); HTTP mocked with `axios-mock-adapter`; zod schemas and `axiosBaseQuery` unit-tested directly.
  - End to end: manual checklist on two devices (task 016).
  - **Coverage: 100%** for the backend and each mobile app/package, enforced locally and in CI; every feature ships its unit tests in the same task. Exclusions and rules in ADR 0013.
- **Mobile data flow**: screens → RTK Query hooks (`useGetCurrentRideQuery`, `useRequestRideMutation`) → `axiosBaseQuery` → axios. WebSocket messages → `lib/realtime` → store (`ride:updated` patches the `getCurrentRide` cache; `rider:location` → `rideLive` slice; offers → `rider` slice). Components never call axios directly.
- **Mobile errors**: RTK Query errors are `{ status, errors: Error[] }`. Forms pass them to `applyServerErrors` (field errors under inputs, the rest in a banner); other screens show the first `message` in an `ErrorBanner`. `status: 0` / `NETWORK_ERROR` means the backend was unreachable.
- **Spec lint**: `npx @redocly/cli lint docs/api/openapi.yaml` must pass.
