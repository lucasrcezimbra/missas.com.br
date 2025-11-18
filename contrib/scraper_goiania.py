"""
Scraper for Arquidiocese de Goiânia parish data.

The Goiânia archdiocese website uses WordPress with a custom post type "paroquia".
This scraper attempts to access parish data via the WordPress REST API.

Website: https://arquidiocesedegoiania.org.br/
Mass schedules page: https://arquidiocesedegoiania.org.br/horarios-de-missas/

Website details:
- 132 parishes total across 24 Foranias and 5 Vicariatos
- Custom post type: "paroquia"
- Uses JetSmartFilters plugin for dynamic filtering
"""

import json
import scrapy
from urllib.parse import urljoin


class GoianiaSpider(scrapy.Spider):
    name = "goiania"
    allowed_domains = ["arquidiocesedegoiania.org.br"]

    def start_requests(self):
        """
        Try to access parish data via WordPress REST API.
        """
        # WordPress REST API endpoint for custom post type
        # Try different possible endpoints
        api_endpoints = [
            "https://arquidiocesedegoiania.org.br/wp-json/wp/v2/paroquia",
            "https://arquidiocesedegoiania.org.br/wp-json/wp/v2/paroquias",
            "https://arquidiocesedegoiania.org.br/wp-json/wp/v2/posts?type=paroquia",
        ]

        for endpoint in api_endpoints:
            # Add per_page parameter to get more results (max is usually 100)
            url = f"{endpoint}?per_page=100&page=1"
            yield scrapy.Request(
                url,
                callback=self.parse_api_response,
                errback=self.handle_error,
                meta={'page': 1, 'endpoint': endpoint}
            )

    def handle_error(self, failure):
        """
        Handle request errors gracefully.
        """
        self.logger.debug(f"Request failed for {failure.request.url}: {failure.value}")

    def parse_api_response(self, response):
        """
        Parse WordPress REST API JSON response.
        """
        if response.status == 404:
            self.logger.debug(f"Endpoint not found: {response.url}")
            return

        try:
            data = json.loads(response.text)

            if not data:
                self.logger.info(f"No more data at {response.url}")
                return

            self.logger.info(f"Found {len(data)} items on page {response.meta['page']}")

            for parish in data:
                # Extract parish information from API response
                parish_name = parish.get('title', {}).get('rendered', '')
                link = parish.get('link', '')

                # Only process URLs that are actual parish pages (not news/blog posts)
                if parish_name and link and '/paroquia/' in link:
                    yield scrapy.Request(
                        link,
                        callback=self.parse_parish_detail,
                        meta={'parish_name': parish_name}
                    )

            # Check if there are more pages
            # WordPress REST API includes total pages in headers
            total_pages = response.headers.get('X-WP-TotalPages')
            if total_pages:
                total_pages = int(total_pages)
                current_page = response.meta['page']
                if current_page < total_pages:
                    next_page = current_page + 1
                    endpoint = response.meta['endpoint']
                    next_url = f"{endpoint}?per_page=100&page={next_page}"
                    yield scrapy.Request(
                        next_url,
                        callback=self.parse_api_response,
                        errback=self.handle_error,
                        meta={'page': next_page, 'endpoint': endpoint}
                    )

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON from {response.url}: {e}")

    def parse_parish_detail(self, response):
        """
        Parse individual parish page to extract schedule information.
        """
        parish_name = response.meta.get('parish_name')

        if not parish_name:
            parish_name = response.css('h1.entry-title::text, h1::text').get()

        if not parish_name:
            parish_name = response.css('title::text').get()
            if parish_name:
                parish_name = parish_name.split('|')[0].strip()

        # Clean up HTML entities in parish name
        if parish_name:
            parish_name = parish_name.replace('&#8211;', '–').replace('&amp;', '&')

        schedule_data = []

        # Look for tables with schedule information
        for table in response.css('table'):
            for row in table.css('tr'):
                cells = row.css('td::text, th::text').getall()
                cleaned_cells = [c.strip() for c in cells if c.strip()]
                if cleaned_cells:
                    schedule_data.extend(cleaned_cells)

        # Alternative: look for specific content sections (avoid navigation and scripts)
        if not schedule_data:
            # Try to find the main content area
            content_selectors = [
                'article .entry-content',
                '.post-content',
                'main [class*="content"]',
                '.single-paroquia',
            ]

            for selector in content_selectors:
                content_area = response.css(selector).get()
                if content_area:
                    # Parse the content area to extract text
                    content_response = scrapy.Selector(text=content_area)

                    # Look for paragraphs and list items with relevant keywords
                    relevant_text = []
                    for elem in content_response.css('p, li, h2, h3, h4, strong'):
                        text = elem.css('::text').getall()
                        text = ' '.join([t.strip() for t in text if t.strip()])

                        # Filter out CSS, JavaScript, and navigation items
                        if (text and len(text) > 3
                            and not text.startswith('var ')
                            and not text.startswith('.')
                            and not text.startswith('@media')
                            and 'elementor' not in text.lower()
                            and text not in ['Menu', 'Home', 'Facebook', 'Instagram', 'Youtube']
                        ):
                            relevant_text.append(text)

                    if relevant_text:
                        schedule_data = relevant_text
                        break

        if parish_name and schedule_data:
            yield {
                "parish_name": parish_name.strip(),
                "times": schedule_data,
                "url": response.url,
            }
        else:
            self.logger.debug(f"Could not extract schedule data from {response.url}")
