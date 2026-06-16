# Local Development Guide

This is the project-specific operating contract for agentic development in Missas.com.br.

## Relationship to Ariad

This project uses Ariad as its human-agent development method. Ariad is the canonical method; this file is the local instance for this repository.

When Ariad and this local guide differ, follow this local guide for project-specific work and surface the difference during the coherence check.

## Driver and Navigator

The agent is the **Driver**. The human is the **Navigator**.

The Driver reads context, proposes plans, changes files, runs checks, prepares validation routes, updates documentation, and stops at checkpoints.

The Navigator holds intent, trade-offs, product judgment, and acceptance.

## Project Commands

All Python and Django commands must run through Poetry.

```bash
# install dependencies and seed local data
make install

# run tests
make test
poetry run pytest

# run lint and dead-fixture checks
make lint

# run coverage
make coverage

# run app locally with migrations
make dev

# run production-like process locally
make run

# migrate database
poetry run python manage.py migrate

# dump and load fixture data
make dbdump
make dbload

# run scraper example
poetry run scrapy runspider contrib/scraper_natal.py -o natal.jsonl
```

Do not run Python, Django, pytest, or Scrapy directly without `poetry run`, except through `make` targets that already use Poetry.

## Verification

Verification depends on the change:

- Behavior changes: run relevant `poetry run pytest ...` tests or `make test`.
- Lint-sensitive changes: run `make lint` when practical, especially before commit.
- Django schema changes: generate migrations with Django CLI, run migrations, and test the affected behavior.
- Data fixture changes: verify `make dbload` or targeted `loaddata` behavior when relevant.
- UI changes: run `make dev`, inspect locally, capture a Playwright screenshot at 1920x1080, and include it in PR comments.
- Docs-only changes: inspect the diff; automated tests are optional unless links, commands, or generated docs are affected.

Navigator validation routes should include commands, URLs or files to inspect, expected observations, pass condition, and fail condition.

## Documentation Rules

Update documentation when project memory changes, not for every edit.

Use these surfaces:

- `README.md` for contributor-facing setup and usage.
- `docs/project/briefing.md` for stable project context.
- `docs/project/decisions.md` for project-shaping decisions and ADR summaries.
- `docs/architecture/decisions/` for canonical architecture decisions.
- `docs/project/roadmap/index.md` for active focus and planned work.
- `docs/project/debt.md` for structural debt that should outlive one story.
- `docs/process/development-guide.md` for local operating rules.
- `docs/process/worklog.md` for meaningful completed milestones.
- `docs/product/principles.md` for product trade-off principles.

Keep docs concise and in English. User-facing product strings should remain Brazilian Portuguese.

## Roadmap Taxonomy

Use Ariad's default taxonomy unless the project explicitly adapts it:

- Value / CV: major delivery stage with clear impact.
- Delivery Story: coherent delivery arc inside a Value / CV.
- User Story: atomic user-observable delivery verified end to end.
- Technical Story: internal capability needed by a Delivery Story.
- Task: concrete work inside a User Story or Technical Story.
- Maintenance: legitimate work that may sit outside roadmap structure.

Do not inflate maintenance into the roadmap just to make it visible.

Use Ariad's default new-work codes unless this project explicitly adapts them: `CV<N>`, `DS<N>`, `US<N>`, and `TS<N>`.

Use Ariad's default roadmap states: `Planned`, `Active`, `Blocked`, `Validated`, `Done`, `Deferred`, and `Dropped`.

## Django and Python Rules

- Prefer function-based views.
- Use Django's built-in authentication patterns when auth is needed.
- Use managers and querysets when they make domain queries clearer.
- Do not hand-write migrations; use Django CLI.
- Avoid type hints in project Python code.
- Follow Ruff rules configured in `pyproject.toml`.
- Avoid useless comments that restate code; explain why when needed.
- Never do database queries inside loops. Use `select_related`, `prefetch_related`, annotations, or bulk operations.
- Assert against whole Pydantic or Django model objects when equality gives clearer tests; avoid decomposing fields unnecessarily.
- Prefer real backends and model-bakery for tests. Mock external services and I/O boundaries only when needed.

## Frontend Rules

- Use Bootstrap 5 components, HTMX, FontAwesome, and project CSS consistently.
- JavaScript is required; no no-JavaScript support path is needed.
- Avoid inline CSS. Use classes and external stylesheets.
- Keep pages responsive for mobile users.
- For UI changes, PR title must include `[render preview]`.
- For UI changes, take a Playwright screenshot at 1920x1080 and add it to PR comments.

## Data and Domain Rules

- State codes should use official Brazilian abbreviations.
- City names, parish names, and public text should preserve accents.
- Times should use 24-hour format for display.
- Public date formatting should use Brazilian convention when shown to users.
- Phone numbers should follow Brazilian formats, usually with country code `+55`.
- Protect contact data, especially WhatsApp numbers.
- Track schedule sources and verification dates when available.

## Expand and Collapse

Use expand when work is blocked by ambiguity: separate concerns, name options, clarify scope, or split work into smaller stories.

Use collapse when work is fragmented: relate parts, update status, name emergent value, close a story, or prepare a release boundary.

## User and Technical Story Lifecycle

For non-trivial work, follow the Ariad lifecycle:

1. Read and orient.
2. Plan, including scope, acceptance behavior, risks, and validation route.
3. Stop for Navigator confirmation.
4. Implement within scope.
5. Test and validate.
6. Present automated evidence and Navigator validation route.
7. Review refactoring, debt paid, debt introduced, and documentation needs.
8. Stop for Navigator confirmation.
9. Update docs and run coherence check.
10. Propose history action.
11. Stop before commit or push unless local policy says otherwise.

For trivial low-risk changes, compress the lifecycle but still state what changed and how it was verified.

## Technical Debt Tracking

Use `docs/project/debt.md` when debt should outlive one story's review notes.

During review, name:

- debt paid;
- new debt introduced;
- debt carried forward;
- revisit trigger;
- whether a Debt Ledger entry should be created or updated.

## Navigator Preferences

- **Commit policy:** commit after a coherent story or meaningful change is validated and accepted.
- **Push policy:** ask before pushing to a shared remote.
- **Checkpoint compression:** full checkpoints for non-trivial work; compressed checkpoints for trivial low-risk changes.
- **Documentation detail:** smallest update that keeps project memory coherent.
- **Worklog policy:** record meaningful milestones, not every edit.
- **Branch/PR habits:** include `[render preview]` in UI PR titles; include screenshots for UI changes.

## Commit and Release Rules

When a commit is requested:

- Run relevant validation first.
- Stage only relevant files.
- Use a descriptive commit message that explains why.
- If pre-commit fails, fix reported issues before retrying.
- Ask before pushing.

If work creates a release boundary, name the likely boundary explicitly: Value / CV, Delivery Story, User Story, Technical Story, or Maintenance.

## Local Exceptions

- SQLite is intentional for this project. Do not replace it with PostgreSQL or a GIS database without a new decision.
- Geocoding should avoid SpatiaLite/PostGIS unless product needs change enough to revisit the ADR.
- JavaScript is required; do not spend effort on no-JavaScript fallback behavior.
