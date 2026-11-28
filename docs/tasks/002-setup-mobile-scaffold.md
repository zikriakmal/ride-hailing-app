# 002: Mobile workspace scaffold (Consumer + Rider apps)

- **Status:** todo   <!-- todo | in-progress | blocked | done -->
- **Depends on:** 001
- **PRD flow:** none (foundation)

## Goal

A developer can run both the Consumer app and the Rider app on real phones from one pnpm workspace, and each reaches the local backend's `/health` through the real data stack (axios → RTK Query → Redux). Shared packages and the feature-based, atomic layout exist so later tasks only add features.

## Scope

**In:**
- `frontend/` pnpm workspace per `docs/ARCHITECTURE.md` (ADRs 0001, 0009, 0010): `apps/consumer`, `apps/rider`, `packages/ui`, `packages/core`, `packages/features`; shared `tsconfig.base.json`; Metro configured for the workspace
- Each app: own `app.config.ts` (name, icon placeholder, bundle ID `com.ridehailing.consumer` / `com.ridehailing.rider`), `@/` alias to its `src/`, route groups `(auth)` and `(main)` with placeholder screens re-exported from its features
- `@ride/core`:
  - `http/client.ts`: axios instance, base URL from `EXPO_PUBLIC_API_URL`, 10 s timeout, bearer token interceptor (ADR 0007)
  - `api/`: `axiosBaseQuery` unwrapping `{ status, data, errors }` (network failure → `status: 0`, `NETWORK_ERROR`), `baseApi` with tags `Me`, `Ride`, `RideHistory`, a `getHealth` endpoint
  - types generated from `docs/api/openapi.yaml` into `api/generated/`
  - `form/applyServerErrors` (ADR 0008)
- `@ride/ui`: theme tokens; atoms `Button`, `Text`, `TextInput`, `Spinner`; molecule `FormField` (label + input + error, RHF `Controller`); template `ScreenTemplate`
- `@ride/features`: empty `index.ts`
- Each app's `src/store/`: `configureStore` with `baseApi` reducer + middleware, typed hooks
- ESLint import boundaries: `apps → @ride/features → @ride/ui, @ride/core`; packages never import apps; `@ride/ui` never imports `@ride/core`; no deep imports into features
- Jest + RNTL in every package/app with `coverageThreshold.global` at 100% (statements, branches, functions, lines) and the ADR 0013 exclusions in `collectCoverageFrom`; `renderWithStore` helper and `axios-mock-adapter`
- Root scripts `pnpm -r lint`, `pnpm -r test`, `pnpm -r typecheck`; run commands for both apps added to `CLAUDE.md` and `README.md`

**Out (don't build here):**
- Real screens, login, maps (later tasks)
- App store builds, real icons/splash

## API

- none (uses `GET /health`)

## Acceptance criteria

- [ ] Documented commands launch each app on a physical device; both show backend health `ok` on a dev screen, with different app names on the home screen
- [ ] `axiosBaseQuery` returns `data` for a success envelope, `{ status, errors }` for an error envelope, and `status: 0` + `NETWORK_ERROR` on timeout (unit tests with `axios-mock-adapter`)
- [ ] `applyServerErrors` calls `setError` per `field` and puts field-less errors on `root.serverError` (unit test)
- [ ] Atoms and `FormField` render and fire their callbacks; `FormField` shows the RHF error message (RNTL tests)
- [ ] ESLint fails on `@ride/ui` importing `@ride/core`, a package importing from an app, and a deep import into a feature (proved once, then removed)
- [ ] Release config: Android `usesCleartextTraffic=false` outside dev, iOS ATS on; no secrets in `app.config.ts` beyond the restricted Maps key (docs/SECURITY.md)
- [ ] ESLint security rules on (`no-eval`, `react/no-danger`); `osv-scanner` clean on `pnpm-lock.yaml`
- [ ] `pnpm -r lint`, `pnpm -r typecheck`, and `pnpm -r test` pass
- [ ] `pnpm -r test:coverage` reports 100% for all five workspaces and fails when an untested branch is added (proved once, then removed)

## Notes

