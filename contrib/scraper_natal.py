import scrapy


class NatalSpider(scrapy.Spider):
    name = "natal"
    allowed_domains = ["www.arquidiocesedenatal.org.br"]
    start_urls = [
        "https://www.arquidiocesedenatal.org.br/c%C3%B3pia-hor%C3%A1rios-de-missa-2"
    ]

    def parse(self, response):
        """
        @url https://www.arquidiocesedenatal.org.br/horariosdemissa
        @returns items 56 56
        @returns requests 1 1
        @scrapes parish_name times
        """
        for rich_text in response.css('div[data-testid="richTextElement"]'):
            parish_name = rich_text.css("h1>span>span::text").get()
            times = rich_text.css("p ::text").getall()
            if not times:
                self.logger.info("No times found for %s", parish_name)
                continue
            yield {
                "parish_name": parish_name,
                "times": times,
            }

        next_page_urls = response.css('a[aria-label="Next"]::attr(href)').getall()
        for url in next_page_urls:
            yield response.follow(url, self.parse)
