# 0014: Back office as a React + Vite web app in the frontend workspace

- **Date:** 2026-11-28
- **Status:** proposed

## Context

Staff need to search users, read ride timelines, watch active rides on a map, and work a ticket queue, mostly from a desk with a big screen and a keyboard. The Consumer and Rider apps already share axios, RTK Query, zod, React Hook Form, and the envelope handling in `@ride/core` (ADRs 0007, 0008, 0010).

## Decision

A web app at `frontend/apps/backoffice`:

- **React 18 + Vite + TypeScript**, `react-router` for routes, **CSS Modules** for styling (built into Vite; no UI framework).
- Reuses `@ride/core` for axios, `baseApi`/`axiosBaseQuery`, generated API types, `authSlice`, and `applyServerErrors`. Admin endpoints are injected by the back office's own features.
- **Same structure rules** as the mobile apps (ADR 0009): `src/features/<feature>/` with screens (pages) and domain organisms; web atoms → molecules → organisms → templates in `src/shared/ui/`. `@ride/ui` (React Native) is not used; web atoms stay inside the back office until a second web app needs them.
- **Map**: `react-leaflet` with OpenStreetMap tiles for the active-rides map (no API key).
- **Freshness by polling**, not WebSocket: active rides every 5 s, ticket queue every 15 s, via RTK Query `pollingInterval`. Polling stops when the tab is hidden.
- **Same origin**: served at `https://admin.<domain>`, where the host nginx sends `/api/*` to the backend (prefix stripped) and everything else to the back office container. No CORS needed, and the token never goes cross-origin.
- **Token storage**: in memory plus `sessionStorage` (cleared when the tab closes), through `@ride/core`'s `TokenStorage` adapter. Strict CSP (`script-src 'self'`), `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer` from the container's nginx.
- **Tests**: Vitest + React Testing Library + `axios-mock-adapter`, 100% coverage (ADR 0013).

## Alternatives considered

- **Third Expo app** (React Native, `@ride/ui`): one UI toolkit, but tables, filters, and long support sessions are awkward on mobile layouts.
- **Next.js**: SSR and routing we don't need for an authenticated internal tool; a static SPA is simpler to host.
- **Admin generators (React-admin, Refine, Retool)**: fast CRUD, but they fight the envelope, our atomic structure, and the audit/reason requirements; Retool is a hosted third party with access to user data.
- **WebSocket for staff**: live updates, but needs staff rooms and fan-out of every ride event; 5 s polling of one list is enough for a handful of agents.
- **httpOnly cookie session for staff**: safer against XSS than `sessionStorage`, but needs a second auth mechanism next to bearer JWTs. CSP + short 12 h tokens is the accepted trade-off; revisit with 2FA (backlog).

## Consequences

- `@ride/core` must stay platform-neutral: no `react-native` or Expo imports; storage is injected by each app.
- Web and native atoms are separate; visual consistency comes from shared theme token values copied into CSS variables.
- Polling adds a few requests per agent per minute; trivial at our scale.
- One more image to build and deploy (`ride-hailing-backoffice`), served by its own small nginx container on `127.0.0.1:3001`.
