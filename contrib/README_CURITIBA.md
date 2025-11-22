# Curitiba Scraper and Import Scripts

This directory contains scripts for scraping Mass schedules from the Arquidiocese de Curitiba website and importing the data into Django.

## Files

### `scraper_curitiba.py`
Scrapy spider that extracts parish data from https://arquidiocesedecuritiba.org.br/paroquias/

**Current status:** Extracts parish names and URLs. Mass schedule data requires JavaScript rendering.

**Output:** JSONL file with parish information

### `curitiba_parishes_into_django.py`
Import script that creates Parish records in the database from scraped data.

**Input:** `curitiba_parishes.jsonl`

**What it does:**
- Creates Parish records for Curitiba/PR
- Creates a Source record for tracking data origin
- Skips duplicate parishes (based on slug)

### `curitiba_schedules_into_django.py`
Import script that creates both Parish and Schedule records from scraped data.

**Input:** `curitiba_schedules.jsonl`

**What it does:**
- Creates Parish records for Curitiba/PR
- Parses day and time information
- Creates Schedule (Mass) records
- Creates a Source record for tracking data origin
- Skips records without schedule data

**Note:** This script requires the scraper to be enhanced with JavaScript rendering to extract schedule data.

## Usage

### 1. Run the Scraper

```bash
# Extract parish data (no schedules yet - requires JavaScript)
poetry run scrapy runspider contrib/scraper_curitiba.py -o contrib/curitiba_parishes.jsonl
```

### 2. Import Parish Data

```bash
# Import parishes into Django
poetry run python contrib/curitiba_parishes_into_django.py
```

### 3. Import Schedule Data (Future)

Once the scraper is enhanced with JavaScript rendering:

```bash
# Run scraper with full schedule extraction
poetry run scrapy runspider contrib/scraper_curitiba.py -o contrib/curitiba_schedules.jsonl

# Import schedules into Django
poetry run python contrib/curitiba_schedules_into_django.py
```

## Prerequisites

- PostgreSQL database must be running and configured
- Environment variables must be set (see `.env` file)
- Curitiba city must exist in the database:
  ```python
  City.objects.get(name="Curitiba", state__short_name="PR")
  ```

## Adding JavaScript Rendering to Scraper

To extract Mass schedules, the scraper needs JavaScript rendering support:

1. **Install scrapy-playwright:**
   ```bash
   poetry add scrapy-playwright
   playwright install
   ```

2. **Update `scraper_curitiba.py`:**
   - Uncomment the `custom_settings` section
   - Add Playwright request meta to `parse_parish`
   - Add wait conditions for AJAX-loaded content

3. **Example Playwright request:**
   ```python
   yield scrapy.Request(
       url,
       callback=self.parse_parish,
       meta={
           "playwright": True,
           "playwright_page_methods": [
               PageMethod("wait_for_selector", "table tr"),
           ],
       },
   )
   ```

## Data Format

### Parish JSONL Format
```json
{
  "parish_name": "Paróquia São Francisco de Paula",
  "parish_url": "https://arquidiocesedecuritiba.org.br/paroquia/paroquia-sao-francisco-de-paula/",
  "slug": "paroquia-sao-francisco-de-paula",
  "days": null,
  "times": null,
  "note": "Schedule data requires JavaScript rendering"
}
```

### Schedule JSONL Format (Future)
```json
{
  "parish_name": "Paróquia São Francisco de Paula",
  "parish_url": "https://...",
  "slug": "paroquia-sao-francisco-de-paula",
  "days": "Terça-feira, Quarta-feira, Quinta-feira, Sexta-feira",
  "times": "18:30"
}
```

## Troubleshooting

### Import Script Errors

**"Curitiba city not found"**
- Ensure the city exists: `City.objects.get(name="Curitiba", state__short_name="PR")`
- Run migrations: `poetry run python manage.py migrate`
- Load fixtures if available

**"IntegrityError: duplicate key"**
- Parish already exists in database
- Check `NAMES_MAPPER` in script to map parish name variations
- Script will skip duplicates and continue

**"No schedule data found"**
- Expected behavior - scraper needs JavaScript rendering enhancement
- Use `curitiba_parishes_into_django.py` to import parishes only

## Related Files

- `scraper_natal.py` - Reference implementation for Natal/RN
- `natal_contracts_into_django.py` - Similar import script for contact data
- `missas/core/models.py` - Django model definitions
