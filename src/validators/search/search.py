import re
import urllib.parse
from typing import List
from src.types.search_result import SearchResult
from playwright.sync_api import sync_playwright, Page, Browser
from playwright_stealth import Stealth

class SearchClient:

    # TODO: Move this into a google config
    RESULT_REGEX = re.compile(r"([0-9][0-9,\.]+)\s+results", flags=re.I)
    
    def __init__(self, headless: bool = False):
        self.headless = headless
    
    def search_queries(self, queries: List[str]) -> List[SearchResult]:
        """Execute multiple search queries and return result counts."""
        with Stealth().use_sync(sync_playwright()) as p:
            browser = p.chromium.launch(headless=self.headless)
            try:
                return self._search_with_browser(browser, queries)
            finally:
                self._safe_close_browser(browser)
    
    def _search_with_browser(self, browser: Browser, queries: List[str]) -> List[SearchResult]:
        """Execute searches using an open browser."""
        page = browser.new_page()
        results = []
        
        for query in queries:
            count = self._search_single_query(page, query)
            results.append(count)
            page.wait_for_timeout(250)
        
        return results
    
    def _search_single_query(self, page: Page, query: str) -> SearchResult:
        """Execute a single search query and extract result count."""
        
        params = {
            "q": query,
            "nfpr": "1",
            "tbs": "li:1"
        }

        results = 0
        pages = 0
        try:
            url = f"https://www.google.com/search?{urllib.parse.urlencode(params)}"
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_timeout(10000)

            text = page.locator('#result-stats').inner_text(
                timeout=2500
            )

            results = self._parse_result_count(text)
            pages = self._get_pagination_count(page)

            return SearchResult(results=results, pages=pages)

        except Exception as e:
            print(f"Search failed for query '{query}': {e}")
            return SearchResult(results=results, pages=pages)
    
    def _parse_result_count(self, text: str) -> int:
        """Parse result count from result-stats text."""
        if not text:
            return 0
        
        match = self.RESULT_REGEX.search(text)
        if not match:
            return 0
        
        num_txt = match.group(1).replace(",", "").replace(".", "")
        try:
            return int(float(num_txt))
        except ValueError:
            return 0
    
    def _get_pagination_count(self, page: Page) -> int:
        """Extract highest page number from pagination."""
        try:
            # TODO: Move this into a google config
            links = page.locator('[role="navigation"] a')
            texts = [t.strip() for t in links.all_text_contents()]
            nums = [int(t) for t in texts if t.isdigit()]
            return max(nums) if nums else 1
        except Exception:
            return 1
    
    @staticmethod
    def _safe_close_browser(browser: Browser) -> None:
        try:
            browser.close()
        except Exception:
            pass