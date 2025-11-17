import scrapy


class FlorianopolisSpider(scrapy.Spider):
    name = "florianopolis"
    allowed_domains = ["arquifln.org.br"]
    start_urls = [
        "https://arquifln.org.br/paroquias"
    ]

    def parse(self, response):
        """
        @url https://arquifln.org.br/paroquias
        @returns items 0 100
        @returns requests 0 100
        @scrapes parish_name times
        """
        for parish_link in response.css('a[href*="/igrejas/paroquia-"]::attr(href)').getall():
            yield response.follow(parish_link, self.parse_parish)

    def parse_parish(self, response):
        parish_name = response.css("h1::text").get()

        if not parish_name:
            parish_name = response.css("title::text").get()

        times = []
        for p in response.css('p'):
            text_parts = p.css("::text").getall()
            p_text = " ".join(text_parts).strip()

            if p_text and any(keyword in p_text.lower() for keyword in ["missa", "horário", "confiss", "domingo", "segunda", "terça", "quarta", "quinta", "sexta", "sábado"]):
                times.append(p_text)

        if times:
            yield {
                "parish_name": parish_name,
                "times": times,
                "url": response.url,
            }
        else:
            self.logger.info("No times found for %s", parish_name)
