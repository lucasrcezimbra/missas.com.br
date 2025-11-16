# 3. Geocoding without SpatiaLite

Date: 2025-11-16


## Status

Accepted


## Context

As part of adding geocoding features (retrieving nearby parishes and schedules by user location), we evaluated Spatialite as a potential spatial extension to SQLite. Spatialite is the official GIS extension for SQLite and is supported by GeoDjango.

The geocoding use case for the project will be modest: Find nearby parishes and schedules; apply a maximum distance filter; order by distance. This requires only simple point geometry and basic distance calculations.


## Decision
**We will not adopt Spatialite or PostGIS.**

Instead, we will:

- Store coordinates as simple `latitude` and `longitude` float fields.
- Perform distance calculations in Python (e.g., Haversine or approximate deltas).
- Filter and sort in Python after querying only nearby rows.
- Enforce a maximum radius in the API to avoid returning excessive data.


## Rationale
The decision is based on the following factors:

### 1. Low contributor friction
The project prioritizes a simple “clone → install → run” setup.
Spatialite introduces:

- OS-specific installation steps
- Native library dependencies
- Compilation requirements on some platforms
- Divergent behaviors across systems (e.g., macOS vs Debian vs Ubuntu)

Removing Spatialite keeps onboarding trivial for new contributors. No need for external services, native libraries, or OS-specific tooling.

### 2. We don’t need advanced GIS queries
The current geocoding needs are simple:

- Distance calculation
- Max-distance filtering
- Ordering by distance

These can be implemented efficiently in Python.

### 3. The dataset is small
The number of parishes and schedules is manageable, and typical geospatial queries return only a small subset of rows.
This keeps Python-side filtering inexpensive and performant.


## Consequences

- Distance filtering and ordering will be performed in Python, not in SQL.
- API endpoints will use a maximum allowed radius to keep result sets manageable.
- If the future requires more advanced GIS operations—spatial indexes, complex geometry relationships, projections—we may re-evaluate adopting Spatialite or migrating to PostGIS.
