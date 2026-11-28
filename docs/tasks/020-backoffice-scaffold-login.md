# 020: Back office scaffold and staff login

- **Status:** todo   <!-- todo | in-progress | blocked | done -->
- **Depends on:** 013, 014, 015 (core ride flow first; also needs 002, 005)
- **PRD flow:** 8. Staff log in

## Goal

Staff open the back office in a browser, log in with a `support` or `admin` account, and see an empty dashboard shell with navigation. The first admin can be created on the server from the command line.

## Scope

**In:**
- Backend: roles `support`/`admin` in model + migration; signup still rejects them; staff token expiry 12 h; `requireStaff` / `requireAdmin` guards on an `/admin` route group (ADR 0015); `api create-admin --email --name` CLI (password from stdin)
- `@ride/core`: `TokenStorage` interface injected by each app; mobile apps pass an `expo-secure-store` adapter (no behavior change); no React Native imports left in `@ride/core`
- `frontend/apps/backoffice` per `docs/ARCHITECTURE.md` (ADR 0014): Vite + React + TS, react-router, store with `@ride/core` reducers, `sessionStorage` token adapter, Vite dev proxy `/api` → `localhost:3000`, base URL `/api`
- Web atoms `Button`, `Text`, `TextInput`, `Badge`, `Spinner`; molecules `FormField`, `Pagination`; organisms `DataTable`, `ErrorBanner`, `ConfirmDialog` (with required reason input); templates `AppShell` (sidebar + header), `AuthTemplate`
- `features/auth`: staff `LoginScreen` (RHF + `loginSchema`), role gate (consumer/rider accounts get "This account can't use the back office"), logout, auto-logout on `401`/`ACCOUNT_SUSPENDED`
- Sidebar shows Staff only for `admin`
- Vitest + RTL + `axios-mock-adapter` with 100% thresholds; ESLint boundaries as in the other apps

**Out (don't build here):**
- Any admin data pages (021–025)
- Deploying the back office (027)

## API

- none new (uses `POST /auth/login`, `GET /me`; role enum and login `403` already in spec)

## Acceptance criteria

- [ ] `create-admin` creates an `admin` user; running it twice with the same email fails cleanly; the password never appears in logs or shell history
- [ ] `POST /auth/signup` with `role: support` or `admin` → `400`
- [ ] Staff token `exp` is 12 h; consumer/rider token still 7 days
- [ ] A dummy route behind `requireStaff` → `403` for consumer/rider; behind `requireAdmin` → `403` for support
- [ ] Back office: staff login lands on the dashboard; consumer/rider login is refused with a message and no token stored; reload keeps the session; closing the tab ends it
- [ ] Consumer and Rider apps still pass all their tests after the `TokenStorage` change
- [ ] Unit tests added for every new/changed function, handler, slice, endpoint, schema, hook, and component
- [ ] Tests cover the cases above and pass; coverage is 100% in every touched codebase (ADR 0013), output pasted in Notes

## Notes

