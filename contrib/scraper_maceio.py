import scrapy
import json


class MaceioSpider(scrapy.Spider):
    """
    Scraper for Arquidiocese de Maceió using WordPress REST API.

    Note: This archdiocese's website uses a different structure than Natal.
    Parish information is stored as WordPress posts in the "Paróquias" category (ID 96)
    rather than as structured pages. The data is accessed via the WordPress REST API.
    """

    name = "maceio"
    allowed_domains = ["arqdemaceio.com.br"]

    # Use WordPress REST API to fetch parish posts
    # Category ID 96 = "Paróquias" (443 posts as of Nov 2025)
    start_urls = [
        "https://arqdemaceio.com.br/wp-json/wp/v2/posts?categories=96&per_page=100&page=1"
    ]

    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    def parse(self, response):
        """
        Parse WordPress API JSON response containing parish posts.
        """
        try:
            posts = json.loads(response.text)
            self.logger.info(f"Found {len(posts)} parish posts on page")

            for post in posts:
                # Extract basic parish information from the post
                parish_data = self.extract_parish_data(post)
                if parish_data:
                    yield parish_data

            # Check if there are more pages
            # WordPress REST API returns pagination info in headers
            total_pages = response.headers.get("x-wp-totalpages")
            total_posts = response.headers.get("x-wp-total")

            if total_pages:
                total_pages_int = int(total_pages.decode())
                total_posts_int = int(total_posts.decode()) if total_posts else 0
                current_page = self.get_current_page(response.url)

                self.logger.info(
                    f"Page {current_page} of {total_pages_int} "
                    f"(Total posts: {total_posts_int})"
                )

                if current_page < total_pages_int:
                    next_page = current_page + 1
                    next_url = f"https://arqdemaceio.com.br/wp-json/wp/v2/posts?categories=96&per_page=100&page={next_page}"
                    self.logger.info(f"Fetching page {next_page}...")
                    yield scrapy.Request(next_url, callback=self.parse)

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON: {e}")

    def extract_parish_data(self, post):
        """
        Extract parish information from a WordPress post.
        """
        parish_name = post.get("title", {}).get("rendered", "")
        content_html = post.get("content", {}).get("rendered", "")
        excerpt = post.get("excerpt", {}).get("rendered", "")
        post_date = post.get("date", "")
        post_url = post.get("link", "")

        # Clean HTML tags from content for basic text extraction
        # In a real implementation, you might want to parse the HTML
        # to extract structured information like addresses, phone numbers, etc.

        return {
            "parish_name": parish_name,
            "state": "Alagoas",
            "city": "Maceió",  # Most posts are about Maceió parishes
            "url": post_url,
            "date": post_date,
            "excerpt": excerpt,
            "content_html": content_html[:500],  # Truncate for preview
        }

    def get_current_page(self, url):
        """
        Extract current page number from URL.
        """
        # Look for &page= specifically to avoid matching per_page
        if "&page=" in url:
            page_param = url.split("&page=")[1]
            page_num = page_param.split("&")[0]
            return int(page_num)
        elif "?page=" in url:
            page_param = url.split("?page=")[1]
            page_num = page_param.split("&")[0]
            return int(page_num)
        return 1
