import scrapy


class BelemSpider(scrapy.Spider):
    """
    Scraper for Arquidiocese de Belém do Pará.

    NOTE: This website loads parish data dynamically via AJAX/JavaScript,
    which means this basic Scrapy spider will not work as-is. To successfully
    scrape this site, you would need to use one of the following approaches:

    1. Scrapy-Splash or Selenium to render JavaScript
    2. Reverse-engineer the AJAX API endpoints and make direct requests
    3. Find alternative static pages with the data (none found so far)

    Current implementation tries multiple potential URLs but will likely
    return no results since the data is not in static HTML.
    """

    name = "belem"
    allowed_domains = ["arquidiocesedebelem.com.br"]
    start_urls = [
        "https://arquidiocesedebelem.com.br/search-home/",
        "https://arquidiocesedebelem.com.br/paroquias-missas/",
        "https://arquidiocesedebelem.com.br/arq-paroquias-e-missas/",
        "https://arquidiocesedebelem.com.br/paroquias-e-missas/",
    ]

    def parse(self, response):
        """
        @url https://arquidiocesedebelem.com.br/search-home/
        @returns items 0 100
        @scrapes parish_name times
        """
        # Try to find parish cards (will be empty in static HTML)
        for parish in response.css(".parish"):
            parish_name = self._extract_parish_name(parish)
            times = self._extract_times(parish)

            if not parish_name:
                self.logger.debug("No parish name found, skipping")
                continue

            if not times:
                self.logger.info("No times found for %s", parish_name)
                continue

            yield {
                "parish_name": parish_name.strip(),
                "times": times,
            }

    def _extract_parish_name(self, parish):
        """Extract parish name from various possible selectors."""
        parish_name = parish.css("h3::text, h2::text, h1::text").get()
        if not parish_name:
            parish_name = parish.css(".parish-name::text, .title::text").get()
        return parish_name

    def _extract_times(self, parish):
        """Extract mass times from various possible selectors."""
        times = []

        # Try extracting from time details
        times.extend(parish.css(".mec-time-details ::text").getall())

        # Try extracting from list items
        times.extend(parish.css(".h-list > li ::text").getall())

        # Try extracting from general paragraph text
        if not times:
            times.extend(parish.css("p ::text").getall())

        # Clean up the times list
        return [t.strip() for t in times if t.strip()]
