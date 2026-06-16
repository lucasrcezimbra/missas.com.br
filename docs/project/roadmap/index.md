# Roadmap

The roadmap describes meaningful progress, not every task.

Ariad's default delivery taxonomy applies:

- **Value / CV:** major delivery stage with clear impact.
- **Delivery Story:** coherent delivery arc inside a Value / CV.
- **User Story:** atomic delivery verified end to end through observable behavior or capability.
- **Technical Story:** internal capability needed by a Delivery Story.
- **Task:** concrete work inside a User Story or Technical Story.
- **Maintenance:** legitimate work that may sit outside roadmap structure.

Recommended states: `Planned`, `Active`, `Blocked`, `Validated`, `Done`, `Deferred`, `Dropped`.

## Current Focus

Preserve a reliable, low-friction Django site for finding Mass and confession schedules while improving parish data quality and location-based discovery.

This focus is complete when users can continue to find trustworthy schedules, contributors can run and validate the project easily, and data update paths remain understandable.

## Active Work

| Item | Status | Notes |
|------|--------|-------|
| Maintenance: Ariad adoption | Active | Add local Ariad project memory and replace legacy agent instructions with `AGENTS.md`. |

## Planned Work

- Improve schedule data quality and verification workflows.
- Continue refining parish, location, and contact data maintenance.
- Improve location-based discovery without adding SpatiaLite or PostGIS.
- Keep deployment simple and low cost.

## Done

- Initial Django application for parish and schedule search exists.
- SQLite adopted as the project database direction.
- Geocoding direction chosen: decimal latitude/longitude and Python-side distance calculations.
- ADRs added under `docs/architecture/decisions/`.

## Radar

- **Schedule freshness:** users need confidence that times are still valid; plan work when stale data becomes visible or update volume grows.
- **Nearby parish discovery:** users may want schedules near their current location; plan work when location data coverage is sufficient.
- **Contributor data-entry flow:** manual data updates can become slow; plan work when WhatsApp or admin workflows become bottlenecks.
- **Hosting model:** revisit if traffic, reliability needs, or Render cost trade-offs change.
