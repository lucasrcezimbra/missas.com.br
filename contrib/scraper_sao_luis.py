import scrapy


class SaoLuisSpider(scrapy.Spider):
    name = "sao_luis"
    allowed_domains = ["arquislz.org.br"]
    start_urls = [
        "https://arquislz.org.br/foranias/",
    ]

    custom_settings = {
        "DOWNLOAD_DELAY": 2,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "DEFAULT_REQUEST_HEADERS": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        },
    }

    def parse(self, response):
        """
        Parse the foranias (deaneries) page to extract parish links.

        @url https://arquislz.org.br/foranias/
        @returns requests 60 70
        """
        parish_links = response.css('a[href*="/paroquia?paroquiaid="]::attr(href)').getall()

        for link in set(parish_links):
            yield response.follow(link, self.parse_parish_schedule)

    def parse_parish_schedule(self, response):
        """
        Parse individual parish pages to extract mass schedules.

        NOTE: This website uses JavaScript to load parish data dynamically.
        If this scraper doesn't work, it will need to be updated to use
        scrapy-playwright or scrapy-selenium to render JavaScript.

        @scrapes parish_name times
        """
        parish_id = response.url.split("paroquiaid=")[-1]

        parish_name = response.css(".paroquia-details .name::text").get()

        if not parish_name:
            parish_name = response.css("h1::text").get()

        times_sections = response.css(".paroquia-section")
        times = []

        for section in times_sections:
            section_title = section.css(".paroquia-section-title::text").get()
            section_content = section.css("::text").getall()

            if section_title:
                times.append(section_title.strip())

            for text in section_content:
                text = text.strip()
                if text and text not in (parish_name or ""):
                    times.append(text)

        all_text = response.css(".paroquia-page ::text").getall()
        times.extend([t.strip() for t in all_text if t.strip()])

        times = [t for t in times if t]

        if parish_name or times:
            yield {
                "parish_id": parish_id,
                "parish_name": parish_name,
                "times": times,
                "url": response.url,
            }
        else:
            self.logger.warning(
                "No data found for parish %s. "
                "This page may require JavaScript rendering. "
                "URL: %s",
                parish_id,
                response.url,
            )
