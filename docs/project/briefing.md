# Project Briefing

Stable context for Missas.com.br.

## Purpose

Missas.com.br helps Catholic faithful find Mass and confession schedules for parishes in Brazil. It provides searchable parish, location, contact, and schedule data, with a focus on practical access for people deciding where and when to attend.

## Current State

The project is an existing Django web application with fixtures, tests, templates, scraper scripts, and manual WhatsApp-assisted data collection. The application uses SQLite, Bootstrap 5, HTMX, FontAwesome, Whitenoise, Gunicorn, and Sentry.

Current work should preserve reliability, data quality, low operational cost, and simple local development.

## Architecture Premises

- Backend: Django 5.2 on Python 3.12.
- Database: SQLite is the source of truth.
- Deployment: Gunicorn and Whitenoise, currently shaped for Render and possible future VPS hosting.
- Frontend: Bootstrap 5, HTMX, FontAwesome, project CSS, JavaScript required.
- Data collection: Scrapy for diocesan websites; manual WhatsApp extraction and LLM-assisted parsing for schedule updates.
- Monitoring: Sentry.
- Package management: uv.
- Domain model: `State`, `City`, `Parish`, `Location`, `Contact`, `Schedule`, `Source`, and `ContactRequest`.
- Architecture decisions are recorded in `docs/architecture/decisions/` and summarized in `docs/project/decisions.md`.

## Product Premises

- Primary users are Catholic faithful in Brazil looking for Mass or confession times.
- Users should be able to trust schedule data, source context, and verification dates when available.
- Search and navigation should work well on mobile devices.
- Brazilian geography, phone formats, time formats, and Catholic terminology matter.
- User-facing product text should be Brazilian Portuguese.

## Constraints

- All Python and Django commands must run through uv.
- Do not introduce database queries inside loops.
- Do not hand-write Django migrations; generate them with Django CLI.
- Do not add inline CSS; use classes and static stylesheets.
- Keep contributor setup simple: clone, install, run.
- Avoid infrastructure choices that add recurring cost or native dependency friction unless the product need is strong.
- Protect contact data, especially WhatsApp numbers.

## Operating Notes

Common commands:

```bash
make install
make test
make lint
make coverage
make dev
make dbdump
make dbload
```

Run direct Python or Django commands with `uv run`.

For user-visible UI work, run the app, capture a Playwright screenshot at 1920x1080, and include `[render preview]` in the PR title.

## Glossary

- **Parish:** Catholic church or parish community with schedules and contact data.
- **Schedule:** Mass or confession time, including day, time, type, location, observation, source, and verification when available.
- **Source:** Origin of schedule data, such as website scraping or WhatsApp contact.
- **Verification:** Evidence or timestamp that schedule data was confirmed recently.
- **Navigator:** Human project owner who holds product judgment and acceptance.
- **Driver:** Agent operating the repository under Ariad.
