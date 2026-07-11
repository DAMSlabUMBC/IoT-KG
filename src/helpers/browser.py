from playwright.sync_api import Browser, Page
from playwright_stealth import stealth_sync


def new_stealth_page(browser: Browser, locale: str = "en-US") -> Page:
    """Create a page with the shared anti-bot setup (locale + stealth patches)."""
    page = browser.new_page(locale=locale)
    stealth_sync(page)
    return page
