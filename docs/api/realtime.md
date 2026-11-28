# Realtime contract (WebSocket)

> Server → client pushes only. Clients never change state over the socket; they call the REST API (`openapi.yaml`). Change this file first, like the OpenAPI spec. See ADR 0004.

## Connection

- URL: `ws://<api-host>/ws` (same host and port as the REST API).
- Auth: `Authorization: Bearer <accessToken>` header on the upgrade request. In React Native: `new WebSocket(url, undefined, { headers: { Authorization: "Bearer …" } })`. Missing/invalid/expired token → HTTP `401` with the standard error envelope (`errors: [{ code: UNAUTHORIZED }]`); no upgrade.
- The server registers the connection under the user's ID. Every message for that user goes to all their connections, so one user with two devices gets both.
- Keepalive: server pings every 25 s and closes connections that don't pong within 10 s.
- Reconnect: the client retries with backoff (1 s, 2 s, 4 s … capped at 30 s) while logged in.
- **On every (re)connect the client calls `GET /rides/current`** to resync. Messages missed while disconnected are not replayed.
- Server → client only. Anything the client sends is ignored.
- Suspension: when staff suspend or disable an account, the server closes that user's connections with close code `4003` and reason `ACCOUNT_SUSPENDED`. Clients don't reconnect after `4003`; they log out and show "Your account is suspended. Contact support."
- Staff (`support`, `admin`) don't use the WebSocket; the back office polls (ADR 0014).

## Message format

Every message is one JSON text frame:

```json
{ "event": "ride:updated", "data": { "ride": { "...": "..." } } }
```

## Events

Payload schemas reference `docs/api/openapi.yaml` components.

| `event` | To | When | `data` |
|-------|----|------|---------|
| `ride:offered` | each `online` rider with a fresh location (≤ 30 s old) within 3 km of pickup | ride created | `{ ride: Ride }` |
| `ride:offer_withdrawn` | every rider who got the offer, except the one who accepted | accepted by someone else, cancelled, or expired | `{ rideId: string, reason: "taken" \| "cancelled" \| "expired" }` |
| `ride:updated` | consumer + assigned rider (if any) | any status change, including staff force-cancel (`cancelledBy: support`) | `{ ride: Ride }` |
| `ticket:updated` | the ticket's owner (consumer or rider) | staff reply (not internal notes) or status change | `{ ticketId: string, status: "open" \| "in_progress" \| "resolved" }` |
| `rider:location` | consumer of the rider's active ride | rider `PUT /riders/me/location` while ride is `accepted`, `arrived`, or `in_progress` | `{ rideId: string, location: LatLng, at: date-time }` |

## Rules

- WebSocket messages use `{ event, data }`, not the HTTP `{ status, data, errors }` envelope: there is no status or error on a push.
- The payload `ride` is the same shape as the REST `Ride` schema (the `data` of REST ride responses), so clients reuse one type.
- Clients treat events as hints: if a `ride:updated` arrives for a ride they don't know, they fetch `GET /rides/{rideId}`.
- Event names are `noun:verb` with snake_case after the colon. New events are added here before code changes; clients ignore events they don't know.
