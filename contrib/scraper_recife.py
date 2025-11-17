import scrapy


class RecifeSpider(scrapy.Spider):
    name = "recife"
    allowed_domains = ["www.arquidioceseolindarecife.org"]
    start_urls = ["https://www.arquidioceseolindarecife.org/horarios-de-missas/"]

    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36"
    }

    def parse(self, response):
        """
        @url https://www.arquidioceseolindarecife.org/horarios-de-missas/
        @returns items 100 150
        @scrapes parish_name location times
        """
        paragraphs = response.css("div.entry-content p")

        for p in paragraphs:
            strong_text = p.css("strong::text").get()

            if not strong_text:
                continue

            strong_text = strong_text.strip()

            if strong_text in ["BASÍLICAS", "SANTUÁRIOS", "ORATÓRIOS", "PARÓQUIAS"]:
                continue

            all_text = p.css("::text").getall()
            all_text = [t.strip() for t in all_text if t.strip()]

            times = [t for t in all_text if t != strong_text]

            location = None
            parish_name = strong_text
            if " – " in parish_name:
                parts = parish_name.split(" – ", 1)
                parish_name = parts[0].strip()
                location = parts[1].strip()

            yield {
                "parish_name": parish_name,
                "location": location,
                "times": times,
            }
