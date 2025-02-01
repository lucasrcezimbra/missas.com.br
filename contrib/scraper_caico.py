import requests
from bs4 import BeautifulSoup

url = "https://diocesecaico.com/horario-das-missas/"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36"
}

response = requests.get(url, headers=headers, timeout=100)
response.raise_for_status()

soup = BeautifulSoup(response.content, "html.parser")

content_mapping = {}
for content_div in soup.find_all(
    "div", class_="elementor-tab-content elementor-clearfix"
):
    data_tab = content_div.get("data-tab")
    if data_tab:
        content_mapping[data_tab] = content_div

days = {}
for tab_title in soup.find_all(
    "div", class_="elementor-tab-title elementor-tab-mobile-title"
):
    day_name = tab_title.get_text(strip=True)
    data_tab = tab_title.get("data-tab")
    if data_tab and data_tab in content_mapping:
        day_content = content_mapping[data_tab].get_text(separator="\n", strip=True)
        days[day_name] = day_content

for day, content in days.items():
    print(f"{day}:\n")
    print(content)
    print("\n" + "=" * 40 + "\n")

# TODO: parse
