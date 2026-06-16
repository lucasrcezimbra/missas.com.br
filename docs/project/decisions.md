# Decisions

Incremental decisions made as the project evolves.

Architecture Decision Records in `docs/architecture/decisions/` remain the canonical record for architecture decisions. This file summarizes project-shaping decisions for agent context and records non-architecture process/product decisions when useful.

## Completed Decisions

Add newest decisions at the top.

### Adopt Ariad as the local agent method

**Date:** 2026-06-15  
**Status:** Decided

Decision: Adopt Ariad project documentation and `AGENTS.md` as the local operating contract for agentic development.

Rationale: The project benefits from a small, explicit memory surface for process, project, and product context. Ariad reduces repeated re-orientation and keeps future agent sessions coherent.

Consequences: `AGENT.md` and `CLAUDE.md` were removed. Future agents should start from `AGENTS.md` and the local docs under `docs/project/`, `docs/process/`, and `docs/product/`.

### Geocoding without SpatiaLite

**Date:** 2025-11-16  
**Status:** Decided  
**Canonical ADR:** `docs/architecture/decisions/0003-geocoding-without-spatialite.md`

Decision: Do not adopt SpatiaLite or PostGIS. Store coordinates as decimal latitude and longitude fields and perform modest distance calculations in Python.

Rationale: The project needs simple nearby parish discovery, has a small dataset, and prioritizes low contributor friction.

Consequences: Advanced GIS features would require revisiting this decision.

### SQLite as the primary database

**Date:** 2025-11-16  
**Status:** Decided  
**Canonical ADR:** `docs/architecture/decisions/0002-postgres-to-sqlite.md`

Decision: Use SQLite instead of PostgreSQL as the primary database.

Rationale: The project is small, read-heavy, low-concurrency, cost-sensitive, and benefits from simple local setup and deployment.

Consequences: Brief deploy downtime and limited write concurrency are accepted trade-offs. Revisit if traffic, write concurrency, advanced indexing, or SLA needs grow.

### Record architecture decisions with ADRs

**Date:** 2025-11-16  
**Status:** Decided  
**Canonical ADR:** `docs/architecture/decisions/0001-record-architecture-decisions.md`

Decision: Record architecture decisions using lightweight ADRs.

Rationale: Future sessions should preserve the reason behind hard-to-reverse architecture choices.

Consequences: New architecture decisions should be added under `docs/architecture/decisions/` and summarized here when they affect ongoing agent context.

## Open Discussions

No open discussions recorded yet.

## Decision Template

```markdown
### Title

**Date:** YYYY-MM-DD  
**Status:** Decided

Decision:

Rationale:

Consequences:
```
