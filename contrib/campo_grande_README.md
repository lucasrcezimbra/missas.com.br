# Campo Grande (MS) - Data Import Scripts

This directory contains scrapers and import scripts for the Archdiocese of Campo Grande (MS).

## Overview

- **scraper_campo_grande.py**: Scrapes mass schedules from the archdiocese website
- **scraper_campo_grande_contact.py**: Scrapes parish contact information
- **campo_grande_schedules_into_django.py**: Imports scraped schedules into Django models
- **campo_grande_contacts_into_django.py**: Imports scraped contacts into Django models

## Step-by-Step Usage

### 1. Scrape Mass Schedules

```bash
poetry run scrapy runspider contrib/scraper_campo_grande.py -o contrib/campo_grande_schedules.jsonl
```

This will scrape ~750 mass schedules from https://arquidiocesedecampogrande.org.br/horarios-de-missas/

### 2. Scrape Parish Contacts (Optional)

**Note**: This requires the `OPENAI_API_KEY` environment variable set with a valid OpenAI API key.

```bash
export OPENAI_API_KEY="your-api-key-here"
poetry run scrapy runspider contrib/scraper_campo_grande_contact.py -o contrib/campo_grande_contacts.jsonl
```

This will scrape contact information from 116 parish pages (108 paróquias + 8 santuários).

### 3. Import Schedules into Django

**Prerequisites**:
- Database must be set up and migrated
- The state 'MS' (Mato Grosso do Sul) must exist in the database (it should be loaded from fixtures)

```bash
poetry run python contrib/campo_grande_schedules_into_django.py
```

This script will:
- Create the city "Campo Grande/MS" if it doesn't exist
- Create parishes as needed
- Import all mass schedules
- Link schedules to the archdiocese website as source

### 4. Import Contacts into Django (Optional)

```bash
poetry run python contrib/campo_grande_contacts_into_django.py
```

This script will:
- Create parishes if they don't exist
- Import contact information (phone, WhatsApp, email, social media)
- Link contacts to parishes

## Data Structure

### Schedules (campo_grande_schedules.jsonl)

```json
{
  "parish_name": "PARÓQUIA NOSSA SENHORA DA GUIA",
  "type": "Missa",
  "day": "Domingo",
  "time": "09:30",
  "notes": null
}
```

### Contacts (campo_grande_contacts.jsonl)

```json
{
  "parish_name": "Paróquia Exemplo",
  "state": "Mato Grosso do Sul",
  "city": "Campo Grande",
  "email": "mail@example.com",
  "facebook": "paroquiaexemplo",
  "instagram": "paroquiaexemplo",
  "phone": "+5567000000000",
  "phone2": "+5567000000000",
  "whatsapp": "+5567000000000"
}
```

## Troubleshooting

### State 'MS' not found

If you get the error "State 'MS' (Mato Grosso do Sul) not found in database", you need to load the states fixture:

```bash
poetry run python manage.py loaddata states
```

### OpenAI API Key

The contact scraper uses GPT-4o to extract structured data from parish pages. If you don't have an API key, you can:
- Skip the contact scraping step
- Manually extract contact information
- Use a different LLM provider by modifying the scraper

## Notes

- The schedules scraper works without any API keys
- Both import scripts are idempotent - running them multiple times won't create duplicates
- Parish names are normalized (converting "PARÓQUIA" to "Paróquia" for consistency)
- Schedules are linked to the source URL for transparency
