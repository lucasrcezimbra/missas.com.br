# Worklog

Operational progress for the project.

Update this file when a meaningful milestone is completed. The worklog is not a full history of every edit. It is the project memory that helps future sessions understand what changed, why it matters, and how it was verified.

## Done

Add newest entries at the top.

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
