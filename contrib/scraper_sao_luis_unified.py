import json

import llm
import scrapy
from decouple import config

OPENAI_API_KEY = config("OPENAI_API_KEY")


class SaoLuisUnifiedSpider(scrapy.Spider):
    name = "sao_luis_unified"
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
        parish_links = response.css(
            'a[href*="/paroquia?paroquiaid="]::attr(href)'
        ).getall()

        for link in set(parish_links):
            yield response.follow(link, self.parse_parish)

    def parse_parish(self, response):
        """
        Parse individual parish pages to extract both schedules and contact info.

        NOTE: This website uses JavaScript to load parish data dynamically.
        If this scraper doesn't work, it will need to be updated to use
        scrapy-playwright or scrapy-selenium to render JavaScript.

        @scrapes parish_id parish_name times contact_info state url
        """
        parish_id = response.url.split("paroquiaid=")[-1]

        parish_name = response.css(".paroquia-details .name::text").get()
        if not parish_name:
            parish_name = response.css("title::text").get()
            if parish_name:
                parish_name = parish_name.replace("–", "-").split("-")[0].strip()

        post_body = (
            response.css(".paroquia-page")[0]
            if response.css(".paroquia-page")
            else response.css("#content-wrapper")
        )

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

        contact_info = json.loads(ai_response.text())

        yield {
            "parish_id": parish_id,
            "parish_name": parish_name,
            "state": "Maranhão",
            "times": times,
            "contact_info": contact_info,
            "url": response.url,
        }
