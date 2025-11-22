# São Luís (MA) Scrapers and Data Import

This directory contains scrapers and import scripts for the **Arquidiocese de São Luís do Maranhão**.

## Scrapers

### Option 1: Unified Scraper (Recommended)

The unified scraper collects both schedules and contact information in a single pass, making it more efficient.

```bash
poetry run scrapy runspider contrib/scraper_sao_luis_unified.py \
  -O contrib/sao_luis_unified.jsonl
```

**Output format:**
```json
{
  "parish_id": "59",
  "parish_name": "Paróquia São Pedro Apóstolo",
  "state": "Maranhão",
  "times": ["Terça e quinta-feira 19h30", "Domingo 7h e 19h30", ...],
  "contact_info": {
    "city": "Raposa",
    "phone": "+5598999701096",
    "email": "paróquia.s.pedroraposa@gmail.com",
    "instagram": "paroquia_saopedro_raposa_ma"
  },
  "url": "https://arquislz.org.br/paroquia/?paroquiaid=59"
}
```

### Option 2: Separate Scrapers

If you need to run scrapers separately:

**Schedules only:**
```bash
poetry run scrapy runspider contrib/scraper_sao_luis.py \
  -O contrib/sao_luis_schedules.jsonl
```

**Contacts only:**
```bash
poetry run scrapy runspider contrib/scraper_sao_luis_contact.py \
  -O contrib/sao_luis_contacts.jsonl
```

## Importing Data into Django

### Prerequisites

1. Ensure the database is set up and migrations are applied:
   ```bash
   poetry run python manage.py migrate
   ```

2. Load the state and city fixtures (if not already loaded):
   ```bash
   poetry run python manage.py loaddata states cities
   ```

3. Verify that Maranhão (MA) state and São Luís city exist:
   ```bash
   poetry run python manage.py shell
   >>> from missas.core.models import State, City
   >>> State.objects.get(short_name="MA")
   >>> City.objects.get(name="São Luís", state__short_name="MA")
   ```

### Import Scripts

**For unified scraper output:**
```bash
poetry run python contrib/sao_luis_into_django.py
```

This script:
- Creates parishes if they don't exist
- Creates or updates contact information
- Uses São Luís as the default city

**For separate contact scraper output:**
```bash
poetry run python contrib/sao_luis_contacts_into_django.py
```

### Notes

- The scripts use `get_or_create` for parishes to avoid duplicates
- Contact information is updated using `update_or_create` to keep data fresh
- Parish names are automatically slugified for URLs
- If a city is not found, it defaults to São Luís, MA

### Schedule Data

The scraped `times` field contains raw text data extracted from parish pages. This includes:
- Mass times (e.g., "Domingo 7h e 19h30")
- Confession times
- Special celebrations
- Contact details mixed in

**Manual processing required:** Due to the unstructured nature of this data, schedule times need to be parsed and structured manually or with additional processing before importing into the `Schedule` model.

To create schedules, you would need to:
1. Parse the times text to extract day of week, time, and type (mass/confession)
2. Create `Schedule` objects with the appropriate fields

Example manual approach:
```python
from missas.core.models import Parish, Schedule, Source

parish = Parish.objects.get(name="Paróquia São Pedro Apóstolo")
source = Source.objects.get(type="site", description__icontains="são luís")

Schedule.objects.create(
    parish=parish,
    day=Schedule.Day.TUESDAY,  # 2
    start_time="19:30",
    type=Schedule.Type.MASS,
    source=source
)
```

## Environment Variables

The contact scraper requires an OpenAI API key for LLM-based parsing:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

Or add it to your `.env` file:
```
OPENAI_API_KEY=your-api-key-here
```

## Troubleshooting

**403/503 errors from website:**
- The scrapers include delays and proper headers
- If still blocked, increase `DOWNLOAD_DELAY` in the scraper settings

**City not found:**
- Verify the city exists in the database
- The script will default to São Luís if city lookup fails
- Check spelling and accents match the fixtures

**Duplicate parishes:**
- Check the slug field for conflicts
- May need to adjust parish names manually
