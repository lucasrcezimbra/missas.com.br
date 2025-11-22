import scrapy


class ManausSpider(scrapy.Spider):
    name = "manaus"
    allowed_domains = ["arquidiocesedemanaus.org.br"]
    start_urls = ["https://arquidiocesedemanaus.org.br/paroquias/"]

    def parse(self, response):
        """
        Parse the main parishes page to extract all parish information.

        @url https://arquidiocesedemanaus.org.br/paroquias/
        @returns items 50 100
        @scrapes parish_name times
        """
        parish_headings = response.css('h2.wp-block-heading')

        for heading in parish_headings:
            parish_name = heading.css('::text').get()

            if not parish_name:
                parish_name = heading.xpath('.//text()').get()

            if not parish_name:
                continue

            # Collect all content between this h2 and the next h2
            following_content = []
            for sibling in heading.xpath('./following-sibling::*'):
                # Stop if we hit another parish h2
                sibling_classes = sibling.xpath('@class').get()
                if (sibling.root.tag == 'h2' and
                    sibling_classes and
                    'wp-block-heading' in sibling_classes):
                    break
                following_content.append(sibling)

            # Extract text from all elements
            times = []
            for elem in following_content:
                text_content = elem.css('::text').getall()
                times.extend([text.strip() for text in text_content if text.strip()])

            if not times:
                self.logger.info("No schedule information found for %s", parish_name)
                continue

            yield {
                "parish_name": parish_name.strip(),
                "times": times,
            }
