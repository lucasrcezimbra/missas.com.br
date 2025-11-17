"""
Scraper for Arquidiocese da Paraíba (João Pessoa, PB) - Anuário Digital

This scraper extracts parish information from the digital annual directory
at http://162.241.101.195/~lumenpastoral/anuario/paroquias

The data includes:
- Parish names and patron saints
- Year of creation
- Addresses with city and state
- Contact information (phones, emails)
- Active clergy

Usage:
    poetry run python contrib/scraper_joao_pessoa_anuario.py

Output:
    Prints JSON to stdout (redirect to file with > output.jsonl)
"""

import json
import re

import requests
from bs4 import BeautifulSoup

BASE_URL = "http://162.241.101.195/~lumenpastoral/anuario"
PARISHES_URL = f"{BASE_URL}/paroquias"


def get_forania_links():
    """Get all Forania (regional grouping) links from the main parishes page."""
    response = requests.get(PARISHES_URL, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "html.parser")

    forania_links = []
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if "paroquias/list?forania_description=" in href:
            forania_name = link.get_text(strip=True)
            # Clean up the forania name (remove extra text like "label_important")
            forania_name = re.sub(
                r"label_important|Forania|Cidade\(s\):.*", "", forania_name
            ).strip()

            if not href.startswith("http"):
                href = BASE_URL + href.replace("~lumenpastoral/anuario", "")

            forania_links.append({"name": forania_name, "url": href})

    # Deduplicate by URL
    seen_urls = set()
    unique_links = []
    for link in forania_links:
        if link["url"] not in seen_urls:
            seen_urls.add(link["url"])
            unique_links.append(link)

    return unique_links


def extract_parish_data(parish_div, forania_name):
    """Extract data from a single parish div."""
    parish_data = {"forania": forania_name}

    # Find the parish title in the title div
    title_elem = parish_div.find(
        "div", class_="anuario-titulo-listagem-paroquias-e-clerigos"
    )
    if title_elem:
        # Remove the icon text and city/state info from parish name
        parish_name = title_elem.get_text(strip=True)
        parish_name = parish_name.replace("label_important", "")
        # Remove city and state from the end (they appear in a separate element)
        parish_name = re.sub(r"[A-Z][a-zçáéíóúâêôãõ\s]+\s*-\s*PB.*$", "", parish_name)
        parish_data["parish_name"] = parish_name.strip()

    # Find city and state from the orange text
    city_elem = parish_div.find("small", class_="orange-text")
    if city_elem:
        city_text = city_elem.get_text(strip=True)
        # Remove "- PB" and extract city
        city = city_text.replace("- PB", "").replace("-PB", "").strip()
        if city:
            parish_data["city"] = city
            parish_data["state"] = "PB"

    # Extract information from the info boxes
    info_boxes = parish_div.find_all(
        "div",
        class_=lambda c: c
        and "anuario-box-informacoes-de-uma-paroquia-ou-clerigo" in c,
    )

    for box in info_boxes:
        text = box.get_text(separator="\n", strip=True)

        if "Ano de Criação:" in text:
            year_match = re.search(r"Ano de Criação:\s*(\d+)", text)
            if year_match:
                parish_data["year_created"] = int(year_match.group(1))

        elif "Endereço:" in text:
            address_text = re.sub(r"Endereço:\s*", "", text, flags=re.IGNORECASE)
            # Clean up material icons and extra whitespace
            address_text = re.sub(r"done\s*", "", address_text)
            address_text = re.sub(r"\s+", " ", address_text)
            address_text = address_text.strip()
            if address_text and "Não há" not in address_text:
                parish_data["address"] = address_text

        elif "Contatos:" in text:
            # Extract phone numbers
            phones = re.findall(r"\(?\d{2}\)?\s*\d{4,5}-?\d{4}", text)
            if phones:
                parish_data["phones"] = phones

            # Extract emails
            emails = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", text)
            if emails:
                parish_data["emails"] = emails

        elif "Clérigos Atuantes:" in text:
            clergy_text = re.sub(
                r"Clérigos Atuantes:\s*", "", text, flags=re.IGNORECASE
            )
            # Clean up material icons
            clergy_text = re.sub(r"done\s*", "", clergy_text)
            clergy_text = re.sub(r"\s+", " ", clergy_text)
            clergy_text = clergy_text.strip()
            if clergy_text and "Não há" not in clergy_text:
                parish_data["clergy"] = clergy_text

    return parish_data


def scrape_forania(forania):
    """Scrape all parishes from a single Forania."""
    # Clean up the forania name
    forania_clean_name = re.sub(r"done.*$", "", forania["name"]).strip()
    forania_clean_name = re.sub(r"\s+", " ", forania_clean_name)

    print(f"Scraping {forania_clean_name}...", file=__import__("sys").stderr)

    response = requests.get(forania["url"], timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "html.parser")

    parishes = []

    # Look for parish containers - each parish is in a row
    parish_rows = soup.find_all("div", class_="anuario-wrapper-listagem-com-imagens")

    for row in parish_rows:
        parish_data = extract_parish_data(row, forania_clean_name)
        if parish_data.get("parish_name"):
            parishes.append(parish_data)

    return parishes


def main():
    """Main scraper function."""
    print("Fetching Forania links...", file=__import__("sys").stderr)
    foranias = get_forania_links()

    print(
        f"Found {len(foranias)} Foranias: {[f['name'] for f in foranias]}",
        file=__import__("sys").stderr,
    )

    all_parishes = []

    for forania in foranias:
        try:
            parishes = scrape_forania(forania)
            all_parishes.extend(parishes)
            print(
                f"  Found {len(parishes)} parishes in {forania['name']}",
                file=__import__("sys").stderr,
            )
        except Exception as e:
            print(
                f"  Error scraping {forania['name']}: {e}",
                file=__import__("sys").stderr,
            )

    print(
        f"\nTotal parishes scraped: {len(all_parishes)}",
        file=__import__("sys").stderr,
    )

    # Output as JSONL
    for parish in all_parishes:
        print(json.dumps(parish, ensure_ascii=False))


if __name__ == "__main__":
    main()
