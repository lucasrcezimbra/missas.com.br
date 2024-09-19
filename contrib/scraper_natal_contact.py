import json

import llm
import scrapy
from decouple import config

OPENAI_API_KEY = config("OPENAI_API_KEY")


class NatalSpider(scrapy.Spider):
    name = "natal"
    allowed_domains = ["www.arquidiocesedenatal.org.br"]
    start_urls = [
        "https://www.arquidiocesedenatal.org.br/vicariato-urbano",
        "https://www.arquidiocesedenatal.org.br/c%C3%B3pia-vicariato-urbano",
        "https://www.arquidiocesedenatal.org.br/vicariato-norte",
        "https://www.arquidiocesedenatal.org.br/c%C3%B3pia-vicariato-norte",
        "https://www.arquidiocesedenatal.org.br/vicariato-sul",
        "https://www.arquidiocesedenatal.org.br/c%C3%B3pia-vicariato-sul",
    ]

    def parse(self, response):
        for rich_text in response.css('div[data-testid="richTextElement"]'):
            a_elements = rich_text.css("a")

            for a in a_elements:
                href = a.css("::attr(href)").get()

                if "mailto:" in href:
                    yield {
                        "parish_name": rich_text.css("h1>span>span::text").get(),
                        "email": href.replace("mailto:", ""),
                    }
                else:
                    yield response.follow(href, self.parse_parish_page)

    def parse_parish_page(self, response):
        parish_name = response.css("title::text").get()
        post_body = response.css("#content-wrapper")[0]
        text_elements = post_body.css("::text")
        post_text = "\n".join((e.get() for e in text_elements))

        model = llm.get_model("gpt-4o")
        model.key = OPENAI_API_KEY
        ai_response = model.prompt(
            post_text,
            system="""\
                You are a scraping helper. The user will send a text extracted from a HTML page and you MUST return a JSON.
                If you don't find the information in the page, do NOT add to the final JSON.
                `phone`, `phone2`, `whatsapp` MUST be in the format +5584000000000 or +558400000000.
                `instagram` and `facebook` MUST be only the username, remove the URL.
                The JSON example:
                `{"city": "Natal", email": "mail@example.com", "facebook": "paroquiadacatedraldenatal", "instagram": "paroquiadacatedraldenatal", "phone": "+5584000000000", "phone2": "+5584000000000", "whatsapp": "+5584000000000"}`\
            """,
            json_object=True,
        )
        yield {
            "parish_name": parish_name,
            "state": "Rio Grande do Norte",
            **json.loads(ai_response.text()),
        }
