import json

import llm
import scrapy
from decouple import config

OPENAI_API_KEY = config("OPENAI_API_KEY", default="")


class SalvadorSpider(scrapy.Spider):
    name = "salvador"
    allowed_domains = ["arquidiocesesalvador.org.br"]

    # All forania category pages
    start_urls = [
        "https://arquidiocesesalvador.org.br/categoria/paroquias/foranias/forania-1/",
        "https://arquidiocesesalvador.org.br/categoria/paroquias/foranias/forania-2a/",
        "https://arquidiocesesalvador.org.br/categoria/paroquias/foranias/forania-2b/",
        "https://arquidiocesesalvador.org.br/categoria/paroquias/foranias/forania-3/",
        "https://arquidiocesesalvador.org.br/categoria/paroquias/foranias/forania-4/",
        "https://arquidiocesesalvador.org.br/categoria/paroquias/foranias/forania-5/",
        "https://arquidiocesesalvador.org.br/categoria/paroquias/foranias/forania-6/",
        "https://arquidiocesesalvador.org.br/categoria/paroquias/foranias/forania-7a/",
        "https://arquidiocesesalvador.org.br/categoria/paroquias/foranias/forania-7b/",
        "https://arquidiocesesalvador.org.br/categoria/paroquias/foranias/forania-8/",
        "https://arquidiocesesalvador.org.br/categoria/paroquias/foranias/forania-9/",
        "https://arquidiocesesalvador.org.br/categoria/paroquias/foranias/forania-10/",
    ]

    def parse(self, response):
        # Extract parish links from Elementor posts
        parish_links = response.css(
            "a.elementor-post__thumbnail__link::attr(href)"
        ).getall()

        # Also get from text links
        text_links = response.css("div.elementor-post__text a::attr(href)").getall()
        parish_links.extend(text_links)

        # Remove duplicates while preserving order
        seen = set()
        unique_links = []
        for link in parish_links:
            if (
                link
                and link not in seen
                and ("paroquia-" in link or "basilica-" in link)
            ):
                seen.add(link)
                unique_links.append(link)

        for link in unique_links:
            yield response.follow(link, self.parse_parish_page)

    def parse_parish_page(self, response):
        parish_name = response.css("h1.entry-title::text").get()
        if not parish_name:
            parish_name = response.css("title::text").get()

        # Extract all text from Elementor content or main content area
        # Try Elementor content first
        post_body = response.css(
            "div.elementor-widget-container, div.entry-content, article.post, main"
        )

        if post_body:
            text_elements = post_body.css("::text")
            post_text = "\n".join(
                (e.get().strip() for e in text_elements if e.get().strip())
            )
        else:
            # Fallback: get all text from body
            text_elements = response.css("body ::text")
            post_text = "\n".join(
                (e.get().strip() for e in text_elements if e.get().strip())
            )

        if not post_text or len(post_text) < 50:
            self.logger.warning("No sufficient content found for %s", parish_name)
            return

        if not OPENAI_API_KEY:
            self.logger.warning(
                "OPENAI_API_KEY not configured, skipping LLM processing for %s",
                parish_name,
            )
            return

        model = llm.get_model("gpt-4o")
        model.key = OPENAI_API_KEY
        ai_response = model.prompt(
            post_text,
            system="""\
                You are a scraping helper. The user will send a text extracted from a HTML page and you MUST return a JSON.
                If you don't find the information in the page, do NOT add to the final JSON.
                `phone`, `phone2`, `whatsapp` MUST be in the format +5571000000000 or +557100000000.
                `instagram` and `facebook` MUST be only the username, remove the URL.
                `address` should be the full address if available.
                `website` should be the full URL if available.
                The JSON example:
                `{"city": "Salvador", "state": "Bahia", "address": "Rua Example, 123", "email": "mail@example.com", "facebook": "paroquiaexemplo", "instagram": "paroquiaexemplo", "phone": "+5571000000000", "phone2": "+5571000000000", "whatsapp": "+5571000000000", "website": "https://example.com"}`\
            """,
            json_object=True,
        )

        result = {
            "parish_name": parish_name,
            "state": "Bahia",
            **json.loads(ai_response.text()),
        }

        yield result
