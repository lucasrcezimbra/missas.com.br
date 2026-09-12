# Parish facts API

The public, read-only Django Ninja endpoint lists parishes with recorded,
non-whitespace `Contact.whatsapp` information. Ordinary phone numbers,
Instagram-only contacts, and missing contacts do not qualify. Presence does not
establish reachability or permission to send.

## Request

```http
GET /api/v0/parishes?limit=100&offset=0
```

- No trailing slash and no authentication are required.
- `limit` defaults to 100 and is capped at 100; `offset` defaults to 0.
- Responses use the site's 24-hour cache. Each complete query string has a
  separate cache entry, so distinct `limit`/`offset` pages do not collide.
- There is no write method, send side effect, verification mutation, freshness
  cutoff, outreach-history filter, or `verified_before` requirement.
- Interactive docs and the public OpenAPI endpoint remain disabled.
- Endpoint and response schemas are colocated in `missas/api/api.py`.

## Response

```json
{
  "items": [
    {
      "id": 12,
      "name": "Paróquia Exemplo",
      "city": "Natal",
      "state": "RN",
      "contact": {"id": 7, "whatsapp": "+5511999990001"},
      "mass_schedules": [
        {
          "id": 41,
          "day": 0,
          "start_time": "08:00:00",
          "end_time": null,
          "observation": "",
          "verified_at": "2025-01-02",
          "location_name": "",
          "location": {"id": 3, "name": "Matriz", "address": "Praça Central"},
          "source": {
            "id": 9,
            "type": "whatsapp",
            "description": "Recorded contributor",
            "link": null
          }
        }
      ]
    }
  ],
  "count": 1
}
```

`count` is the total number of qualifying parishes, not the number in the page.
Parishes are ordered by database ID. Mass schedules include only Masses and are
ordered by day, start time, and ID. Day 0 is Sunday through day 6 Saturday.

Verification belongs to each schedule: `verified_at` is nullable and is not a
parish-level timestamp. `source` and `location` can be null;
`location_name` preserves legacy location text. Contact presence is not consent.
Email, ordinary phone numbers, and unrelated internal fields are not exported.

## Pagination and caching limitations

To read all results, increment `offset` by the number of returned items until it
reaches `count`. Offset pagination is not a snapshot: inserts and deletions while
a scan is in progress can shift rows, causing duplicates or omissions. Updates
may also be hidden by independent 24-hour cache entries, so pages fetched at
different times can reflect different dataset versions. Consumers that require a
stable scan must copy the results and tolerate/reconcile these mutations.

| Status | Meaning |
| --- | --- |
| 200 | Page, including an empty page |
| 405 | Unsupported HTTP method |
| 422 | Invalid `limit` or `offset` |

## Local check

```bash
SENTRY_DSN='' SECRET_KEY=local-test-only ALLOWED_HOSTS='*' \
  DATABASE_URL=sqlite:///:memory: \
  uv run pytest -q --maxfail=5 missas/api/tests
```

For a manual read, start the development server and request
`/api/v0/parishes?limit=1&offset=0`. No API secret or new Render environment value is
needed. This API does not send WhatsApp messages or update parish data.
