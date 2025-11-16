# 2. Migration from PostgreSQL to SQLite

Date: 2025-11-16

## Status

Accepted

## Context

Missas.com.br originally used PostgreSQL as its primary database. PostgreSQL is powerful and mature, but the project’s real needs are limited: it is a small, mostly read‑only application, with low concurrency and no use of database‑specific features.

The project is currently hosted on Render.com, where PostgreSQL adds a monthly cost (~$7/month). As a side project that generates no revenue, ongoing operational cost matters. Normally this migration would not be prioritized, but recent AI-assisted code generation tooling made the migration faster, reducing the cost (time and effort) of the change.

The deployment model also plays a role. Render offers persistent disks that work well with SQLite, and both Render and future VPS environments provide simple filesystem-based persistence that aligns naturally with SQLite’s single-file design. Backups are also handled automatically by Render and would be easy to configure on a VPS.

The project will soon introduce geocoding features. Django supports both PostGIS (PostgreSQL) and SpatiaLite (SQLite) for geographic data. Since the project’s geospatial needs are simple, SQLite remains a suitable option.

Finally, because the site’s traffic is light and the majority of requests are public, cacheable reads, SQLite’s limited concurrency model is not a concern. Writes (e.g., via the admin or small data-entry features) are infrequent, and the overall read-heavy nature of the workload aligns well with SQLite’s strengths.

## Decision

Migrate the project’s primary database from PostgreSQL to SQLite.

### Migration Plan

1. **Add SQLite configuration** to the project and run migrations to create the SQLite schema, while keeping PostgreSQL as the active default database.
2. **Migrate data** from PostgreSQL into SQLite. PostgreSQL remains the default database during this step.
3. **Switch the default database** to SQLite. SQLite becomes the source of truth. PostgreSQL is retained for verification, manual inspection, or rollback if any migration issues appear.
4. **Remove PostgreSQL** once all data is confirmed correct and the application is fully operating on SQLite, eliminating unnecessary cost and maintenance.

## Rationale

* **Cost reduction:** PostgreSQL on Render costs approximately $7/month. For a non‑commercial side project, this expense accumulates with little benefit.
* **Low migration effort thanks to AI:** Normally, switching databases would not justify the effort, but AI tooling (scripts, code generation) reduced migration time significantly, making the cost-benefit tradeoff favorable.
* **Operational simplicity:** SQLite is a single-file database with zero administration. It removes the need to manage PostgreSQL on a future VPS.
* **Compatible with project needs:** The project does not use any PostgreSQL-specific features and relies mostly on simple CRUD operations. Django’s support for SpatiaLite makes geospatial features possible without PostGIS.
* **Workload characteristics:** Traffic is low, read-heavy, and cacheable. SQLite performs well under these conditions.
* **Future-proof for planned hosting changes:** If migrating from Render to a VPS, SQLite keeps the stack lightweight and avoids the overhead of running a database server.
* **Backups remain straightforward:** Render persistent disks provide automatic backups, and VPS environments can mirror this with standard filesystem snapshot tools.

## Consequences

### Positive

* Reduced monthly operating cost.
* Simpler development, deployment, and local setup.
* Easier migration to VPS in the future.
* Minimal maintenance burden.

### Negative / Trade-offs

* SQLite on Render’s persistent disk does not support zero-downtime deploys, causing brief downtime on each deploy. This is acceptable for a small side project.
* SQLite has limited concurrency, though current traffic patterns make this a negligible issue.

## When to Revisit

* If traffic grows substantially and write concurrency becomes an issue.
* If new features require advanced indexing, partitioning, or heavy geospatial querying.
* If moving into a commercial, SLA‑driven phase where downtime must be minimized.
