import scrapy


class AracajuSpider(scrapy.Spider):
    name = "aracaju"
    allowed_domains = ["arquidiocesedearacaju.org"]
    start_urls = [
        "https://arquidiocesedearacaju.org/horarios-de-missa/"
    ]

    def parse(self, response):
        """
        @url https://arquidiocesedearacaju.org/horarios-de-missa/
        @scrapes parish_name times
        """
        # Find all parish containers (each parish is in an e-loop-item div)
        for parish_div in response.css('div.e-loop-item.paroquias'):
            # Extract parish name from h1 inside this container
            parish_name = parish_div.css('h1.elementor-heading-title::text').get()

            if not parish_name:
                continue

            parish_name = parish_name.strip()

            # Find the table within this parish container
            table = parish_div.css('table.dce-acf-repeater-table')

            if not table:
                self.logger.info("No schedule table found for %s", parish_name)
                continue

            # Extract schedule data from table rows (skip header rows)
            times = []
            for row in table.css('tr'):
                # Skip header rows (those with class 'tit-tabela' or containing 'Tipo')
                if row.css('.tit-tabela') or 'Tipo' in row.css('td::text').get(''):
                    continue

                cells = row.css('td::text').getall()
                if cells and len(cells) >= 3:
                    # Join all cells to create a schedule entry
                    row_text = ' | '.join([cell.strip() for cell in cells if cell.strip()])
                    if row_text:
                        times.append(row_text)

            if not times:
                self.logger.info("No schedule times found for %s", parish_name)
                continue

            yield {
                "parish_name": parish_name,
                "times": times,
            }
