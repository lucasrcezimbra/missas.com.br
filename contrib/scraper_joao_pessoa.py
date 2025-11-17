"""
Scraper for Arquidiocese da Paraíba (João Pessoa, PB)

This scraper extracts parish Mass and confession schedules from the
Arquidiocese da Paraíba website.

The website uses Ninja Tables WordPress plugin which loads data dynamically
via JavaScript. This scraper uses Playwright to render the page and extract
the table data.

Setup:
1. Install dependencies: poetry install --with scrapers
2. Install Playwright browsers: poetry run playwright install chromium

Usage:
    poetry run scrapy runspider contrib/scraper_joao_pessoa.py -o output.jsonl

Website: https://arquidiocesepb.org.br/
Schedule page: https://arquidiocesepb.org.br/horario-de-missas-e-confissoes/
"""

import scrapy


class JoaoPessoaSpider(scrapy.Spider):
    name = "joao_pessoa"
    allowed_domains = ["arquidiocesepb.org.br"]

    custom_settings = {
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
    }

    def start_requests(self):
        yield scrapy.Request(
            url="https://arquidiocesepb.org.br/horario-de-missas-e-confissoes/",
            callback=self.parse,
            meta={
                "playwright": True,
                "playwright_include_page": True,
                "playwright_context": "default",
                "playwright_page_goto_kwargs": {
                    "wait_until": "networkidle",
                    "timeout": 60000,
                },
            },
            dont_filter=True,
        )

    async def parse(self, response):
        page = response.meta["playwright_page"]

        try:
            await page.wait_for_selector(
                "table, .ninja-table, [class*='ninja'], [id*='ninja']", timeout=20000
            )
        except Exception as e:
            self.logger.error(f"Timeout waiting for table: {e}")

            html_content = await page.content()
            self.logger.info(
                f"Page content preview: {html_content[:1000]}..."
                if len(html_content) > 1000
                else html_content
            )
            await page.close()
            return

        tables = await page.query_selector_all("table")
        self.logger.info(f"Found {len(tables)} table(s) on the page")

        for table_idx, table in enumerate(tables):
            rows = await table.query_selector_all("tr")
            self.logger.info(f"Table {table_idx}: {len(rows)} rows")

            headers = []
            for row_idx, row in enumerate(rows):
                cells = await row.query_selector_all("th, td")
                cell_texts = []

                for cell in cells:
                    text = await cell.inner_text()
                    cell_texts.append(text.strip())

                if row_idx == 0 and await row.query_selector("th"):
                    headers = cell_texts
                    self.logger.info(f"Headers: {headers}")
                elif cell_texts:
                    row_data = {"table_index": table_idx, "raw_cells": cell_texts}

                    if headers:
                        row_data["data"] = dict(zip(headers, cell_texts))

                    for i, cell_text in enumerate(cell_texts):
                        if any(
                            keyword in cell_text.lower()
                            for keyword in [
                                "paróquia",
                                "igreja",
                                "parish",
                                "church",
                            ]
                        ):
                            row_data["parish_name"] = cell_text
                            break

                    yield row_data

        await page.close()
