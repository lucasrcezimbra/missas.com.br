import scrapy


class PortoVelhoSpider(scrapy.Spider):
    name = "porto_velho"
    allowed_domains = ["arquidiocesedeportovelho.org.br"]
    start_urls = ["https://arquidiocesedeportovelho.org.br/paroquias/"]

    def parse(self, response):
        """
        Parse the main parishes listing page and follow links to individual parish pages.
        @url https://arquidiocesedeportovelho.org.br/paroquias/
        @returns requests
        """
        # Extract all links to individual parish pages
        parish_links = response.css('a[href*="/paroquia/"]::attr(href)').getall()

        # Follow each parish link
        for link in parish_links:
            yield response.follow(link, callback=self.parse_parish)

    def parse_parish(self, response):
        """
        Parse an individual parish page to extract name and mass schedule.
        @scrapes parish_name times
        """
        # Extract parish name from h1 or h2 heading
        parish_name = (
            response.css("h1::text").get()
            or response.css("h2::text").get()
            or response.css("title::text").get()
        )

        if not parish_name:
            self.logger.warning("No parish name found for %s", response.url)
            return

        parish_name = parish_name.strip()

        # Look for mass schedule section
        # Try to find text containing schedule keywords
        schedule_text = []

        # Strategy 1: Look for paragraphs containing time patterns or schedule keywords
        paragraphs = response.css("p ::text").getall()

        # Filter for relevant schedule information
        # Look for paragraphs with time patterns (e.g., "18h", "6h30")
        # or day keywords (Domingo, Segunda, etc.)
        schedule_keywords = [
            "horário",
            "celebração",
            "missa",
            "domingo",
            "segunda",
            "terça",
            "quarta",
            "quinta",
            "sexta",
            "sábado",
        ]

        collecting = False
        for text in paragraphs:
            text_lower = text.lower().strip()

            # Start collecting when we find schedule-related keywords
            if any(keyword in text_lower for keyword in schedule_keywords):
                collecting = True

            # Collect text if we're in schedule section and it has content
            if collecting and text.strip():
                # Check if this line contains time information or day information
                if any(keyword in text_lower for keyword in schedule_keywords) or "h" in text_lower:
                    schedule_text.append(text.strip())
                # Stop collecting if we hit a section that doesn't look like schedule
                elif len(schedule_text) > 0 and not any(c.isdigit() for c in text):
                    # If we already collected some schedule and this line has no digits, stop
                    if len(text_lower) > 50:  # Long text without digits = new section
                        break

        # If we didn't find schedule using paragraph parsing, try other approaches
        if not schedule_text:
            # Try to extract all text and look for schedule patterns
            all_text = response.css("body ::text").getall()
            for i, text in enumerate(all_text):
                text_lower = text.lower().strip()
                if "horário" in text_lower and "celebra" in text_lower:
                    # Found schedule header, collect next few lines
                    schedule_text = [
                        t.strip()
                        for t in all_text[i : i + 15]
                        if t.strip() and len(t.strip()) > 3
                    ]
                    break

        if not schedule_text:
            self.logger.info("No schedule found for %s", parish_name)
            return

        yield {
            "parish_name": parish_name,
            "times": schedule_text,
        }
