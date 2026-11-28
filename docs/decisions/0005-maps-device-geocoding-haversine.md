# 0005: Map display, device geocoding, haversine distance

- **Date:** 2026-11-27
- **Status:** proposed

## Context

Consumers pick pickup and destination, see a fare estimate within 2 s, and watch the rider on a map. Paid map APIs (Directions, Places) need billing accounts and add latency and failure modes.

## Decision

- Map: `react-native-maps` (Google on Android, Apple on iOS).
- Address search and reverse geocoding: `expo-location` (`geocodeAsync` / `reverseGeocodeAsync`), using the phone's built-in geocoder. No API key.
- Distance: haversine straight line × 1.3 road factor, computed on the backend. Fare from that (PRD rules).

## Alternatives considered

- **Google Directions + Places APIs**: accurate road distance and nicer autocomplete, but billing, keys, and a network hop in the estimate path.
- **Mapbox / OSRM self-hosted**: accurate and free-ish, but more setup than a demo justifies.

## Consequences

- Estimate is instant and needs no external call.
- Fares are approximate; long or winding routes are underpriced.
- Device geocoder quality varies by OS; search has no autocomplete.
- Route-based distance is in the backlog.
