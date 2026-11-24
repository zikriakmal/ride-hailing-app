# Architecture

> Stack, data model, folder structure. Update this file in the same change that alters any of them.

## Stack

<!-- TODO: choose and record the "why" for each in docs/decisions/ -->
| Layer | Choice | ADR |
|-------|--------|-----|
| Mobile | TBD | — |
| Backend | TBD | — |
| Database | TBD | — |
| Realtime (driver location, ride status) | TBD | — |
| Maps / geocoding | TBD | — |
| Auth | TBD | — |
| Hosting | TBD | — |

## System overview

```
[Rider app] ─┐                 ┌─> [Database]
             ├─> [Backend API] ┤
[Driver app]─┘        ▲        └─> [Maps provider]
                      │
               realtime channel
           (location + ride status)
```

## Data model

<!-- TODO: refine once stack is chosen -->
- **User**: id, role (`rider` | `driver`), name, phone, email, created_at
- **Driver**: user_id, vehicle info, status (`offline` | `online` | `on_trip`), last_location
- **Ride**: id, rider_id, driver_id?, pickup, dropoff, status, fare_estimate, fare_final, timestamps
- **RideStatus**: `requested` → `accepted` → `arriving` → `in_progress` → `completed` (or `cancelled`)

## Folder structure

<!-- TODO: fill in once scaffolding exists -->
```
/
├── CLAUDE.md
├── docs/
├── backend/        # API server
├── mobile/         # rider + driver app
└── .claude/        # agents & commands
```

## Cross-cutting concerns

- **Errors**: <!-- TODO: standard error response shape (also define in openapi.yaml) -->
- **Auth**: <!-- TODO: token type, expiry, refresh -->
- **Config**: env vars, documented in `.env.example`
- **Testing**: <!-- TODO: unit / integration / e2e approach -->
