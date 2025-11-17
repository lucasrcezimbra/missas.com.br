import scrapy

# TODO: This scraper needs to be updated to handle JavaScript-rendered content
# The Arquidiocese de BH website (https://arquidiocesebh.org.br/para-voce/missas/)
# loads parish data dynamically via JavaScript, which Scrapy cannot scrape by default.
#
# Options to fix this:
# 1. Use Scrapy with Splash or Selenium for JavaScript rendering
# 2. Find and use the API endpoint the website calls to load parish data
# 3. Scrape individual parish pages if they have static content
# 4. Check if the archdiocese provides parish data in another format
#
# For now, this is a placeholder based on the Natal scraper structure.


class BeloHorizonteSpider(scrapy.Spider):
    name = "bh"
    allowed_domains = ["arquidiocesebh.org.br"]
    start_urls = [
        "https://arquidiocesebh.org.br/para-voce/missas/"
    ]

    def parse(self, response):
        """
        @url https://arquidiocesebh.org.br/para-voce/missas/
        @returns items 0
        @scrapes parish_name times
        """
        self.logger.warning(
            "This scraper requires JavaScript rendering support. "
            "The page content is loaded dynamically and cannot be scraped with basic Scrapy."
        )

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
