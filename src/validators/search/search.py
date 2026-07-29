import re
import time
import urllib.parse
from typing import List
from src.types.search_result import SearchResult
from src.helpers.browser import new_stealth_page
from playwright.sync_api import sync_playwright, Page

class SearchClient:

    # TODO: Move this into a google config
    RESULT_REGEX = re.compile(r"([0-9][0-9,\.]+)\s+results", flags=re.I)
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self._playwright = None
        self._browser = None
        self._page = None
        self._page_crashed = False

    def search_queries(self, queries: List[str]) -> List[SearchResult]:
        """Execute multiple search queries and return result counts."""
        results = []

        for i, query in enumerate(queries):
            if i:
                # Throttle between queries only; time.sleep does not depend on
                # the page being alive, so a dead page cannot abort the batch.
                time.sleep(2.5)
            page = self._get_page()
            results.append(self._search_single_query(page, query))

        return results

    def _get_page(self) -> Page:
        """Return the shared page, launching the browser on first use."""
        if self._browser is None or not self._browser.is_connected():
            self.close()
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(headless=self.headless)

        if self._page is None or self._page.is_closed() or self._page_crashed:
            if self._page is not None and not self._page.is_closed():
                try:
                    self._page.close()
                except Exception:
                    pass
            page = new_stealth_page(self._browser)
            # A crashed renderer leaves the page open but permanently broken
            # (is_closed() stays False), so track crashes explicitly and
            # rebuild the page on the next query.
            page.on("crash", lambda _: setattr(self, "_page_crashed", True))
            self._page_crashed = False
            self._page = page

        return self._page

    def close(self) -> None:
        """Close the shared browser session."""
        try:
            if self._browser is not None:
                self._browser.close()
        except Exception:
            pass
        try:
            # Stop the driver even if the browser refused to close, otherwise
            # the playwright node process is orphaned.
            if self._playwright is not None:
                self._playwright.stop()
        except Exception:
            pass
        self._playwright = None
        self._browser = None
        self._page = None
        self._page_crashed = False
    
    def _search_single_query(self, page: Page, query: str) -> SearchResult:
        """Execute a single search query and extract result count."""
        
        params = {
        "q": query,
        "hl": "en",
        "gl": "us",
        "tbs": "li:1,lr:lang_1en"
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
