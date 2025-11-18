import scrapy


class TeresinaSpider(scrapy.Spider):
    name = "teresina"
    allowed_domains = ["arquidiocesedetersina.org.br"]
    start_urls = ["https://arquidiocesedetersina.org.br/"]

    def parse(self, response):
        """
        Spider para extrair informações de paróquias e horários de missas
        da Arquidiocese de Teresina.

        TODO: Verificar a URL correta da página de horários de missas
        TODO: Atualizar os seletores CSS baseado na estrutura real do site

        @url https://arquidiocesedetersina.org.br/
        @returns items 0 100
        @returns requests 0 10
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
