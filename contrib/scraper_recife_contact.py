import json

import llm
import scrapy
from decouple import config

OPENAI_API_KEY = config("OPENAI_API_KEY")


class RecifeSpider(scrapy.Spider):
    name = "recife"
    allowed_domains = ["www.arquidioceseolindarecife.org"]
    start_urls = [
        "https://www.arquidioceseolindarecife.org/boa-viagem/",
        "https://www.arquidioceseolindarecife.org/vicariato-beberibe/",
        "https://www.arquidioceseolindarecife.org/cabo/",
        "https://www.arquidioceseolindarecife.org/paroquias/igarassu/",
        "https://www.arquidioceseolindarecife.org/jardim-sao-paulo/",
        "https://www.arquidioceseolindarecife.org/paroquias/olinda/",
        "https://www.arquidioceseolindarecife.org/soledade/",
        "https://www.arquidioceseolindarecife.org/varzea/",
        "https://www.arquidioceseolindarecife.org/vitoria-2/",
        "https://www.arquidioceseolindarecife.org/vicariato-ibura/",
        "https://www.arquidioceseolindarecife.org/vicariato-sao-lourenco/",
        "https://www.arquidioceseolindarecife.org/vicariato-paulista/",
        "https://www.arquidioceseolindarecife.org/vicariato-jaboatao/",
    ]

    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36"
    }

    def parse(self, response):
        content = response.css("div.entry-content")[0]
        text_elements = content.css("::text")
        content_text = "\n".join((e.get() for e in text_elements))

        vicariate_name = response.css("h1.entry-title::text").get()

        model = llm.get_model("gpt-4o")
        model.key = OPENAI_API_KEY
        ai_response = model.prompt(
            content_text,
            system="""\
                You are a scraping helper for Catholic parish data. The user will send text extracted from a vicariate page containing multiple parishes.
                Parse the text and extract ALL parishes with their information.
                Return a JSON array where each item represents one parish.
                If you don't find specific information for a field, do NOT add it to the parish object.
                `phone`, `phone2`, `whatsapp` MUST be in the format +558100000000 or +5581000000000.
                `instagram` and `facebook` MUST be only the username, remove the URL.
                Extract the city from the address if present.
                The JSON array example:
                `[{"parish_name": "Nossa Senhora da Conceição", "city": "Recife", "address": "Praça da Convenção, 107 - Beberibe, 52130-470", "email": "mail@example.com", "facebook": "paroquiansconceicao", "instagram": "paroquiansconceicao", "phone": "+558134490521", "phone2": "+558134490522", "whatsapp": "+558134490521"}]`\
            """,
            json_object=True,
        )

        parishes = json.loads(ai_response.text())

        if isinstance(parishes, dict) and "parishes" in parishes:
            parishes = parishes["parishes"]

        for parish in parishes:
            yield {
                "vicariate": vicariate_name,
                "state": "Pernambuco",
                **parish,
            }
