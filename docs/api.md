# Parish facts API

A read-only Django Ninja API for the `whatsapp-missas` application. It lists all
parishes with **recorded, non-whitespace `Contact.whatsapp` information**. Ordinary
phone numbers, Instagram-only contacts, and missing contacts do not qualify.
Presence does not establish reachability or permission to send.

## Request

```http
GET /api/parishes?limit=100&cursor=...
X-API-Key: <shared secret>
```

- No trailing slash. `limit` defaults to 100; valid range is 1–100.
- Omit `cursor` for the first page. Pass the returned `next_cursor` unchanged for
  subsequent pages; stop when it is `null`.
- Configure `MISSAS_API_SHARED_SECRET` privately in the server and caller.
  Missing, empty, or whitespace-only server configuration refuses all access.
- Only `X-API-Key` is accepted, not Bearer auth, cookies, or query-string keys.
- Use HTTPS outside local loopback development. Never put credentials in URLs,
  source control, logs, or workflow payloads. Rotate by updating both environments.
- Responses bypass the site's page cache and have private/no-store headers.
  Configure any CDN/reverse proxy to bypass caching for `/api/*` too.
- There is no write method, send side effect, verification mutation, freshness
  cutoff, outreach-history filter, or `verified_before` requirement.
- Interactive docs and the public OpenAPI endpoint are disabled. The explicit
  response models are in `missas/api/schemas.py`.

## Response

Illustrative synthetic data:

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
  "next_cursor": null
}
```

### What the fields mean

- IDs are existing stable database IDs. `contact` is the parish's current
  one-to-one contact, not necessarily its previous contributor.
- `mass_schedules` contains only Mass schedules, ordered by day/time/ID. It may
  be empty. Day 0 is Sunday, through day 6 Saturday. Times are recorded local
  schedule times, without an invented timezone conversion.
- **Verification belongs to each schedule:** `verified_at` is a nullable date,
  not a timestamp and not the row's `updated_at`. Missas has no parish-level
  verification date; the API deliberately does not invent one.
- `source` is the recorded attribution shown by the UI: ID, type (`site` or
  `whatsapp`), free-text description, and optional link. There is no structured
  verifier-contact relationship. Do not parse it as the next recipient.
- `source` and `location` can be null. `location_name` preserves the legacy text
  location when no structured location exists.
- There are no recorded consent/cooldown/contact-restriction fields in the
  current model. Their omission is **not** a claim of consent. Email, ordinary
  phone numbers, and unrelated internal fields are intentionally not exported.

## Pagination and errors

Pages use increasing parish IDs rather than offsets. A signed cursor expires
one hour after issuance. It also carries a fingerprint of the qualifying IDs:
adding/removing a parish or gaining/losing a WhatsApp contact during traversal
returns `409`, including changes behind the cursor. The caller must discard its
partial scan and start again; it must not treat partial pages as a complete list.
Repeated scans are not authorization to repeat outreach.

This is **membership consistency**, not a frozen cross-request data snapshot.
Changes to schedules, names, sources, or a still-nonempty contact number may be
observed on later pages. A single page's database reads share one transaction.
The caller remains responsible for freezing and approving its chosen recipient
and message before sending.

To detect membership changes without server-side snapshot storage or writes,
each page streams all qualifying IDs into a hash, then loads at most `limit + 1`
parishes and their Mass schedules. This is O(number of qualifying parishes) per
page, with bounded ID-buffer memory and a fixed query count. Revisit if catalogue
size or scan frequency makes this material; there is no new snapshot table.

| Status | Meaning |
| --- | --- |
| 200 | Page, including an empty final/first page |
| 400 | Invalid, tampered, or expired cursor; restart without it |
| 401 | Missing/incorrect key or disabled server configuration |
| 405 | Unsupported HTTP method |
| 409 | Qualifying membership changed; discard partial scan and restart |
| 422 | Invalid query value (e.g. page size outside 1–100) |

Errors use `{"detail": ...}`. The detail is Portuguese text for 400/401/409 and
Ninja's validation structure for 422. Branch on status, not translated wording.
The API returns neither credentials nor raw cursor-signature exceptions. Sentry
scrubbing includes this header/configuration name and does not capture frame
local variables. Infrastructure must likewise avoid logging request headers.

## Local end-to-end check

From the Missas repository, install and apply the generated **proxy-model-only**
migration (it creates no business table and changes no existing parish data):

```bash
uv sync --frozen
uv run python manage.py migrate
```

Choose a new development-only secret privately and export it in both the server
and client terminals, without putting its value in shell history:

```bash
read -rs -p 'Development API secret: ' MISSAS_API_SHARED_SECRET; echo
export MISSAS_API_SHARED_SECRET
```

Start the server, using your normal local database configuration:

```bash
SENTRY_DSN='' uv run python manage.py runserver 127.0.0.1:8000
```

In the client terminal (the stdin header avoids exposing the key in curl's
process arguments):

```bash
printf 'X-API-Key: %s\n' "$MISSAS_API_SHARED_SECRET" |
  curl --fail-with-body --silent --show-error --header @- \
    'http://127.0.0.1:8000/api/parishes?limit=1'

curl --silent --show-error --include \
  'http://127.0.0.1:8000/api/parishes?limit=1'
```

The first request should return 200 and one qualifying parish (or an empty list
if the local database has none). The second must return 401 even immediately
after the authorized request. Follow `next_cursor` using URL encoding until
null, and compare verification/source fields with the parish UI. Do not paste
real contact responses into public logs. These reads send no WhatsApp messages.

Automated checks use isolated test databases, including a real local HTTP server:

```bash
SENTRY_DSN='' SECRET_KEY=local-test-only DATABASE_URL=sqlite:///:memory: \
  uv run pytest -q --maxfail=5 missas/api/tests
```

`whatsapp-missas` integration, pairing, sending, and deployment are separate work;
this API check alone does not establish a successful live outreach.
