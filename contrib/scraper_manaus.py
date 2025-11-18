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
        # Get all h4 elements which contain parish names
        parish_headings = response.css('h4')

        for heading in parish_headings:
            parish_name = heading.css('::text').get()

            if not parish_name:
                continue

            # Get all following siblings until the next h4 or h2/h3
            following_content = heading.xpath(
                './following-sibling::*[following-sibling::h4 or following-sibling::h3 or following-sibling::h2]'
            )

            # If no following content found, get everything after this h4
            if not following_content:
                following_content = heading.xpath('./following-sibling::*')

            # Extract text from paragraphs and lists
            times = []
            for elem in following_content:
                # Stop if we hit another parish heading
                if elem.root.tag in ['h2', 'h3', 'h4']:
                    break

                # Extract text from the element
                text_content = elem.css('::text').getall()
                times.extend([text.strip() for text in text_content if text.strip()])

            if not times:
                self.logger.info("No schedule information found for %s", parish_name)
                continue

            yield {
                "parish_name": parish_name.strip(),
                "times": times,
            }
