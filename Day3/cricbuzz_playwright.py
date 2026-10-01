"""Wait for a visible cricket score on Cricbuzz, print it, and save score.png.

Run headed (default):
    python cricbuzz_score.py

Run headless:
    python cricbuzz_score.py --headless
"""

import argparse
import re
import sys
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


CRICBUZZ_URL = "https://www.cricbuzz.com/cricket-match/live-scores"
# Cricbuzz score text commonly contains runs-wickets (e.g. 182-4) or
# runs/wickets (e.g. 182/4). The page is inspected at runtime to find the node.
SCORE_PATTERN = re.compile(r"\b\d{1,3}\s*[-/]\s*\d{1,2}\b")
SCORE_PATTERN_TEXT = SCORE_PATTERN.pattern
SCREENSHOT_PATH = Path(__file__).resolve().with_name("score.png")


def find_visible_score(page):
    """Wait for, then inspect, the smallest visible DOM element containing a score."""
    page.wait_for_function(
        """pattern => {
            const scorePattern = new RegExp(pattern);
            return [...document.querySelectorAll('body *')].some(element => {
                const rect = element.getBoundingClientRect();
                const style = getComputedStyle(element);
                const text = (element.innerText || '').trim();
                return rect.width > 0 && rect.height > 0 &&
                    style.visibility !== 'hidden' && style.display !== 'none' &&
                    text.length > 0 && text.length < 240 && scorePattern.test(text);
            });
        }""",
        arg=SCORE_PATTERN_TEXT,
        timeout=60_000,
    )

    # Inspect the rendered DOM instead of relying on a guessed CSS class or id.
    score_element = page.evaluate(
        """pattern => {
            const scorePattern = new RegExp(pattern);
            const visible = element => {
                const rect = element.getBoundingClientRect();
                const style = getComputedStyle(element);
                return rect.width > 0 && rect.height > 0 &&
                    style.visibility !== 'hidden' && style.display !== 'none';
            };
            const matches = [...document.querySelectorAll('body *')].filter(element => {
                const text = (element.innerText || '').trim();
                return visible(element) && text.length > 0 && text.length < 240 &&
                    scorePattern.test(text);
            });
            const leafMatches = matches.filter(element =>
                ![...element.children].some(child =>
                    scorePattern.test((child.innerText || '').trim())
                )
            );
            const candidates = leafMatches.length ? leafMatches : matches;
            candidates.sort((a, b) =>
                (a.innerText || '').trim().length - (b.innerText || '').trim().length
            );
            const element = candidates[0];
            if (!element) return null;
            const scoreCard = element.closest('a') || element;
            return {
                tag: element.tagName.toLowerCase(),
                className: typeof element.className === 'string' ? element.className : '',
                text: (scoreCard.innerText || '').trim()
            };
        }""",
        SCORE_PATTERN_TEXT,
    )

    if not score_element:
        raise RuntimeError("A score appeared, but its visible page element could not be inspected.")
    return score_element


def main():
    parser = argparse.ArgumentParser(description="Capture a Cricbuzz score with Playwright.")
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run without showing the browser window.",
    )
    args = parser.parse_args()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=args.headless)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        try:
            page.goto(CRICBUZZ_URL, wait_until="domcontentloaded", timeout=60_000)
            score = find_visible_score(page)
            print("Visible score element found:")
            print(f"  HTML tag: {score['tag']}")
            if score["className"]:
                print(f"  HTML class: {score['className']}")
            print(f"  Score text: {score['text']}")

            page.screenshot(path=str(SCREENSHOT_PATH), full_page=True)
            print(f"Screenshot saved to: {SCREENSHOT_PATH}")
        except PlaywrightTimeoutError:
            print(
                "No visible score element appeared on Cricbuzz within 60 seconds. "
                "The page may have no score available or may not have loaded.",
                file=sys.stderr,
            )
            raise SystemExit(1)
        finally:
            browser.close()


if __name__ == "__main__":
    main()
