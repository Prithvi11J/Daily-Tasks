"""Capture India's current Goodreturns gold rates and enter them in Excel for the web.

Install once in the VS Code terminal:
    py -m pip install pyautogui requests beautifulsoup4 pyperclip pygetwindow

Run:
    py gold_rate_automation.py
"""

from datetime import datetime
from pathlib import Path
import re
import time

import pyautogui
import pyperclip
import pygetwindow
import requests
from bs4 import BeautifulSoup


GOODRETURNS_URL = "https://www.goodreturns.in/gold-rates/"
# Excel's new-workbook shortcut creates a blank workbook directly after sign-in.
EXCEL_URL = "https://excel.new"
OUTPUT_DIR = Path(__file__).resolve().parent

pyautogui.FAILSAFE = True  # Move the mouse to the top-left corner to abort.
pyautogui.PAUSE = 0.7


def fetch_india_gold_rates():
    """Read the current 24K, 22K and 18K per-gram prices from page text."""
    response = requests.get(
        GOODRETURNS_URL,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        timeout=25,
    )
    response.raise_for_status()
    page_text = BeautifulSoup(response.text, "html.parser").get_text(" ", strip=True)

    # The page's India summary names all purities and states the per-gram prices.
    match = re.search(
        r"Today's gold price in India stands at\s*₹?\s*([\d,]+)\s*per gram for 24 karat gold"
        r".*?₹?\s*([\d,]+)\s*per gram for 22 karat gold"
        r".*?₹?\s*([\d,]+)\s*per gram for 18 karat gold",
        page_text,
        flags=re.IGNORECASE,
    )
    if not match:
        raise RuntimeError(
            "Couldn't identify all three rates on the Goodreturns page. "
            "The page layout may have changed; open the page and check it manually."
        )
    return {"24K": match.group(1), "22K": match.group(2), "18K": match.group(3)}


def open_url_in_chrome(url):
    """Open a URL in Chrome using keyboard automation (Chrome must be installed)."""
    pyautogui.hotkey("win", "r")
    time.sleep(1)
    pyautogui.write("chrome", interval=0.08)
    pyautogui.press("enter")
    time.sleep(3)
    pyautogui.hotkey("ctrl", "l")
    pyperclip.copy(url)
    pyautogui.hotkey("ctrl", "v")
    pyautogui.press("enter")


def main():
    captured_at = datetime.now().astimezone()
    file_date = captured_at.strftime("%Y-%m-%d")
    timestamp = captured_at.strftime("%Y-%m-%d %H:%M:%S %Z")

    workbook_name = f"gold_rate_{file_date}.xlsx"
    screenshot_path = OUTPUT_DIR / f"gold_rate_{file_date}_screenshot.png"

    print("Opening Goodreturns in Chrome so the source page is visible…")
    open_url_in_chrome(GOODRETURNS_URL)
    time.sleep(4)

    print("Reading the latest India rates from Goodreturns…")
    rates = fetch_india_gold_rates()
    rate_summary = " | ".join(f"{karat}: ₹{value}/g" for karat, value in rates.items())
    print("Captured:", rate_summary)

    comments = "Captured"

    print("Opening a new blank workbook in Excel for the web…")
    pyautogui.hotkey("ctrl", "l")
    pyperclip.copy(EXCEL_URL)
    pyautogui.hotkey("ctrl", "v")
    pyautogui.press("enter")

    print("\nIf Microsoft asks you to sign in, complete sign-in in Chrome now.")
    print("Waiting 30 seconds for the blank workbook to load before entering the data…")
    time.sleep(30)

    # Exactly three data rows: capture time, rates, and the user's comments.
    rows = [
        ["Current date and time", timestamp, ""],
        ["Goodreturns India gold rates (per gram)", rate_summary, ""],
        ["Comments", comments, ""],
    ]
    tsv = "\n".join("\t".join(cell for cell in row) for row in rows)
    pyperclip.copy(tsv)
    # Excel's Go To shortcut focuses the sheet and selects A1 without relying on
    # screen coordinates or assuming the currently selected cell stayed active.
    pyautogui.hotkey("ctrl", "g")
    time.sleep(0.5)
    pyautogui.write("A1")
    pyautogui.press("enter")
    time.sleep(0.5)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(3)

    # Rename by clicking the filename near the top-left of the Excel page.
    # Calculate the click relative to the active Chrome window, not the desktop.
    chrome_window = pygetwindow.getActiveWindow()
    if chrome_window is None or "chrome" not in chrome_window.title.lower():
        raise RuntimeError("Excel in Chrome is not the active window; bring it to the front and retry.")
    chrome_window.activate()
    chrome_window.maximize()
    time.sleep(1)
    # The workbook title sits left of the cloud-status icon; 6% avoids the icon.
    workbook_x = chrome_window.left + int(chrome_window.width * 0.06)
    workbook_y = chrome_window.top + int(chrome_window.height * 0.15)
    print(f"Clicking workbook name near ({workbook_x}, {workbook_y})...")
    pyautogui.press("esc")
    pyautogui.click(workbook_x, workbook_y)
    time.sleep(1)
    pyautogui.hotkey("ctrl", "a")
    pyperclip.copy(Path(workbook_name).stem)
    pyautogui.hotkey("ctrl", "v")
    pyautogui.press("enter")
    time.sleep(6)  # Let Excel autosave the new workbook name and pasted data.
    pyautogui.screenshot().save(screenshot_path)
    print(f"Screenshot: {screenshot_path}")


if __name__ == "__main__":
    try:
        main()
    except (requests.RequestException, RuntimeError) as exc:
        print(f"Could not finish: {exc}")
    except pyautogui.FailSafeException:
        print("Stopped by PyAutoGUI fail-safe.")
