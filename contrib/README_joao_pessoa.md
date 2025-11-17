# João Pessoa (PB) Scraper

Scrapers for extracting parish Mass and confession schedules from Arquidiocese da Paraíba.

**Website:** https://arquidiocesepb.org.br/
**Schedule Page:** https://arquidiocesepb.org.br/horario-de-missas-e-confissoes/

## Challenge

The website uses **Ninja Tables** WordPress plugin (table ID: 770) which loads data dynamically via JavaScript. The table data is not present in the static HTML and requires JavaScript rendering to extract.

## Available Scrapers

### 1. scraper_joao_pessoa.py (Recommended)

Full-featured scraper using **scrapy-playwright** for JavaScript rendering.

**Setup:**
```bash
poetry install --with scrapers
poetry run playwright install chromium
```

**Usage:**
```bash
poetry run scrapy runspider contrib/scraper_joao_pessoa.py -o output.jsonl
```

**Features:**
- Renders JavaScript to access dynamic table content
- Automatically extracts table headers and data
- Identifies parish names from table content
- Outputs structured JSONL format

**Note:** May timeout in some environments due to network/proxy issues. If this happens, use the simple scraper or manual extraction.

### 2. scraper_joao_pessoa_simple.py (Fallback)

Simple scraper for investigating the page structure without JavaScript rendering.

**Setup:**
```bash
poetry install --with scrapers
```

**Usage:**
```bash
poetry run python contrib/scraper_joao_pessoa_simple.py
```

**Output:**
- Confirms Ninja Tables usage
- Saves HTML to `/tmp/joao_pessoa.html` for manual inspection
- Provides recommendations for data extraction

## Alternative Data Extraction Methods

If the automated scrapers don't work in your environment:

1. **Manual Browser Extraction:**
   - Open https://arquidiocesepb.org.br/horario-de-missas-e-confissoes/ in a browser
   - Wait for the table to load
   - Copy the table data manually or use browser DevTools

2. **Browser DevTools:**
   - Open the page in a browser
   - Open DevTools (F12) → Network tab
   - Look for AJAX requests to `wp-admin/admin-ajax.php`
   - Find the request that loads table data
   - Copy the JSON response

3. **Contact Diocese:**
   - Request a data export or API access from the archdiocese
   - Contact: (83) 3133-1000

## Dependencies Added

This scraper required adding the following dependencies:

```toml
[tool.poetry.group.scrapers.dependencies]
scrapy-playwright = "^0.0.44"
beautifulsoup4 = "^4.14.2"
```

## Comparison with Other Scrapers

- **Natal scraper:** Uses basic Scrapy for static HTML (pagination)
- **Caicó scraper:** Uses requests + BeautifulSoup for simple pages
- **João Pessoa scraper:** Uses Scrapy + Playwright for JavaScript-rendered content
