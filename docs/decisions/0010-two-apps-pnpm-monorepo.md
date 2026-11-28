# 0010: Two mobile apps (Consumer, Rider) in a pnpm monorepo

- **Date:** 2026-11-28
- **Status:** proposed

## Context

Consumers (passengers) and riders (motorbike drivers) have different jobs, permissions, and store listings, as in Gojek/Grab. One app with role-based screens ships rider-only code (location sending, offers, simulate mode) to every consumer and makes each screen check the role. But both apps share a lot: atomic UI, the axios/RTK Query/WebSocket plumbing, auth, and ride types.

## Decision

Two Expo apps in a **pnpm workspace** under `frontend/`:

- `apps/consumer` (**Consumer app**): signup/login as `consumer`, request rides, track the rider, history.
- `apps/rider` (**Rider app**): signup/login as `rider` (with vehicle), go online, offers, trip lifecycle, history, dev simulate mode.
- `packages/ui` (`@ride/ui`): theme tokens + atoms, molecules, generic organisms, templates. No domain types, no store, no API.
- `packages/core` (`@ride/core`): non-UI plumbing: axios client, `baseApi` + `axiosBaseQuery`, generated API types, shared endpoints (auth, `getCurrentRide`, `getRide`, `listRides`, `cancelRide`), `authSlice`, realtime client, secure storage, `applyServerErrors`, formatters.
- `packages/features` (`@ride/features`): domain UI used by **both** apps: `auth` (LoginForm, base SignupForm, `useSessionBootstrap`), `history` (RideHistoryList, screen), `trip-map` (map with pickup/dropoff/rider markers).

Each app keeps its own `src/features/` for app-only features and its own Redux store that mounts `@ride/core`'s reducers plus its own slices.

A third app, the **Back office** web app (`apps/backoffice`), lives in the same workspace and reuses `@ride/core` (ADR 0014). The workspace root is `frontend/`.

Each app is locked to one role: after login, if `user.role` isn't the app's role, the app discards the token and shows "This is a consumer account — please use the Consumer app" (or vice versa). Role guards on the backend still protect every endpoint.

## Alternatives considered

- **One app, role switch** (previous plan): one build to install, but role branching everywhere and rider-only code shipped to consumers.
- **Two independent Expo projects**: no workspace tooling, but atoms and API plumbing get copied and drift.
- **Nx / Turborepo**: build caching and graphs we don't need for two apps and three packages; plain pnpm workspaces are enough.

## Consequences

- Two dev builds to install for the two-device demo (one per phone), each with its own app name, icon, and bundle ID (`com.ridehailing.consumer`, `com.ridehailing.rider`).
- Dependency direction: `apps → @ride/features → @ride/ui, @ride/core`; `@ride/ui` and `@ride/core` never import each other's internals or any app. Enforced by each package's `dependencies` + ESLint.
- Metro needs workspace config (`watchFolders`, `nodeModulesPaths`); Expo SDK 52+ handles most of it.
- A change to a shared package can break both apps; CI/local `pnpm -r test` runs everything.
- The API role enum is `consumer | rider`; the app split needs no API change.
