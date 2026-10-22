
import requests
from bs4 import BeautifulSoup

# Website we want to scrape
URL = "https://www.bbc.com/news"

# A normal browser User-Agent
HEADERS = {"User-Agent": "Mozilla/5.0"}

try:
    # Fetch the webpage
    response = requests.get(URL, headers=HEADERS, timeout=10)

    # Check the HTTP status before parsing
    response.raise_for_status()

    # Convert the HTML into a searchable structure
    soup = BeautifulSoup(response.text, "html.parser")

    # CSS selector to verify using browser inspection
    items = soup.select('h2[data-testid="card-headline"]')

    # Remove empty and duplicate headlines
    headlines = []
    seen = set()

    for item in items:
        headline = " ".join(item.stripped_strings)

        if not headline or headline in seen:
            continue

        seen.add(headline)
        headlines.append(headline)

        if len(headlines) == 5:
            break

    # Print only the headlines, numbered 1 to 5
    for number, headline in enumerate(headlines, 1):
        print(f"{number}. {headline}")

    # Handle pages with fewer than five headlines
    if len(headlines) < 5:
        print(f"Only {len(headlines)} headlines found.")

except requests.RequestException as error:
    print(f"Failed to fetch news: {error}")
