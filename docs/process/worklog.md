# Worklog

Operational progress for the project.

Update this file when a meaningful milestone is completed. The worklog is not a full history of every edit. It is the project memory that helps future sessions understand what changed, why it matters, and how it was verified.

## Done

Add newest entries at the top.

### 2026-09-10–12 — Public, cached parish facts API for WhatsApp outreach

Implemented `GET /api/v0/parishes` with Django Ninja. The API exports only
parishes with recorded WhatsApp contacts and preserves per-schedule verification
dates and source attribution, without inventing a parish-level verification
timestamp or verifier relationship. The proxy-model migration changes no
business table. Sending, outreach policy, and write-back remain outside this API.

After review, the Navigator chose public access and the existing 24-hour site
cache, replacing the initial shared-secret and signed-cursor design. Ninja's
built-in limit/offset pagination orders parishes by ID and caps pages at 100
items. Schemas live beside the endpoint. The [API contract](../api.md) owns the
wire format and documents offset mutation and cross-page cache-staleness limits.

Final verification: 19 API/site-cache tests and `make lint` passed. A disposable
real HTTP API → `whatsapp-missas` CLI check verified 101 qualifying parishes over
two pages, four exclusions, cached responses, and all three simulated outcomes.
The initial implementation had passed 139 tests; the full suite after these
revisions remains unverified because its rerun stalled under orb memory pressure
and was stopped. Existing `datetime.utcnow()` deprecation warnings remain.
No production database was changed and nothing was deployed.

### 2026-09-10 — Legacy WhatsApp extraction workflow retired

Removed the WPPConnect extractor, LLM-assisted WhatsApp parser, old LLM contact scraper, Scrapy spider, and their JavaScript and Python dependencies. The legacy workflow is being retired because work has started on a replacement WhatsApp extraction workflow.

Previously generated data and the standalone Caicó collection script remain available.

Verified with dependency locking, the test suite, lint checks, and searches for stale integration references.

### 2026-08-26 — Python tooling migrated to uv

Replaced Poetry with uv for dependency locking, local development, CI, and Render deployment. Preserved separate development and scraper dependency groups while keeping production installs limited to runtime dependencies.

This reduces environment setup and dependency installation time while retaining reproducible builds through the committed lock file.

Verified with a frozen dependency sync, the test suite, lint checks, and a production-style build.

### 2026-06-15 — Ariad local instance installed

Added Ariad project memory files under `docs/project/`, `docs/process/`, and `docs/product/`. Replaced legacy agent instruction files with `AGENTS.md` as the agent-facing entry point.

This matters because future agent sessions can start from shared context: project purpose, product principles, roadmap, decisions, debt ledger, and local development rules.

Verified by inspecting the generated files and reviewing the Git diff. No automated tests were needed because this was a documentation-only change.

## Next

- Use the continuous Ariad workflow on the next small real change.
- Keep roadmap and worklog updates concise; update only when project memory changes.
