"""
Scrape each URL in urls using selectors from the chosen config and
write extracted fields to JSON files on disk for downstream LLM use.

Example Command:
  uv run -m src.scraper.scrape_ecommerce_to_disk --amazon

Configs are located in src.configs

PLEASE READ: 
ITEM variable is to specify the folder you would like to read and write from (line 25, 43, 93)
You still need to update the exact file you'd like to read
"""

import os
import json
import datetime
import argparse

from playwright.sync_api import sync_playwright

from src.configs import AMAZON_SELECTOR, BEST_BUY_SELECTOR, COSTCO_SELECTOR, TARGET_SELECTOR, WALMART_SELECTOR
from src.helpers.browser import new_stealth_page

ITEM = "robot_vacuums"

CONFIGS = {
    "amazon": AMAZON_SELECTOR,
    "best_buy": BEST_BUY_SELECTOR,
    "costco": COSTCO_SELECTOR,
    "target": TARGET_SELECTOR,
    "walmart": WALMART_SELECTOR,
}

def scrape_to_disk(urls: list[str], config: str):
    output_dir = f"data/html_dumps/{config}/{ITEM}"
    os.makedirs(output_dir, exist_ok=True)

    with sync_playwright() as p:
            browser = None
            try:
                browser =  p.firefox.launch(headless=False)
                page = new_stealth_page(browser)

                with open(f"{output_dir}/{datetime.datetime.now().strftime('%Y-%m-%d')}.jsonl", "a", encoding="utf-8") as f:
                    for url in urls:
                        try:
                            page.goto(url, wait_until='domcontentloaded')
                            page.wait_for_timeout(5000)

                            result = {"url": url}
                            for key, selector in CONFIGS[config].items():
                                locator = page.locator(selector)
                                count = locator.count()

                                if count == 0:
                                    continue
                                text = locator.first.inner_text().strip()

                                if text:
                                    result[key] = text

                            if len(result) > 1:
                                f.write(json.dumps(result) + "\n")
                        except Exception as e:
                            print(f"[ERROR] Failed to scrape {url}: {e}")
                            continue

            except Exception as e:
                raise Exception("Error scraping to disk: ", e)
            finally:
                if browser is not None:
                    browser.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scrape e-commerce websites')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--amazon', action='store_true', help='Use Amazon config')
    group.add_argument('--best_buy', action='store_true', help='Use Best Buy config')
    group.add_argument('--costco', action='store_true', help='Use Costco config')
    group.add_argument('--target', action='store_true', help='Use Target config')
    group.add_argument('--walmart', action='store_true', help='Use Walmart config')

    args = parser.parse_args()
    
    if args.amazon:
        config = "amazon"
    elif args.best_buy:
        config = "best_buy"
    elif args.costco:
        config = "costco"
    elif args.target:
        config = "target"
    elif args.walmart:
        config = "walmart"

    urls = []

    file_path = f"data/urls/{config}/{ITEM}/2025-11-19.txt"

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            url = line.strip()
            if url:
                urls.append(url)

    scrape_to_disk(urls, config)