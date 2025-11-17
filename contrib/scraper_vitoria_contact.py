import json

import llm
import scrapy
from decouple import config

OPENAI_API_KEY = config("OPENAI_API_KEY")


class VitoriaSpider(scrapy.Spider):
    name = "vitoria"
    allowed_domains = ["www.aves.org.br"]
    start_urls = [
        "https://www.aves.org.br/benevente/",
        "https://www.aves.org.br/cariacica-viana/",
        "https://www.aves.org.br/serra-fundao/",
        "https://www.aves.org.br/serrana/",
        "https://www.aves.org.br/vila-velha/",
        "https://www.aves.org.br/vitoria-paroquias/",
    ]

    def parse(self, response):
        parish_links = response.css('h2 a')

        for link in parish_links:
            parish_url = link.css('::attr(href)').get()
            parish_name = link.css('::text').get()

            if parish_url and parish_name:
                if "area-pastoral" not in parish_url.lower():
                    yield response.follow(parish_url, self.parse_parish_page)

        next_page_link = response.xpath('//a[contains(text(), "Próximo")]/@href').get()
        if next_page_link:
            yield response.follow(next_page_link, self.parse)

    def parse_parish_page(self, response):
        parish_name = response.css("title::text").get()
        if parish_name:
            parish_name = parish_name.split(" - ")[0].strip()

        main_content = response.css('main, article, div.elementor-widget-container')
        text_elements = main_content.css("::text")
        post_text = "\n".join((e.get().strip() for e in text_elements if e.get().strip()))

        model = llm.get_model("gpt-4o")
        model.key = OPENAI_API_KEY
        ai_response = model.prompt(
            post_text,
            system="""\
                You are a scraping helper. The user will send a text extracted from a HTML page and you MUST return a JSON.
                If you don't find the information in the page, do NOT add to the final JSON.
                `phone`, `phone2`, `whatsapp` MUST be in the format +5527000000000 or +552700000000.
                `instagram` and `facebook` MUST be only the username, remove the URL.
                The JSON example:
                `{"city": "Vitória", "email": "mail@example.com", "facebook": "paroquiasagradafamilia", "instagram": "paroquiasagradafamilia", "phone": "+5527000000000", "phone2": "+5527000000000", "whatsapp": "+5527000000000"}`\
            """,
            json_object=True,
        )
        yield {
            "parish_name": parish_name,
            "state": "Espírito Santo",
            **json.loads(ai_response.text()),
        }
