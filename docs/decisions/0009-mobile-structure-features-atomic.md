# 0009: Mobile structure: feature folders + atomic UI components

- **Date:** 2026-11-28
- **Status:** proposed

## Context

Consumer and rider flows share UI pieces (buttons, inputs, map layout) but have separate logic. As tasks land one by one, we want each task to touch mostly one folder, and shared UI to stay consistent.

## Decision

**Feature-based** code under `src/features/<feature>/`, and **atomic design** for UI:

| Level | Where | May use | Must not |
|-------|-------|---------|----------|
| Atoms | `@ride/ui` `atoms/` | RN primitives, theme tokens | other atoms' internals, store, API, RHF |
| Molecules | `@ride/ui` `molecules/` | atoms | store, API |
| Organisms | `@ride/ui` `organisms/` (generic), `@ride/features` (domain, both apps), or `apps/*/src/features/*/components/` (domain, one app) | atoms, molecules; feature organisms may use their own feature's hooks | another feature's internals |
| Templates | `@ride/ui` `templates/` | layout + slots (`children`, `header`, `footer`) | data, business logic |
| Pages | `apps/*/src/features/*/screens/` (or `@ride/features` for shared screens like history) | everything in its feature, `@ride/*` packages | — |

- `app/` (expo-router) files are one-liners that re-export a feature screen: `export { LoginScreen as default } from '@/features/auth'`.
- Each feature exposes a public API via `index.ts`. Other code imports only from `@/features/<name>`, never deep paths.
- Dependency direction: `app/ routes → app features → @ride/features → @ride/ui, @ride/core`. Packages never import from apps. Enforced by ESLint (`import/no-restricted-paths`) and package `dependencies` (ADR 0010).
- The back office web app (ADR 0014) follows the same levels with web atoms in `apps/backoffice/src/shared/ui/`.
- A piece moves up only when needed twice: from an app feature to `@ride/features` when the other app needs it; generic UI to `@ride/ui` when a second feature needs it.

## Alternatives considered

- **Layer folders** (`screens/`, `components/`, `redux/`, `services/`): one task touches five folders; boundaries blur.
- **Atomic only, no features**: good UI reuse, but business logic has no home.
- **Feature-sliced design (full)**: more layers (`entities`, `widgets`, `processes`) than an app this size needs.

## Consequences

- A task like "trip history" lives mostly in `@ride/features/history` plus a one-line route in each app.
- Atoms and molecules are pure and easy to test; snapshot-free RNTL tests on behavior.
- Some judgment calls about level (molecule vs organism); rule of thumb: if it needs domain types (`Ride`, `Rider`), it's a feature organism.
