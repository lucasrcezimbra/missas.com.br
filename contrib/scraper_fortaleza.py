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
        Parse the parishes list page and follow links to individual parishes.
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

            yield response.follow(
                parish_url,
                self.parse_parish_page,
                meta={
                    "parish_name": parish_name,
                    "location": location,
                    "region": region_name,
                    "region_url": response.url,
                },
            )

    def parse_parish_page(self, response):
        """
        Parse individual parish page to extract schedules and contact information.

        @scrapes parish_name location region schedule address phone email
        """
        parish_name = response.meta["parish_name"]
        location = response.meta["location"]
        region = response.meta["region"]
        region_url = response.meta["region_url"]

        content_area = response.css("article, .entry-content, main")

        schedules_text = []
        for section in content_area:
            text_content = section.css("::text").getall()
            schedules_text.extend([t.strip() for t in text_content if t.strip()])

        phone_numbers = []
        for link in response.css('a[href*="tel:"]'):
            phone = link.css("::text").get()
            if phone:
                phone_numbers.append(phone.strip())

        emails = []
        for link in response.css('a[href*="mailto:"]'):
            email = link.attrib.get("href", "").replace("mailto:", "")
            if email:
                emails.append(email.strip())

        yield {
            "parish_name": parish_name,
            "location": location,
            "region": region,
            "parish_url": response.url,
            "region_url": region_url,
            "schedule_text": "\n".join(schedules_text),
            "phones": ", ".join(phone_numbers),
            "emails": ", ".join(emails),
        }
