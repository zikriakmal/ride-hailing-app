# 0007: Mobile state with Redux Toolkit + RTK Query over axios

- **Date:** 2026-11-28
- **Status:** proposed

## Context

The app mixes server data (current ride, history, estimate) with client state that changes fast and arrives over WebSocket (rider location, offers, session). Every HTTP response is wrapped in `{ status, data, errors }`, and any `401` must log the user out. We want one predictable place for state and one place that understands the envelope.

## Decision

- **axios** is the only HTTP client (`@ride/core` `http/client.ts`): base URL from `EXPO_PUBLIC_API_URL`, request interceptor adds `Authorization` from the store, 10 s timeout.
- **RTK Query** for all server data, using a custom `axiosBaseQuery` that unwraps the envelope: success → `{ data: body.data }`, error → `{ error: { status, errors } }`. Network failure/timeout → `{ status: 0, errors: [{ code: "NETWORK_ERROR" }] }` (client-only code). One `baseApi` in `@ride/core` (with endpoints both apps use); each app feature adds its own endpoints with `baseApi.injectEndpoints`. Each app has its own store (ADR 0010).
- **Redux Toolkit slices** only for client state: `auth` (token, user; in `@ride/core`), Rider app `availability` + `offers`, Consumer app `rideLive` (latest rider location).
- WebSocket messages are dispatched into the store: `ride:updated` patches the `getCurrentRide` cache via `api.util.updateQueryData`; `rider:location` goes to the `rideLive` slice; offers go to the `rider` slice.
- Any `401` envelope → `auth/loggedOut`, which also resets the API cache and closes the socket.
- The token lives in `expo-secure-store`, not in redux-persist; it is loaded into the `auth` slice on launch.

## Alternatives considered

- **Slices + `createAsyncThunk` with axios**: works, but we'd hand-write loading flags, caching, and refetch-after-mutation that RTK Query gives for free.
- **RTK Query `fetchBaseQuery`**: no axios needed, but we want axios interceptors and timeouts.
- **TanStack Query + Zustand**: lighter, but two libraries instead of one store with devtools.
- **redux-persist for the token**: stores it in AsyncStorage (not encrypted).

## Consequences

- Screens read `useGetCurrentRideQuery()` etc.; mutations invalidate tags (`Ride`, `RideHistory`, `Me`), so lists refresh without manual wiring.
- The envelope is handled in exactly one function; feature code never sees `status`/`errors` wrappers except through the typed error.
- Hand-written endpoint definitions must match `docs/api/openapi.yaml`; types come from `openapi-typescript` to keep them honest.
- Tests mock HTTP with `axios-mock-adapter` and render with a real store.
