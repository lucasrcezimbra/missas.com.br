# Worklog

Operational progress for the project.

Update this file when a meaningful milestone is completed. The worklog is not a full history of every edit. It is the project memory that helps future sessions understand what changed, why it matters, and how it was verified.

## Done

Add newest entries at the top.

### 2026-09-10 — Read-only parish facts API for WhatsApp outreach

Implemented `GET /api/parishes` with Django Ninja 1.7.0, as requested by the
Navigator. The API exports only parishes with recorded WhatsApp contacts, and
preserves actual per-schedule verification dates and source attribution rather
than inventing a parish-level verification timestamp or verifier relationship.
The [API contract and local test guide](../api.md) own the wire format and limits.

The environment-configured `X-API-Key` fails closed; API responses bypass the
site-wide cache. Signed keyset cursors detect qualifying-membership changes and
require a fresh scan rather than silently skipping parishes. The proxy-model
migration changes no business table. There is no outreach policy, sending,
write-back, or deployment in this slice; `whatsapp-missas` is separate agent work.
The Navigator explicitly waived routine checkpoints for this implementation.

Implemented incrementally with failing behavior tests followed by minimal code.
Verification: 139 tests passed, including a real local HTTP scan and authorization
check; the API has 100% statement/branch coverage. Focused pre-commit hooks, Django
system checks, migration drift checks, and dead-fixture checks passed. Existing
`datetime.utcnow()` deprecation warnings remain in the city view, outside this
change. No live API, private parish database, or WhatsApp account was used for
validation. Intercom was unavailable; the contract is shared through `docs/api.md`.

### 2026-08-26 — Python tooling migrated to uv

Replaced Poetry with uv for dependency locking, local development, CI, and Render deployment. Preserved separate development and scraper dependency groups while keeping production installs limited to runtime dependencies.

This reduces environment setup and dependency installation time while retaining reproducible builds through the committed lock file.

Verified with a frozen dependency sync, the test suite, lint checks, and a production-style build.

### 2026-06-15 — Ariad local instance installed

Added Ariad project memory files under `docs/project/`, `docs/process/`, and `docs/product/`. Replaced legacy agent instruction files with `AGENTS.md` as the agent-facing entry point.

This matters because future agent sessions can start from shared context: project purpose, product principles, roadmap, decisions, debt ledger, and local development rules.

Verified by inspecting the generated files and reviewing the Git diff. No automated tests were needed because this was a documentation-only change.

## Next

- Use the Ariad lifecycle on the next small real change.
- Keep roadmap and worklog updates concise; update only when project memory changes.
