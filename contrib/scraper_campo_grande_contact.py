import json

import llm
import scrapy
from decouple import config

try:
    OPENAI_API_KEY = config("OPENAI_API_KEY")
except Exception:
    OPENAI_API_KEY = None


class CampoGrandeContactSpider(scrapy.Spider):
    name = "campo_grande_contact"
    allowed_domains = ["arquidiocesedecampogrande.org.br"]
    start_urls = ["https://arquidiocesedecampogrande.org.br/nossas-paroquias/"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY is required. Set it in your .env file or environment."
            )

    def parse(self, response):
        parish_links = response.css(
            'article.elementor-post a[href*="paroquia"]::attr(href), '
            'article.elementor-post a[href*="santuario"]::attr(href)'
        ).getall()

        for link in parish_links:
            yield response.follow(link, self.parse_parish_page)

    def parse_parish_page(self, response):
        parish_name = response.css("title::text").get()
        if parish_name:
            parish_name = parish_name.replace(
                " - Arquidiocese de Campo Grande", ""
            ).strip()

        content_wrapper = response.css(
            'div.elementor-widget-container, '
            'main#content, '
            'article.post'
        )

        if content_wrapper:
            text_elements = content_wrapper.css("::text")
            post_text = "\n".join((e.get() for e in text_elements))
        else:
            post_text = "\n".join(response.css("::text").getall())

        model = llm.get_model("gpt-4o")
        model.key = OPENAI_API_KEY
        ai_response = model.prompt(
            post_text,
            system="""\
                You are a scraping helper. The user will send a text extracted from a HTML page and you MUST return a JSON.
                If you don't find the information in the page, do NOT add to the final JSON.
                `phone`, `phone2`, `whatsapp` MUST be in the format +5567000000000 or +556700000000.
                `instagram` and `facebook` MUST be only the username, remove the URL.
                The JSON example:
                `{"city": "Campo Grande", email": "mail@example.com", "facebook": "paroquiaexemplo", "instagram": "paroquiaexemplo", "phone": "+5567000000000", "phone2": "+5567000000000", "whatsapp": "+5567000000000"}`\
            """,
            json_object=True,
        )
        yield {
            "parish_name": parish_name,
            "state": "Mato Grosso do Sul",
            **json.loads(ai_response.text()),
        }
