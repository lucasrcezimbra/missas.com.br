import scrapy


class CuiabaSpider(scrapy.Spider):
    name = "cuiaba"
    allowed_domains = ["arquidiocesecuiaba.org.br"]
    start_urls = ["https://arquidiocesecuiaba.org.br/horarios-de-missas/"]

    def parse(self, response):
        """
        @url https://arquidiocesecuiaba.org.br/horarios-de-missas/
        @returns items 1
        @scrapes parish_name schedule_data
        """
        parish_divs = response.xpath('//div[.//h2 and .//table]')

        for div in parish_divs:
            heading = div.xpath('.//h2')
            if not heading:
                continue

            parish_name = heading.xpath(".//text()").get()
            if not parish_name:
                continue

            parish_name = parish_name.strip()

            table = div.xpath('.//table')
            if not table:
                self.logger.info("No table found for %s", parish_name)
                continue

            schedule_data = []
            for row in table.xpath(".//tr[position() > 1]"):
                cells = row.xpath(".//td//text()").getall()
                cells = [cell.strip() for cell in cells if cell.strip()]

                if len(cells) >= 3:
                    schedule_data.append(
                        {
                            "tipo": cells[0],
                            "dia_da_semana": cells[1],
                            "horario": cells[2],
                        }
                    )

            if not schedule_data:
                self.logger.info("No schedule data found for %s", parish_name)
                continue

            yield {
                "parish_name": parish_name,
                "schedule_data": schedule_data,
            }
