import json

import llm
import scrapy
from decouple import config

OPENAI_API_KEY = config("OPENAI_API_KEY")


class SaoLuisContactSpider(scrapy.Spider):
    name = "sao_luis_contact"
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
        """
        parish_links = response.css('a[href*="/paroquia?paroquiaid="]::attr(href)').getall()

        for link in set(parish_links):
            yield response.follow(link, self.parse_parish_contact)

    def parse_parish_contact(self, response):
        """
        Parse individual parish pages to extract contact information.

        NOTE: This website uses JavaScript to load parish data dynamically.
        If this scraper doesn't work, it will need to be updated to use
        scrapy-playwright or scrapy-selenium to render JavaScript.
        """
        parish_id = response.url.split("paroquiaid=")[-1]

        parish_name = response.css(".paroquia-details .name::text").get()
        if not parish_name:
            parish_name = response.css("title::text").get()
            if parish_name:
                parish_name = parish_name.replace("–", "-").split("-")[0].strip()

        post_body = response.css(".paroquia-page")[0] if response.css(".paroquia-page") else response.css("#content-wrapper")

        if not post_body:
            self.logger.warning(
                "No content found for parish %s. "
                "This page may require JavaScript rendering. "
                "URL: %s",
                parish_id,
                response.url,
            )
            return

        text_elements = post_body.css("::text")
        post_text = "\n".join((e.get() for e in text_elements))

        if not post_text.strip():
            self.logger.warning(
                "Empty content for parish %s. "
                "This page may require JavaScript rendering. "
                "URL: %s",
                parish_id,
                response.url,
            )
            return

        model = llm.get_model("gpt-4o")
        model.key = OPENAI_API_KEY
        ai_response = model.prompt(
            post_text,
            system="""\
                You are a scraping helper. The user will send a text extracted from a HTML page and you MUST return a JSON.
                If you don't find the information in the page, do NOT add to the final JSON.
                `phone`, `phone2`, `whatsapp` MUST be in the format +5598000000000 or +559800000000.
                `instagram` and `facebook` MUST be only the username, remove the URL.
                The JSON example:
                `{"city": "São Luís", email": "mail@example.com", "facebook": "paroquiaexemplo", "instagram": "paroquiaexemplo", "phone": "+5598000000000", "phone2": "+5598000000000", "whatsapp": "+5598000000000"}`\
            """,
            json_object=True,
        )

        yield {
            "parish_id": parish_id,
            "parish_name": parish_name,
            "state": "Maranhão",
            "url": response.url,
            **json.loads(ai_response.text()),
        }
