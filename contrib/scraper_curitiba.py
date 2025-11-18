import scrapy


class CuritibaSpider(scrapy.Spider):
    """
    Spider to scrape parish and Mass schedule data from Arquidiocese de Curitiba website.

    NOTE: This website heavily relies on JavaScript to load Mass schedule information.
    The current implementation extracts parish names and URLs, but Mass schedule data
    requires JavaScript rendering (Scrapy-Playwright or Scrapy-Splash).

    To fully extract Mass schedules, you'll need to:
    1. Install scrapy-playwright: poetry add scrapy-playwright
    2. Update settings.py to enable Playwright middleware
    3. Update parse_parish to wait for AJAX-loaded schedule content
    """

    name = "curitiba"
    allowed_domains = ["arquidiocesedecuritiba.org.br"]
    start_urls = ["https://arquidiocesedecuritiba.org.br/paroquias/"]

    # Enable Playwright if available (uncomment when scrapy-playwright is installed)
    # custom_settings = {
    #     "DOWNLOAD_HANDLERS": {
    #         "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    #     },
    #     "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
    # }

    def parse(self, response):
        """
        Parse the parishes listing page and follow links to individual parish pages.

        @url https://arquidiocesedecuritiba.org.br/paroquias/
        @returns items 0 0
        @returns requests 10 100
        """
        parish_links = response.css('a[href*="/paroquia/"]::attr(href)').getall()

        for link in set(parish_links):
            yield response.follow(link, self.parse_parish)

        next_page_links = response.css(
            "a.page-numbers:not(.current)::attr(href)"
        ).getall()
        for next_page in next_page_links:
            yield response.follow(next_page, self.parse)

    def parse_parish(self, response):
        """
        Extract parish information and Mass schedules from individual parish pages.

        Note: Mass schedule data is loaded via JavaScript and won't appear
        without a JavaScript-enabled browser.

        @url https://arquidiocesedecuritiba.org.br/paroquia/capelania-da-aeronautica/
        @returns items 0 1
        @scrapes parish_name parish_url
        """
        # Parish name is in a span element, often with specific styling
        parish_name = response.css("span.text-\\[\\#A8A8A8\\]::text").get()

        if not parish_name:
            # Try alternative selectors
            parish_name = response.css("h1::text, h2::text").get()

        if not parish_name:
            self.logger.warning("No parish name found on %s", response.url)
            return

        # Extract slug from URL for identification
        slug = response.url.rstrip("/").split("/")[-1]

        # Try to extract schedule data (will be empty without JavaScript rendering)
        schedule_rows = response.css("table tr")

        if schedule_rows:
            for row in schedule_rows:
                days_text = row.css("td:first-child::text").getall()
                times_text = row.css("td:nth-child(2)::text").getall()

                days = [d.strip() for d in days_text if d.strip()]
                times = [t.strip() for t in times_text if t.strip()]

                if days and times:
                    yield {
                        "parish_name": parish_name.strip(),
                        "parish_url": response.url,
                        "slug": slug,
                        "days": ", ".join(days),
                        "times": ", ".join(times),
                    }
        else:
            # No schedule data found (expected without JavaScript rendering)
            self.logger.info(
                "No schedule data found for %s (requires JavaScript)", parish_name
            )
            yield {
                "parish_name": parish_name.strip(),
                "parish_url": response.url,
                "slug": slug,
                "days": None,
                "times": None,
                "note": "Schedule data requires JavaScript rendering",
            }
