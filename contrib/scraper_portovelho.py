import scrapy


class PortoVelhoSpider(scrapy.Spider):
    name = "portovelho"
    allowed_domains = ["arquidiocesedeportovelho.org.br"]
    start_urls = ["https://arquidiocesedeportovelho.org.br/paroquias/"]

    def parse(self, response):
        """
        @url https://arquidiocesedeportovelho.org.br/paroquias/
        @returns requests 26 30
        @scrapes
        """
        parish_links = response.css('a[href*="/paroquia/"]::attr(href)').getall()

        for url in parish_links:
            yield response.follow(url, self.parse_parish)

    def parse_parish(self, response):
        """
        Parse individual parish page to extract name and Mass schedules.

        @url https://arquidiocesedeportovelho.org.br/paroquia/catedral-sagrado-coracao-de-jesus/
        @returns items 1 1
        @scrapes parish_name times
        """
        parish_name = response.css('h1.entry-title::text').get()

        if not parish_name:
            parish_name = response.css('h1::text').get()

        schedule_section = response.xpath(
            '//strong[contains(text(), "HORÁRIO") or contains(text(), "CELEBRAÇÕES")]'
            '/following-sibling::text() | '
            '//strong[contains(text(), "HORÁRIO") or contains(text(), "CELEBRAÇÕES")]'
            '/parent::*/following-sibling::*//text()'
        ).getall()

        if not schedule_section:
            schedule_section = response.xpath(
                '//h2[contains(text(), "Horário") or contains(text(), "horário")]'
                '/following-sibling::*//text() | '
                '//h3[contains(text(), "Horário") or contains(text(), "horário")]'
                '/following-sibling::*//text()'
            ).getall()

        times = [text.strip() for text in schedule_section if text.strip()]

        if not times:
            self.logger.info("No times found for %s", parish_name)
            return

        yield {
            "parish_name": parish_name,
            "times": times,
        }
