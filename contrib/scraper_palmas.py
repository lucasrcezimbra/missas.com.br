import scrapy


class PalmasSpider(scrapy.Spider):
    name = "palmas"
    allowed_domains = ["arquidiocesedepalmas.org.br"]
    start_urls = [
        "https://arquidiocesedepalmas.org.br/horarios-de-missa"
    ]

    def parse(self, response):
        """
        @url https://arquidiocesedepalmas.org.br/horarios-de-missas/
        @returns items 1 100
        @scrapes parish_name times
        """
        # The page uses an Elementor accordion structure
        # Parish names are in <a class="elementor-accordion-title">
        # Times are in the corresponding <div class="elementor-tab-content">

        # Find all accordion items
        accordion_items = response.css('div.elementor-accordion-item')

        for item in accordion_items:
            # Get parish name from the accordion title
            parish_name = item.css('a.elementor-accordion-title::text').get()

            if parish_name:
                # Get the content section
                content = item.css('div.elementor-tab-content')

                # Extract all text from paragraphs in the content
                times = []
                for p in content.css('p'):
                    # Get all text including from strong tags and br-separated lines
                    text = p.css('::text').getall()
                    times.extend([t.strip() for t in text if t.strip()])

                if times:
                    yield {
                        "parish_name": parish_name.strip(),
                        "times": times,
                    }
                else:
                    self.logger.info("No times found for %s", parish_name)
