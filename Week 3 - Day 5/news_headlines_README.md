# BBC News Headlines Scraper

**Week 3 · Day 5 — Print the Top 5 Headlines from a News Site**

A beginner-friendly Python project that fetches BBC News headlines and prints five unique, numbered headlines in the terminal using `requests` and `BeautifulSoup`.

## Features

- Fetches BBC News with a normal `User-Agent` and a request timeout
- Checks the HTTP status code before parsing the response
- Extracts headlines using an HTML selector verified in browser DevTools
- Strips whitespace and skips empty or duplicate headlines
- Prints up to five headlines, numbered 1–5
- Handles HTTP errors and cases where fewer than five headlines are available

## Technologies

- Python
- [requests](https://requests.readthedocs.io/)
- [Beautiful Soup 4](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)

## Project structure

```text
headlines/
├── headlines.py
└── README.md
```

Keep the local `venv/` directory out of GitHub.

## Setup and installation

1. Clone your GitHub repository, or download `headlines.py` into a folder.
2. Open a terminal in that folder.
3. Create a virtual environment:

   ```powershell
   python -m venv venv
   ```

4. Activate it on Windows PowerShell:

   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

   On macOS/Linux instead use `source venv/bin/activate`.

5. Install the dependencies:

   ```powershell
   python -m pip install requests beautifulsoup4
   ```

6. Run the script:

   ```powershell
   python headlines.py
   ```

## How it works

1. `requests.get()` fetches the HTML from `https://www.bbc.com/news`.
2. `response.raise_for_status()` checks for HTTP errors.
3. `BeautifulSoup` parses the HTML.
4. The scraper selects the headline elements, removes extra whitespace and duplicates, and prints the first five unique headlines.

### Inspecting the headline selector

The page was inspected using **Chrome DevTools → Elements**. The observed headline was inside an `h2` element with `data-testid="card-headline"`:

```html
<h2 data-testid="card-headline">Example BBC headline</h2>
```

The corresponding CSS selector is:

```css
h2[data-testid="card-headline"]
```

BBC can change its page structure or serve different HTML to a Python request. If the scraper returns fewer than five headlines, inspect the current page and update the selector as needed.

## Example terminal output

```text
python headlines.py
1. Example news headline one
2. Example news headline two
3. Example news headline three
4. Example news headline four
5. Example news headline five
```

*Illustrative output; actual headlines change.*

## Assignment requirements

- [x] Write one Python file named `headlines.py`
- [x] Use `requests` with a `User-Agent` and check the response status
- [x] Inspect the page to identify a real headline element
- [x] Use BeautifulSoup to extract headlines
- [x] Remove empty and duplicate entries
- [x] Print five numbered headlines when available
- [x] Handle fewer than five headlines
- [x] Capture a screenshot of five headlines printed in the terminal
- [ ] Push `headlines.py` and this README to GitHub
- [ ] Share the GitHub link in WhatsApp
- [ ] Post a screen-recorded demo in the course community

## What I learned

How to fetch web pages with Python, inspect HTML elements, use CSS selectors, extract information with BeautifulSoup, handle HTTP errors, and present clean terminal output.

## Note

This project is for learning. Follow the news site's terms and reasonable request rates. JavaScript-rendered pages may not expose their headlines to `requests` alone.
