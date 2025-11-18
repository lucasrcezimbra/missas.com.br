import json

import llm
import scrapy
from decouple import config

OPENAI_API_KEY = config("OPENAI_API_KEY")


class BrasiliaSpider(scrapy.Spider):
    name = "brasilia"
    allowed_domains = ["arqbrasilia.com.br"]
    start_urls = [
        "https://arqbrasilia.com.br/paroquias/",
    ]

    def parse(self, response):
        # Find all parish links
        parish_links = response.css('a[href*="/todas_paroquias/"]::attr(href)').getall()

        for href in parish_links:
            yield response.follow(href, self.parse_parish_page)

    def parse_parish_page(self, response):
        parish_name = response.css("title::text").get()

        # Extract the main content area
        # Adjust selector based on actual HTML structure
        content_area = response.css("article, .entry-content, .post-content, main")
        if content_area:
            text_elements = content_area[0].css("::text")
        else:
            # Fallback to body if specific content area not found
            text_elements = response.css("body ::text")

        post_text = "\n".join((e.get().strip() for e in text_elements if e.get().strip()))

        model = llm.get_model("gpt-4o")
        model.key = OPENAI_API_KEY
        ai_response = model.prompt(
            post_text,
            system="""\
                You are a scraping helper. The user will send a text extracted from a HTML page and you MUST return a JSON.
                If you don't find the information in the page, do NOT add to the final JSON.
                `phone`, `phone2`, `whatsapp` MUST be in the format +55XXXXXXXXXX (with country code +55 and area code).
                `instagram` and `facebook` MUST be only the username, remove the URL.
                Extract the city name if mentioned (like Brasília, Taguatinga, Ceilândia, etc).
                The JSON example:
                `{"city": "Brasília", "email": "mail@example.com", "facebook": "paroquiaexemplo", "instagram": "paroquiaexemplo", "phone": "+5561000000000", "phone2": "+5561000000000", "whatsapp": "+5561000000000"}`\
            """,
            json_object=True,
        )
        yield {
            "parish_name": parish_name,
            "state": "Distrito Federal",
            **json.loads(ai_response.text()),
        }
