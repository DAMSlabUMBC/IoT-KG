import os
import datetime
from urllib.parse import urljoin

from src.configs import *
from playwright.sync_api import sync_playwright
from src.helpers.browser import new_stealth_page
from src.helpers.snake_case import to_snake_case

CONFIGS = {
    "amazon": AMAZON_PRODUCT_URL_SELECTOR, 
    # "best_buy": BEST_BUY_PRODUCT_URL_SELECTOR,
    # "costco": COSTCO_PRODUCT_URL_SELECTOR,
    # "home_depot": HOME_DEPOT_PRODUCT_URL_SELECTOR,
    # "sams_club": SAMS_CLUB_PRODUCT_URL_SELECTOR,
    # "target": TARGET_PRODUCT_URL_SELECTOR,
    # "walmart": WALMART_PRODUCT_URL_SELECTOR,
}


def slow_scroll(page, step=200, delay=500):
    scrolled = 0
    total_height = page.evaluate("document.body.scrollHeight")

    while scrolled < total_height:
        page.evaluate(f"window.scrollBy(0, {step});")
        page.wait_for_timeout(delay)
        scrolled += step


def click_next(page, selector):
    try:
        next_button = page.locator(selector["next_button"])

        if next_button.count() == 0:
            return False

        if not next_button.first.is_visible():
            return False

        next_button.click()

        page.wait_for_timeout(7000)
        return True

    except Exception as e:
        print("Error clicking next page: ", e)
        return False

def get_product_urls(page, selector):
    result = []

    product_urls = page.locator(selector["product_urls"])
    count = product_urls.count()

    for i in range(count):
        url = product_urls.nth(i).get_attribute("href")
        if selector["home_url"] not in url:
            url = urljoin(selector["home_url"], url)
        
        result.append(url)
        
    page.wait_for_timeout(7000)
    return result

def scrape_product_urls(config_key):
    selector = CONFIGS[config_key]
    with sync_playwright() as p:
        browser = None
        try:
            browser = p.firefox.launch(headless=False)

            page = new_stealth_page(browser)

            page.goto(selector["home_url"], wait_until="domcontentloaded")
            page.wait_for_timeout(7000)

            search_box = page.get_by_role(selector["search_box"]["role"], name=selector["search_box"]["name"], )
            
            for query in search_queries:
                seen_urls = set()
                all_urls = []
                search_box.fill(query)
                search_box.press("Enter")

                page.wait_for_timeout(7000)

                has_next_page = True

                while has_next_page:     
                    slow_scroll(page)
                    urls = get_product_urls(page, selector)
                    for url in urls:
                        if url not in seen_urls:
                            all_urls.append(url)
                            seen_urls.add(url)
                    has_next_page = click_next(page,selector)

                dir = to_snake_case(query)
                output_dir = f"data/urls/{config_key}/{dir}"
                os.makedirs(output_dir, exist_ok=True)
                with open(f"{output_dir}/{datetime.datetime.now().strftime('%Y-%m-%d')}.txt", "w", encoding="utf-8") as f:
                    for url in all_urls:
                        f.write(url + "\n")

        except Exception as e:
            raise Exception("Error scraping product urls: ", e)
        finally:
            if browser is not None:
                browser.close()

if __name__ == "__main__":
    for key in CONFIGS:
        scrape_product_urls(key)