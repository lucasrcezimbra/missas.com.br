# Scraping Analysis - Brazilian Capital Archdioceses

This document analyzes the availability of parish data, Mass schedules, and confession schedules on archdiocese websites in Brazilian capital cities, to determine the feasibility and priority for developing scrapers.

**Analysis date:** 2025-11-10

---

## Legend

- ✅ **Available** - Information present and structured
- ⚠️ **Partial** - Information present but incomplete or poorly structured
- ❌ **Not available** - Information not found
- 🔍 **Not verified** - Not yet analyzed

### Scraping Complexity Level

- 🟢 **Easy** - Static HTML, well-structured data
- 🟡 **Medium** - Requires text parsing or irregular structure
- 🔴 **Hard** - Requires JavaScript rendering (Selenium/Puppeteer)

---

## Summary Table - All Archdioceses

| # | Archdiocese | City/State | Website | Parish List | Address | Contact | Mass Schedule | Confession | Complexity | Priority |
|---|-------------|------------|---------|-------------|---------|---------|---------------|------------|------------|----------|
| 1 | Manaus | Manaus/AM | [Link](https://arquidiocesedemanaus.org.br/) | ✅ | ✅ | ✅ | ✅ | ⚠️ | 🔴 Hard | 🟡 Medium-Low |
| 2 | Belém do Pará | Belém/PA | ❌ Site Down | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ N/A | ❌ Skip |
| 3 | Porto Velho | Porto Velho/RO | [Link](https://arquidiocesedeportovelho.org.br/) | ✅ | ❌ | ❌ | ❌ | ❌ | 🟡 Medium | 🟡 Low |
| 4 | Palmas | Palmas/TO | [Link](https://arquidiocesedepalmas.org.br/) | ✅ | ❌ | ⚠️ | ❌ | ❌ | 🔴 Hard | 🟡 Low |
| 5 | São Luís do Maranhão | São Luís/MA | [Link](https://arquislz.org.br/) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ N/A | ❌ Skip |
| 6 | Teresina | Teresina/PI | ❌ Site Down | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ N/A | ❌ Skip |
| 7 | Fortaleza | Fortaleza/CE | [Link](https://www.arquidiocesedefortaleza.org.br/) | ✅ | ❌ | ❌ | ✅ | ❌ | 🔴 Hard | 🟢 High |
| 8 | Natal | Natal/RN | - | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ Done | ✅ Done |
| 9 | Paraíba | João Pessoa/PB | [Link](https://arquidiocesepb.org.br/) | ✅ | ❌ | ❌ | ❌ | ❌ | 🔴 Hard | 🟡 Low |
| 10 | Olinda e Recife | Recife/PE | [Link](https://www.arquidioceseolindarecife.org/) | ✅ | ✅ | ⚠️ | ✅ | ❌ | 🟢 Easy | 🟢 High |
| 11 | Maceió | Maceió/AL | [Link](https://arqdemaceio.com.br/) | ✅ | ❌ | ❌ | ❌ | ❌ | 🟡 Medium | 🟡 Low |
| 12 | Aracaju | Aracaju/SE | [Link](https://arquidiocesedearacaju.org/) | ✅ | ❌ | ❌ | ❌ | ❌ | 🔴 Hard | 🟡 Low |
| 13 | São Salvador da Bahia | Salvador/BA | [Link](https://arquidiocesesalvador.org.br/) | ✅ | ❌ | ❌ | ❌ | ❌ | 🔴 Hard | 🟡 Medium |
| 14 | Brasília | Brasília/DF | [Link](https://arqbrasilia.com.br/) | ✅ | ❌ | ❌ | ✅ | ❌ | 🔴 Hard | 🟢 High |
| 15 | Goiânia | Goiânia/GO | [Link](https://arquidiocesedegoiania.org.br/) | ✅ | ❌ | ❌ | ⚠️ | ❌ | 🔴 Hard | 🟡 Medium-Low |
| 16 | Cuiabá | Cuiabá/MT | [Link](https://arquidiocesecuiaba.org.br/) | ✅ | ❌ | ❌ | ❌ | ❌ | 🟡 Medium | 🟡 Low |
| 17 | Campo Grande | Campo Grande/MS | [Link](https://arquidiocesedecampogrande.org.br/) | ✅ | ❌ | ❌ | ✅ | ❌ | 🟢 Easy | 🟢 High |
| 18 | Belo Horizonte | Belo Horizonte/MG | [Link](https://arquidiocesebh.org.br/) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ N/A | ❌ Skip |
| 19 | Vitória | Vitória/ES | [Link](https://www.aves.org.br/) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ N/A | ❌ Skip |
| 20 | Rio de Janeiro | Rio de Janeiro/RJ | [Link](https://arqrio.org.br/) | ✅ | ❌ | ❌ | ❌ | ❌ | 🟡 Medium | 🟡 Medium |
| 21 | São Paulo | São Paulo/SP | [Link](https://arquisp.org.br/) | ✅ | ❌ | ❌ | ❌ | ❌ | 🔴 Hard | 🟢 High |
| 22 | Curitiba | Curitiba/PR | [Link](https://arquidiocesedecuritiba.org.br/) | ✅ | ❌ | ❌ | ❌ | ❌ | 🔴 Hard | 🟡 Medium |
| 23 | Florianópolis | Florianópolis/SC | [Link](https://arquifln.org.br/) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ N/A | ❌ Skip |
| 24 | Porto Alegre | Porto Alegre/RS | [Link](https://www.arquipoa.com/) | ✅ | ❌ | ❌ | ❌ | ❌ | 🟡 Medium | 🟡 Medium |

**Note:** Contact includes Phone, Email, WhatsApp, and Social Media

---

## Detailed Analysis by Region

## North Region

### 1. Arquidiocese de Manaus (AM)
**Website:** https://arquidiocesedemanaus.org.br/

#### Data Availability
| Data | Status | Notes |
|------|--------|-------|
| **Parish List** | ✅ | Complete list available at /paroquias/ |
| **Address** | ✅ | Full address with ZIP code |
| **Phone** | ✅ | Multiple phones per parish |
| **Email** | ✅ | Institutional emails available |
| **WhatsApp** | ⚠️ | Some numbers identified as WhatsApp |
| **Social Media** | ⚠️ | Instagram handles mentioned in some cases |
| **Parish Website** | ⚠️ | Few parish websites listed |
| **Mass Schedules** | ✅ | Schedules by day of week |
| **Confession Schedules** | ⚠️ | Mentioned in some cases |

#### Technical Structure
- **Data Format:** HTML with Markdown-formatted text
- **Rendering:** JavaScript (Elementor page builder + AJAX)
- **Complexity:** 🔴 **Hard**
- **URL:** /paroquias/

**Scraping Challenges:**
1. Requires JavaScript execution (Selenium/Playwright)
2. Free-form text format without specific CSS classes
3. Complex parsing due to inconsistent formatting
4. Need to extract text patterns (regex) for fields like phone, email
5. Mass schedules mixed with information about novenas and adorations

**Priority:** 🟡 **Medium-Low** - Complete data but high technical complexity

---

### 2. Arquidiocese de Belém do Pará (PA)
**Website:** https://arquidiocesedebelém.com.br/ ❌ **Site Down**

#### Status
Site is not accessible (DNS error). Cannot be scraped until site is restored.

**Priority:** ❌ **Skip**

---

### 3. Arquidiocese de Porto Velho (RO)
**Website:** https://arquidiocesedeportovelho.org.br/

#### Data Availability
| Data | Status | Notes |
|------|--------|-------|
| **Parish List** | ✅ | 26+ parishes organized by sectors |
| **Address** | ❌ | Not available on listing page |
| **Contact** | ❌ | Must visit individual parish pages |
| **Mass Schedules** | ❌ | Not on main directory |
| **Confession Schedules** | ❌ | Not available |

#### Technical Structure
- **Data Format:** WordPress with card-based layout
- **Rendering:** Mostly server-side HTML
- **Complexity:** 🟡 **Medium**
- **URL:** /paroquias/

**Scraping Notes:**
- Parish directory is just an index with links
- Would need to crawl individual parish pages for details
- No mass schedules visible

**Priority:** 🟡 **Low** - Limited data availability

---

### 4. Arquidiocese de Palmas (TO)
**Website:** https://arquidiocesedepalmas.org.br/

#### Data Availability
| Data | Status | Notes |
|------|--------|-------|
| **Parish List** | ✅ | 20 parishes across 3 regions |
| **Address** | ❌ | Not on main listing |
| **Contact** | ⚠️ | Only archdiocese contact in footer |
| **Mass Schedules** | ❌ | Not available |
| **Confession Schedules** | ❌ | Not available |

#### Technical Structure
- **Data Format:** Jet Engine filterable grid
- **Rendering:** JavaScript (Elementor + Jet Engine)
- **Complexity:** 🔴 **Hard**
- **URL:** /nossas-paroquias/

**Scraping Notes:**
- Only thumbnails and names visible
- Individual parish pages needed for details
- Dynamic filtering system

**Priority:** 🟡 **Low** - Limited data, high complexity

---

## Northeast Region

### 5. Arquidiocese de São Luís do Maranhão (MA)
**Website:** https://arquislz.org.br/

#### Status
No parish directory found on homepage. Site appears to be primarily news/announcements focused.

**Priority:** ❌ **Skip**

---

### 6. Arquidiocese de Teresina (PI)
**Website:** https://arquidiocesedetersina.org.br/ ❌ **Site Down**

#### Status
Site is not accessible (DNS error). Cannot be scraped until site is restored.

**Priority:** ❌ **Skip**

---

### 7. Arquidiocese de Fortaleza (CE)
**Website:** https://www.arquidiocesedefortaleza.org.br/

#### Data Availability
| Data | Status | Notes |
|------|--------|-------|
| **Parish List** | ✅ | Searchable directory |
| **Address** | ❌ | Not in search results |
| **Contact** | ❌ | Not in search results |
| **Mass Schedules** | ✅ | Dedicated mass schedule page with search |
| **Confession Schedules** | ❌ | Not available |

#### Technical Structure
- **Data Format:** WordPress with AJAX search
- **Rendering:** JavaScript (JetSearch REST API)
- **Complexity:** 🔴 **Hard**
- **URL:** /servicos/agendas/agenda-de-missas/

**Scraping Notes:**
- Search-based interface using REST API: /wp-json/jet-search/v1/search-posts
- Dynamic loading requires API calls or JavaScript execution
- Mass schedules available but require search

**Priority:** 🟢 **High** - Has mass schedules despite complexity

---

### 8. Arquidiocese de Natal (RN)
**Status:** ✅ **Already Implemented** - Existing scraper in project

---

### 9. Arquidiocese da Paraíba (João Pessoa - PB)
**Website:** https://arquidiocesepb.org.br/

#### Data Availability
| Data | Status | Notes |
|------|--------|-------|
| **Parish List** | ✅ | Has parishes section |
| **Address** | ❌ | Not on main page |
| **Contact** | ❌ | Not on main page |
| **Mass Schedules** | ❌ | Not available |
| **Confession Schedules** | ❌ | Not available |

#### Technical Structure
- **Data Format:** WordPress with Divi theme
- **Rendering:** JavaScript with AJAX
- **Complexity:** 🔴 **Hard**
- **URL:** /paroquias/

**Priority:** 🟡 **Low** - Limited data visibility

---

### 10. Arquidiocese de Olinda e Recife (PE)
**Website:** https://www.arquidioceseolindarecife.org/

#### Data Availability
| Data | Status | Notes |
|------|--------|-------|
| **Parish List** | ✅ | 70+ parishes organized by type |
| **Address** | ✅ | Locations listed with parish names |
| **Contact** | ⚠️ | Some phone numbers included |
| **Mass Schedules** | ✅ | Comprehensive schedule by day/time |
| **Confession Schedules** | ❌ | Not available |

#### Technical Structure
- **Data Format:** Plain text with hierarchical organization
- **Rendering:** Server-side HTML
- **Complexity:** 🟢 **Easy**
- **URL:** /horarios-de-missas/

**Scraping Notes:**
- Well-organized text format
- Includes Basílicas, Santuários, Oratórios, and Paróquias
- Mass times listed by day of week
- Some phone numbers included
- Text parsing required but straightforward

**Priority:** 🟢 **High** - Excellent data availability with easy structure (3.3M Catholics - 3rd largest)

---

### 11. Arquidiocese de Maceió (AL)
**Website:** https://arqdemaceio.com.br/

#### Data Availability
| Data | Status | Notes |
|------|--------|-------|
| **Parish List** | ✅ | Has parishes section |
| **Address** | ❌ | Not visible on main page |
| **Contact** | ❌ | Not visible |
| **Mass Schedules** | ❌ | Not available |
| **Confession Schedules** | ❌ | Not available |

#### Technical Structure
- **Data Format:** WordPress with Elementor
- **Rendering:** Server-side HTML
- **Complexity:** 🟡 **Medium**
- **URL:** /paroquias/

**Priority:** 🟡 **Low** - Limited data visibility

---

### 12. Arquidiocese de Aracaju (SE)
**Website:** https://arquidiocesedearacaju.org/

#### Data Availability
| Data | Status | Notes |
|------|--------|-------|
| **Parish List** | ✅ | Organized by 6 regional vicariates |
| **Address** | ❌ | Not on main listing |
| **Contact** | ❌ | Not available |
| **Mass Schedules** | ❌ | Not available |
| **Confession Schedules** | ❌ | Not available |

#### Technical Structure
- **Data Format:** JET Smart Filters with Elementor
- **Rendering:** JavaScript (dynamic filtering)
- **Complexity:** 🔴 **Hard**
- **URL:** /paroquias-todas/

**Priority:** 🟡 **Low** - Limited data, high complexity

---

### 13. Arquidiocese de São Salvador da Bahia (BA)
**Website:** https://arquidiocesesalvador.org.br/

#### Data Availability
| Data | Status | Notes |
|------|--------|-------|
| **Parish List** | ✅ | Organized by 10 Foranias (deaneries) |
| **Address** | ❌ | Not on directory page |
| **Contact** | ❌ | Not available |
| **Mass Schedules** | ❌ | Not available |
| **Confession Schedules** | ❌ | Not available |

#### Technical Structure
- **Data Format:** WordPress with Elementor
- **Rendering:** JavaScript (Elementor lazy-loading)
- **Complexity:** 🔴 **Hard**
- **URL:** /paroquias/

**Scraping Notes:**
- Hierarchical organization by Forania
- REST API potentially available
- Requires JavaScript rendering

**Priority:** 🟡 **Medium** - Historic archdiocese (Sé Primacial, 1551) but limited data

---

## Central-West Region

### 14. Arquidiocese de Brasília (DF)
**Website:** https://arqbrasilia.com.br/

#### Data Availability
| Data | Status | Notes |
|------|--------|-------|
| **Parish List** | ✅ | Organized by vicariates |
| **Address** | ❌ | Not on main page |
| **Contact** | ❌ | Not on main page |
| **Mass Schedules** | ✅ | Searchable database with filters |
| **Confession Schedules** | ❌ | Not available |

#### Technical Structure
- **Data Format:** WordPress with search form
- **Rendering:** Server-side with AJAX for search
- **Complexity:** 🔴 **Hard**
- **URL:** /horarios-de-missas/

**Scraping Notes:**
- Search-based interface (filter by day, parish, neighborhood, time)
- Requires form submission or AJAX calls
- Has dedicated parish finder tool

**Priority:** 🟢 **High** - Has mass schedules with search functionality

---

### 15. Arquidiocese de Goiânia (GO)
**Website:** https://arquidiocesedegoiania.org.br/

#### Data Availability
| Data | Status | Notes |
|------|--------|-------|
| **Parish List** | ✅ | Parish directory with images |
| **Address** | ❌ | Not on main listing |
| **Contact** | ❌ | Not visible |
| **Mass Schedules** | ⚠️ | Has "Horários de Missas" link |
| **Confession Schedules** | ❌ | Not available |

#### Technical Structure
- **Data Format:** WordPress/Elementor with image gallery
- **Rendering:** JavaScript (Elementor + custom data objects)
- **Complexity:** 🔴 **Hard**
- **URL:** /paroquias/

**Priority:** 🟡 **Medium-Low** - Has schedules link but complex structure

---

### 16. Arquidiocese de Cuiabá (MT)
**Website:** https://arquidiocesecuiaba.org.br/

#### Data Availability
| Data | Status | Notes |
|------|--------|-------|
| **Parish List** | ✅ | Has parishes section |
| **Address** | ❌ | Not on main page |
| **Contact** | ❌ | Not visible |
| **Mass Schedules** | ❌ | Not available |
| **Confession Schedules** | ❌ | Not available |

#### Technical Structure
- **Data Format:** WordPress with Elementor
- **Rendering:** Server-side HTML with JS enhancements
- **Complexity:** 🟡 **Medium**
- **URL:** /paroquias/

**Priority:** 🟡 **Low** - Limited data visibility

---

### 17. Arquidiocese de Campo Grande (MS)
**Website:** https://arquidiocesedecampogrande.org.br/

#### Data Availability
| Data | Status | Notes |
|------|--------|-------|
| **Parish List** | ✅ | Parish directory with images |
| **Address** | ❌ | Not on main listing |
| **Contact** | ❌ | Not visible |
| **Mass Schedules** | ✅ | **Excellent structured tables** |
| **Confession Schedules** | ❌ | Not available |

#### Technical Structure
- **Data Format:** HTML tables with dropdown filters
- **Rendering:** Server-side HTML
- **Complexity:** 🟢 **Easy**
- **URL:** /horarios-de-missas/

**Scraping Notes:**
- **Highly structured data** in consistent table format
- Four columns: Type, Day, Time, Observations
- Covers 100+ locations (Parishes, Foranias, Chapels, Sanctuaries)
- Dropdown selector for filtering by location
- **Best structure found so far for mass schedules**

**Priority:** 🟢 **High** - Excellent data structure, easy to scrape

---

## Southeast Region

### 18. Arquidiocese de Belo Horizonte (MG)
**Website:** https://arquidiocesebh.org.br/

#### Status
No parish directory or data found. Homepage appears to be primarily CSS/framework code without substantial content.

**Priority:** ❌ **Skip**

---

### 19. Arquidiocese de Vitória (ES)
**Website:** https://www.aves.org.br/

#### Status
No parish directory visible on homepage. Site focuses on archbishop activities and general religious content.

**Priority:** ❌ **Skip**

---

### 20. Arquidiocese de São Sebastião do Rio de Janeiro (RJ)
**Website:** https://arqrio.org.br/

#### Data Availability
| Data | Status | Notes |
|------|--------|-------|
| **Parish List** | ✅ | Organized by vicariates |
| **Address** | ❌ | Not on main page |
| **Contact** | ❌ | Not visible |
| **Mass Schedules** | ❌ | Not available |
| **Confession Schedules** | ❌ | Not available |

#### Technical Structure
- **Data Format:** WordPress with Elementor
- **Rendering:** Server-side HTML
- **Complexity:** 🟡 **Medium**
- **URL:** /vicariatos/

**Priority:** 🟡 **Medium** - 2nd largest archdiocese (3.5M Catholics) but limited data

---

### 21. Arquidiocese de São Paulo (SP)
**Website:** https://arquisp.org.br/

#### Data Availability
| Data | Status | Notes |
|------|--------|-------|
| **Parish List** | ✅ | Search-based interface |
| **Address** | ❌ | Not in search results |
| **Contact** | ❌ | Not visible |
| **Mass Schedules** | ❌ | Not available |
| **Confession Schedules** | ❌ | Not available |

#### Technical Structure
- **Data Format:** WordPress with Ajax Search Lite
- **Rendering:** JavaScript (dynamic search)
- **Complexity:** 🔴 **Hard**
- **URL:** /paroquias/

**Scraping Notes:**
- Search-based database, no static listing
- Would require form submission or AJAX calls
- Individual parish pages needed for details

**Priority:** 🟢 **High** - Largest archdiocese (5M Catholics) despite limited data structure

---

## South Region

### 22. Arquidiocese de Curitiba (PR)
**Website:** https://arquidiocesedecuritiba.org.br/

#### Data Availability
| Data | Status | Notes |
|------|--------|-------|
| **Parish List** | ✅ | Has parishes section |
| **Address** | ❌ | Not on main page |
| **Contact** | ❌ | Not visible |
| **Mass Schedules** | ❌ | Not available |
| **Confession Schedules** | ❌ | Not available |

#### Technical Structure
- **Data Format:** WordPress with Elementor
- **Rendering:** JavaScript/AJAX loading
- **Complexity:** 🔴 **Hard**
- **URL:** /paroquias/

**Priority:** 🟡 **Medium** - High complexity, limited data

---

### 23. Arquidiocese de Florianópolis (SC)
**Website:** https://arquifln.org.br/

#### Status
No parish directory found on homepage. Site appears to be general information focused.

**Priority:** ❌ **Skip**

---

### 24. Arquidiocese de Porto Alegre (RS)
**Website:** https://www.arquipoa.com/

#### Data Availability
| Data | Status | Notes |
|------|--------|-------|
| **Parish List** | ✅ | Has parishes section |
| **Address** | ❌ | Not on main page |
| **Contact** | ❌ | Not visible |
| **Mass Schedules** | ❌ | Not available |
| **Confession Schedules** | ❌ | Not available |

#### Technical Structure
- **Data Format:** Traditional HTML
- **Rendering:** Server-side
- **Complexity:** 🟡 **Medium**
- **URL:** /paroquias

**Priority:** 🟡 **Medium** - Simple structure but limited data

---

## Summary and Recommendations

### Overall Statistics

**Archdioceses Analyzed:** 24/24

**Data Availability:**
- ✅ Parish List Available: 19/24 (79%)
- ✅ Mass Schedules Available: 5/24 (21%)
- ✅ Address Data Available: 2/24 (8%)
- ✅ Contact Data Available: 2/24 (8%)
- ❌ Sites Down/No Data: 5/24 (21%)

**Technical Complexity:**
- 🟢 Easy (Static HTML): 2 sites
- 🟡 Medium (Text parsing): 7 sites
- 🔴 Hard (JavaScript): 10 sites
- ❌ Not Scrapable: 5 sites

### Top Priority Targets (High ROI)

Based on data quality, structure, and archdiocese size:

#### 🟢 Tier 1 - High Priority (Implement Next)

1. **Campo Grande (MS)** - 🟢 Easy
   - **Best data structure found**
   - Excellent HTML tables with mass schedules
   - 100+ locations covered
   - Low implementation effort

2. **Olinda e Recife (PE)** - 🟢 Easy
   - 70+ parishes with locations
   - Mass schedules by day
   - Plain text, straightforward parsing
   - 3rd largest (3.3M Catholics)

3. **Fortaleza (CE)** - 🔴 Hard but worthwhile
   - Has mass schedules with search
   - REST API available
   - Large archdiocese

4. **Brasília (DF)** - 🔴 Hard but worthwhile
   - Searchable mass schedules database
   - Filter by multiple criteria
   - Capital city

#### 🟡 Tier 2 - Medium Priority

5. **São Paulo (SP)** - 🔴 Hard
   - **Largest archdiocese** (5M Catholics)
   - Search-based but worth the effort for coverage

6. **Manaus (AM)** - 🔴 Hard
   - **Most complete data found**
   - Address, contact, schedules all available
   - Complex parsing but comprehensive

7. **Salvador (BA)** - 🔴 Hard
   - **Historic significance** (Sé Primacial, 1551)
   - Well-organized by Foranias

8. **Rio de Janeiro (RJ)** - 🟡 Medium
   - **2nd largest** (3.5M Catholics)
   - Medium complexity

#### ❌ Skip for Now

- Belém (PA) - Site down
- Teresina (PI) - Site down
- São Luís (MA) - No data found
- Belo Horizonte (MG) - No data found
- Vitória (ES) - No data found
- Florianópolis (SC) - No data found

### Implementation Strategy

**Phase 1: Quick Wins (2-3 weeks)**
1. Campo Grande - Easy tables
2. Olinda e Recife - Easy text parsing

**Phase 2: High Value (4-6 weeks)**
3. Fortaleza - REST API integration
4. Brasília - Search form automation
5. São Paulo - Database scraping for largest archdiocese

**Phase 3: Comprehensive Coverage (8-12 weeks)**
6. Manaus - Complex but complete data
7. Other medium-priority sites

### Technical Recommendations

**For Easy Sites (Campo Grande, Olinda e Recife):**
- Use Scrapy with basic HTML parsing
- BeautifulSoup for table/text extraction
- Minimal JavaScript handling needed

**For Hard Sites (Fortaleza, Brasília, São Paulo):**
- Playwright for JavaScript rendering
- REST API calls where available
- Form automation for search-based interfaces
- Selenium as fallback

**General Approach:**
1. Start with sites that have actual mass schedules
2. Prioritize larger archdioceses for maximum impact
3. Use simple tools for easy targets first
4. Invest in complex tooling only for high-value targets

---

**Last update:** 2025-11-10
