import scrapy


class CampoGrandeSpider(scrapy.Spider):
    name = "campo_grande"
    allowed_domains = ["arquidiocesedecampogrande.org.br"]
    start_urls = ["https://arquidiocesedecampogrande.org.br/horarios-de-missas/"]

    def parse(self, response):
        """
        Scrapes mass schedules from Arquidiocese de Campo Grande
        @url https://arquidiocesedecampogrande.org.br/horarios-de-missas/
        @scrapes parish_name day time type notes
        """
        articles = response.css('article.elementor-post')

        for article in articles:
            parish_name = article.css('h1.elementor-heading-title::text').get()
            if not parish_name:
                parish_name = article.css('h2.elementor-heading-title::text').get()

            if not parish_name:
                continue

            tables = article.css('table#HorarioMissas')
            for table in tables:
                rows = table.css('tr.jet-listing-dynamic-repeater__item')
                for row in rows:
                    cells = row.css('td::text').getall()

                    if len(cells) >= 3:
                        mass_type = cells[0]
                        day = cells[1]
                        time = cells[2]
                        notes = cells[3] if len(cells) > 3 else None

                        if day and time:
                            yield {
                                "parish_name": parish_name.strip(),
                                "type": mass_type.strip(),
                                "day": day.strip(),
                                "time": time.strip(),
                                "notes": notes.strip() if notes else None,
                            }
