# 0001: Mobile app with React Native + Expo

- **Date:** 2026-11-27
- **Status:** proposed

## Context

We need mobile apps for consumers and riders that run on real Android and iOS phones, uses GPS and a map, and can be built by a small team quickly. The success criteria require two real devices, so fast install-on-device matters more than native polish.

## Decision

React Native with Expo (TypeScript), `expo-router` for navigation, `expo-location` for GPS and geocoding, `react-native-maps` for the map, `expo-secure-store` for the token. Run on devices with an Expo development build.

## Alternatives considered

- **Flutter**: equally capable; Expo was picked for the larger ecosystem for maps and location and faster setup on real devices.
- **Native (Kotlin + Swift)**: two codebases for one demo; far slower.
- **Bare React Native without Expo**: more native setup for no feature we need.

## Consequences

- API types generated from `openapi.yaml` with `openapi-typescript`, so the app and the Go backend stay in sync through the spec.
- Two apps (Consumer, Rider) sharing packages in one workspace; see ADR 0010.
- Google Maps on Android needs an API key in the dev build config (`GOOGLE_MAPS_API_KEY`); iOS uses Apple Maps by default.
- Background location and push are harder in Expo; both are non-goals for now.
