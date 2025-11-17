"""
Simple scraper for Arquidiocese da Paraíba (João Pessoa, PB)

This is a fallback scraper that fetches the HTML without JavaScript rendering.
Use this to inspect the page structure manually if the Playwright version
doesn't work in your environment.

The data will need to be extracted manually from the HTML or by copying
from the rendered page in a browser.

Usage:
    poetry run python contrib/scraper_joao_pessoa_simple.py
"""

import requests
from bs4 import BeautifulSoup


def main():
    url = "https://arquidiocesepb.org.br/horario-de-missas-e-confissoes/"

    print(f"Fetching {url}...")
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "html.parser")

    print("\n=== Checking for Ninja Tables shortcode ===")
    ninja_shortcode = soup.find_all(string=lambda text: "ninja_tables" in text.lower())
    for shortcode in ninja_shortcode:
        print(f"Found: {shortcode.strip()}")

    print("\n=== Looking for table-related elements ===")
    table_elements = soup.find_all(
        ["table", "div"], class_=lambda c: c and ("table" in c or "ninja" in c)
    )
    print(f"Found {len(table_elements)} elements")

    print("\n=== Page scripts ===")
    scripts = soup.find_all("script")
    print(f"Found {len(scripts)} script tags")

    ninja_scripts = [
        s for s in scripts if s.string and "ninja" in s.string.lower()
    ]
    if ninja_scripts:
        print(f"\nFound {len(ninja_scripts)} scripts mentioning 'ninja'")
        for script in ninja_scripts[:2]:
            print(f"Script preview: {str(script)[:200]}...")

    print("\n=== Recommendation ===")
    print(
        "The table data is loaded via JavaScript (Ninja Tables plugin)."
    )
    print("To extract the data, you can:")
    print("1. Use the Playwright-based scraper (scraper_joao_pessoa.py)")
    print("2. Manually open the page in a browser and copy the table data")
    print("3. Use browser DevTools to inspect the AJAX requests")
    print("4. Contact the diocese for a data export")

    print(f"\nHTML saved to /tmp/joao_pessoa.html for manual inspection")
    with open("/tmp/joao_pessoa.html", "w", encoding="utf-8") as f:
        f.write(response.text)


if __name__ == "__main__":
    main()
