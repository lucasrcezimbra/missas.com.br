import json

import openai
import requests
from bs4 import BeautifulSoup
from decouple import config

# Set your OpenAI API key (ensure you have it in your environment)
openai.api_key = config("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("Please set the OPENAI_API_KEY environment variable.")

# --- Step 1: Get the list of cities from the main page ---
main_url = "https://www.arquipoa.com/paroquias"
main_response = requests.get(main_url)
main_response.raise_for_status()  # Raise error if the request failed

soup_main = BeautifulSoup(main_response.text, "html.parser")
select = soup_main.find("select", attrs={"onchange": "filterByCity(this.value)"})
if not select:
    raise ValueError("The target city select element was not found.")

# Build a dictionary of cities (only including options with a numeric id)
cities = {}
for option in select.find_all("option"):
    value = option.get("value", "")
    if value.isdigit():
        cities[int(value)] = option.get_text(strip=True)

print("Found cities:")
print(json.dumps(cities, indent=4, ensure_ascii=False))


# --- Step 2: For each city, make a POST request to retrieve the parish HTML ---
post_url = "https://www.arquipoa.com/pages/filterCity"
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": "https://www.arquipoa.com",
    "DNT": "1",
    "Connection": "keep-alive",
    "Referer": "https://www.arquipoa.com/paroquias",
}


def parse_parish_html_with_openai(html_snippet, city):
    """
    Call OpenAI API to parse the given HTML snippet into JSON.
    The JSON should follow this format:

    {
        "parish_name": <str>,
        "address": <str>,
        "state": "Rio Grande do Sul",
        "city": <str>,
        "phone": <str>,
        "instagram": <optional str>,
        "facebook": <optional str>,
        "email": <optional str>,
        "schedules": [
            {
                "day": <str>,
                "observation": <optional str>,
                "start_time": <HH:MM>,
                "type": <mass|confession>
            },
            ...
        ]
    }

    Note: One request is made to OpenAI per parish.
    """
    prompt = f"""
You are a helpful assistant that converts HTML code for a parish entry into a JSON object following these rules:
- The JSON object must include:
  - "parish_name": string (the name of the parish)
  - "address": string (the full address)
  - "state": fixed as "Rio Grande do Sul"
  - "city": string (set this to "{city}")
  - "phone": string in the format +55xxxxxxxxxxx
  - "instagram": optional string if available (or null)
  - "facebook": optional string if available (or null)
  - "email": optional string if available (or null)
  - "schedules": a list of objects. Each object must include:
      - "day": string (e.g., "WEDNESDAY")
      - "start_time": string formatted as HH:MM (24-hour format)
      - "observation": optional string (or null)
      - "type": string, either "mass" or "confession" (if known; if not, assume "mass")
- Do not include any extra keys.
- If some data is missing in the HTML, use null for that field.

Here is the HTML snippet to parse:
--------------------
{html_snippet}
--------------------
Return only the JSON.
"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # or another available model
            messages=[
                {
                    "role": "system",
                    "content": "You are an assistant that extracts structured data from HTML.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=500,
        )
        content = response["choices"][0]["message"]["content"].strip()
        # Try to load as JSON
        return json.loads(content)
    except Exception as e:
        print("Error during OpenAI API call:", e)
        return None


# --- Step 3: Process each city ---
all_parishes = []

for city_id, city_name in cities.items():
    if city_id == 0:
        continue
    print(f"\nRequesting parish data for city: {city_name} (ID: {city_id})")
    post_data = {"value": str(city_id)}
    post_response = requests.post(post_url, headers=headers, data=post_data)
    post_response.raise_for_status()
    html_content = post_response.text

    # Use BeautifulSoup to extract individual parish entries.
    # We assume each parish is in a <div class="row my-3 align-items-center">.
    soup_parishes = BeautifulSoup(html_content, "html.parser")
    parish_entries = soup_parishes.find_all("div", class_="row my-3 align-items-center")
    print(f"Found {len(parish_entries)} parish entries for city {city_name}.")

    for idx, parish_div in enumerate(parish_entries, start=1):
        parish_html = str(parish_div)
        print(f"\n--- Parsing parish {idx} for city {city_name} via OpenAI ---")
        parish_json = parse_parish_html_with_openai(parish_html, city_name)
        if parish_json is not None:
            all_parishes.append(parish_json)
            print(json.dumps(parish_json, indent=4, ensure_ascii=False))
        else:
            print("Failed to parse parish HTML.")
    break

# Optionally, save all parish data to a JSON file
with open("parishes.json", "w", encoding="utf-8") as f:
    json.dump(all_parishes, f, ensure_ascii=False, indent=4)

print("\n--- Completed processing all cities. ---")
