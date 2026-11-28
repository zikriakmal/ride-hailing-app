# 0004: Plain WebSocket for server → client pushes only

- **Date:** 2026-11-28
- **Status:** proposed

## Context

Riders must receive offers within 5 s and consumers must see the rider move at least every 3 s. Mobile networks drop connections often. We also want every state change to be testable against the OpenAPI contract. The backend is Go (ADR 0002).

## Decision

One WebSocket endpoint `GET /ws` on the backend using `github.com/coder/websocket`; the app uses React Native's built-in `WebSocket`. The socket is **push only**: clients make every change over REST (including rider location every 3 s); the server sends JSON messages `{ "event", "data" }` to every connection of a user via an in-memory hub keyed by user ID. The client reconnects with backoff and resyncs with `GET /rides/current`. Messages are specified in `docs/api/realtime.md`.

## Alternatives considered

- **Socket.IO**: rooms and auto-reconnect built in, but Go server libraries only support old protocol versions and are unmaintained.
- **gorilla/websocket**: fine and widely used; `coder/websocket` has a smaller, context-aware API.
- **Polling only**: 3 s polling from both apps is simple but slower for offers and wasteful.
- **Location over the socket instead of REST**: fewer requests, but splits writes across two transports and makes contract tests harder.

## Consequences

- One write path (REST) to validate, authorize, and test.
- We write ~50 lines each for the hub (server) and reconnect-with-backoff (client) that Socket.IO would have given us.
- Server sends a ping every 25 s to detect dead connections.
- Missed messages are not replayed; resync on reconnect is mandatory.
- Single backend instance only (in-memory hub); fine per non-goals.
