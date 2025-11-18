# João Pessoa (PB) Scraper

Scraper for extracting parish information from Arquidiocese da Paraíba.

**Website:** https://arquidiocesepb.org.br/
**Data Source:** http://162.241.101.195/~lumenpastoral/anuario/paroquias

## scraper_joao_pessoa_anuario.py

**Parish data scraper using the Digital Annual directory (Anuário Digital).**

This scraper extracts parish information from the HTTP-based digital annual directory, which contains comprehensive data about all parishes in the Archdiocese.

**Setup:**
```bash
poetry install --with scrapers
```

**Usage:**
```bash
poetry run python contrib/scraper_joao_pessoa_anuario.py > output.jsonl
```

**Extracted Data:**
- Parish name and type (Paróquia, Capelania, Santuário)
- Forania (regional grouping)
- City and state (all in Paraíba - PB)
- Year of creation
- Complete address with zip code
- Contact information (phones, emails)
- Active clergy (priests and deacons)

**Output:** JSONL format with ~105 parishes across 9 Foranias:
- Agreste, Centro, Conjuntos, Litoral
- Praia Norte, Praia Sul, Urbana Sul
- Vale do Mamanguape, Várzea

**Advantages:**
- ✅ Works without JavaScript rendering
- ✅ Fast and reliable
- ✅ Comprehensive parish data
- ✅ No authentication required
- ✅ HTTP endpoint (no HTTPS certificate issues)

## Dependencies

This scraper uses:
- `requests` - HTTP requests
- `beautifulsoup4` - HTML parsing

## Example Output

```json
{
  "forania": "Centro João Pessoa.",
  "parish_name": "Paróquia NOSSA SENHORA APARECIDA",
  "city": "João Pessoa",
  "state": "PB",
  "year_created": 1997,
  "address": "Rua Carteiro Francisco Marques, 255 Cristo Redentor - João Pessoa (Paraíba) 58071-160",
  "phones": ["(83) 3224-4969"],
  "emails": ["paroquiansaparecida@gmail.com"],
  "clergy": "Pe. JOSÉ ROBERTO DOS SANTOS Pároco"
}
```
