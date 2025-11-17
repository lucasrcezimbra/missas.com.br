import scrapy


class FortalezaSpider(scrapy.Spider):
    name = "fortaleza"
    allowed_domains = ["www.arquidiocesedefortaleza.org.br"]
    start_urls = ["https://www.arquidiocesedefortaleza.org.br/arquidiocese/regioes/"]

    def parse(self, response):
        """
        Parse the main regions page and follow links to individual regions.
        """
        region_links = response.css("ul li a::attr(href)").getall()

        for url in region_links:
            if "/regiao-" in url:
                yield response.follow(url, self.parse_region)

    def parse_region(self, response):
        """
        Parse a region page and look for the parishes list link.
        """
        parishes_links = response.css("a::attr(href)").getall()

        for url in parishes_links:
            if "paroquias-da-regiao" in url:
                yield response.follow(url, self.parse_parishes_list)
                break

    def parse_parishes_list(self, response):
        """
        Parse the parishes list page and extract parish information.

        @scrapes parish_name location region_url
        """
        region_name = response.url.split("/regiao-")[1].split("/")[0]

        for parish_link in response.css("ul li a"):
            parish_text = parish_link.css("::text").get()
            parish_url = parish_link.css("::attr(href)").get()

            if not parish_text or not parish_url:
                continue

            parish_keywords = ["paroquia", "area-pastoral", "santuario"]
            if not any(keyword in parish_url.lower() for keyword in parish_keywords):
                continue

            parts = [p.strip() for p in parish_text.split(",")]
            parish_name = parts[0] if parts else parish_text
            location = parts[1] if len(parts) > 1 else ""

            yield {
                "parish_name": parish_name,
                "location": location,
                "region": region_name,
                "parish_url": response.urljoin(parish_url),
                "region_url": response.url,
            }
