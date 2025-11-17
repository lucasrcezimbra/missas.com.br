# João Pessoa (PB) Scrapers

Scrapers for extracting parish information and Mass/confession schedules from Arquidiocese da Paraíba.

**Website:** https://arquidiocesepb.org.br/
**Digital Annual:** http://162.241.101.195/~lumenpastoral/anuario/paroquias
**Schedule Page:** https://arquidiocesepb.org.br/horario-de-missas-e-confissoes/

## Challenge

The website uses **Ninja Tables** WordPress plugin (table ID: 770) which loads data dynamically via JavaScript. The table data is not present in the static HTML and requires JavaScript rendering to extract.

## Available Scrapers

### 1. scraper_joao_pessoa_anuario.py (Recommended - Working!)

**Parish data scraper using the Digital Annual directory (Anuário Digital).**

This scraper extracts parish information from the HTTP-based digital annual directory, which contains comprehensive data about all parishes in the Archdiocese.

**Data Source:** http://162.241.101.195/~lumenpastoral/anuario/paroquias

**Setup:**
```bash
poetry install --with scrapers
```

**Usage:**
```bash
poetry run python contrib/scraper_joao_pessoa_anuario.py > parishes.jsonl
```

**Extracted Data:**
- Parish name and type (Paróquia, Capelania, Santuário)
- Forania (regional grouping)
- City and state (all in Paraíba - PB)
- Year of creation
- Complete address with zip code
- Contact information (phones, emails)
- Active clergy (priests and deacons)

**Output:** JSONL format with ~105 parishes

**Advantages:**
- ✅ Works without JavaScript rendering
- ✅ Fast and reliable
- ✅ Comprehensive parish data
- ✅ No authentication required
- ✅ HTTP endpoint (not HTTPS issues)

### 2. scraper_joao_pessoa.py (For Mass Schedules - Experimental)

**Status:** Not fully functional - requires JavaScript rendering for Ninja Tables plugin.

Full-featured scraper using **scrapy-playwright** for JavaScript rendering to extract Mass schedules from the main schedule page.

**Data Source:** https://arquidiocesepb.org.br/horario-de-missas-e-confissoes/

**Setup:**
```bash
poetry install --with scrapers
poetry run playwright install chromium
```

**Usage:**
```bash
poetry run scrapy runspider contrib/scraper_joao_pessoa.py -o output.jsonl
```

**Intended Features:**
- Renders JavaScript to access dynamic Ninja Tables content
- Extracts Mass and confession schedules
- Automatically parses table data

**Current Limitations:**
- May timeout in restricted network environments
- Requires proper browser automation setup
- Ninja Tables uses complex JavaScript rendering

**Alternative:** Use the anuario scraper for parish contact information, then manually collect Mass schedules.

### 3. scraper_joao_pessoa_simple.py (Investigation Tool)

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
