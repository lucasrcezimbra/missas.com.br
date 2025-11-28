import scrapy


class RecifeContactSpider(scrapy.Spider):
    name = "recife_contact"
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

        yield {
            "vicariate": vicariate_name,
            "url": response.url,
            "state": "Pernambuco",
            "raw_text": content_text,
        }
