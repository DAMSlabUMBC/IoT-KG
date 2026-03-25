"""
Deterministic template-based triple extractor for Amazon product pages.

Extracts structured knowledge triples from Amazon's consistent HTML sections
(spec tables, detail bullets, breadcrumbs, etc.) to serve as ground truth
for evaluating LLM-based extraction.
"""

import re

from playwright.sync_api import Page, sync_playwright
from playwright_stealth import stealth_sync

from src.types.triple import Triple, TripleNode

# Maps normalized Amazon table keys to ontology predicates
PREDICATE_MAP: dict[str, str] = {
    "brand": "manufacturedBy",
    "manufacturer": "manufacturedBy",
    "manufacturer / importer": "manufacturedBy",
    "distributor": "manufacturedBy",
    "compatible devices": "compatibleWith",
    "compatible with": "compatibleWith",
    "operating system": "compatibleWith",
    "hardware platform": "compatibleWith",
    "wireless technology": "hasConnectivity",
    "connectivity technology": "hasConnectivity",
    "connectivity type": "hasConnectivity",
    "network technology": "hasConnectivity",
    "interface": "hasInterface",
    "special features": "performs",
    "item weight": "hasWeight",
    "item dimensions": "hasDimensions",
    "product dimensions": "hasDimensions",
    "package dimensions": "hasDimensions",
    "batteries": "hasBattery",
    "number of batteries": "hasBattery",
    "color": "hasColor",
    "model name": "hasModelNumber",
    "model number": "hasModelNumber",
    "item model number": "hasModelNumber",
    "part number": "hasModelNumber",
    "asin": "hasASIN",
    "country of origin": "madeIn",
    "date first available": "firstAvailable",
    "best sellers rank": "hasBestSellerRank",
    "customer reviews": "hasRating",
    "material": "hasMaterial",
    "voltage": "hasVoltage",
    "wattage": "hasWattage",
    "series": "hasSeries",
    "style": "hasStyle",
    "size": "hasSize",
    "item package quantity": "hasQuantity",
    "number of items": "hasQuantity",
    "data transfer rate": "hasDataTransferRate",
    "resolution": "hasResolution",
    "display type": "hasDisplayType",
    "ram": "hasRAM",
    "memory storage capacity": "hasStorage",
    "storage": "hasStorage",
    "processor": "hasProcessor",
    "cpu model": "hasProcessor",
    "battery life": "hasBatteryLife",
    "battery capacity": "hasBatteryCapacity",
    "power source": "hasPowerSource",
    "mounting type": "hasMountingType",
    "form factor": "hasFormFactor",
    "replication": "hasConnectivity",
    # prodDetTable keys (Google Nest / smart home products)
    "controller type": "compatibleWith",
    "additional features": "performs",
    "specific uses for product": "performs",
    "temperature control type": "hasProperty",
    "connectivity protocol": "hasConnectivity",
    "control method": "performs",
    "control type": "hasProperty",
    "backlight": "hasProperty",
    "compatible assistants": "compatibleWith",
    "hub required": "hasProperty",
    "installation type": "hasProperty",
    "item package dimensions": "hasDimensions",
}

# Node types for object nodes based on predicate
OBJECT_TYPES: dict[str, str] = {
    "manufacturedBy": "manufacturer",
    "compatibleWith": "product",
    "hasSensor": "sensor",
    "performs": "process",
    "hasASIN": "identifier",
    "hasCategory": "category",
    "hasConnectivity": "property",
    "hasInterface": "property",
    "hasModelNumber": "identifier",
    "madeIn": "property",
    "hasBestSellerRank": "property",
    "hasRating": "property",
    "hasWeight": "property",
    "hasDimensions": "property",
    "hasColor": "property",
    "hasMaterial": "property",
    "hasVoltage": "property",
    "hasWattage": "property",
    "hasSeries": "property",
    "hasBattery": "property",
    "firstAvailable": "property",
    "hasFeature": "property",
    "hasProperty": "property",
    "hasPrice": "property",
    "hasStyle": "property",
    "hasSize": "property",
    "hasQuantity": "property",
    "hasDataTransferRate": "property",
    "hasResolution": "property",
    "hasDisplayType": "property",
    "hasRAM": "property",
    "hasStorage": "property",
    "hasProcessor": "property",
    "hasBatteryLife": "property",
    "hasBatteryCapacity": "property",
    "hasPowerSource": "property",
    "hasMountingType": "property",
    "hasFormFactor": "property",
}

# Predicates where comma/semicolon-separated values become multiple triples
MULTI_VALUE_PREDICATES = {"compatibleWith", "performs"}

# Regex patterns for extracting structured triples from feature bullet text
# Each tuple: (pattern, predicate)
BULLET_PATTERNS: list[tuple[str, str]] = [
    (r"[Cc]ompatible with ([^.]+)", "compatibleWith"),
    (r"[Ww]orks with ([^.]+)", "compatibleWith"),
    (r"[Ss]upports? ([^.]+?)(?: on| for| with)?\s*$", "compatibleWith"),
    (r"(?:includes?|features?|has)(?: a| an)? (.+?) sensor", "hasSensor"),
    (r"(.+?) sensor (?:built[- ]in|included|for)", "hasSensor"),
    (r"[Mm]anufactured by ([^.]+)", "manufacturedBy"),
]

# Amazon special unicode characters to strip from table keys/values
_UNICODE_JUNK = re.compile(r"[\u200f\u200e\u202f\u200b\u200c\u200d\ufeff]")


def _clean(s: str) -> str:
    """Remove Amazon's invisible unicode chars and strip whitespace."""
    return _UNICODE_JUNK.sub("", s).strip()


class AmazonTemplateExtractor:
    """
    Deterministically extracts knowledge triples from Amazon product pages
    using CSS selectors against Amazon's consistent page template.

    After calling extract(), self.scraped_data contains the raw text of each
    page section, which can be passed directly to LLMTripleExtractor to avoid
    re-loading the page.
    """

    def __init__(self) -> None:
        self.scraped_data: dict[str, str] = {}

    def extract(self, url: str, debug: bool = False) -> list[Triple]:
        """
        Load an Amazon product page and extract all possible triples.
        Also populates self.scraped_data for downstream LLM use.

        Args:
            debug: If True, print page diagnostics and save a screenshot to
                   data/evaluation/debug_screenshot.png when extraction fails.
        """
        with sync_playwright() as p:
            # Use Firefox with headless=False — matches existing scraper pattern,
            # avoids Amazon bot detection that blocks headless Chromium.
            browser = p.firefox.launch(headless=False)
            page = browser.new_page()
            stealth_sync(page)
            if not url.startswith("http"):
                url = "https://" + url
            try:
                page.goto(url, wait_until="domcontentloaded")

                # Wait for product title specifically instead of a blind timeout.
                # Falls back to a plain timeout if the selector never appears
                # (e.g. CAPTCHA page), then reports diagnostics.
                try:
                    page.wait_for_selector("#productTitle", timeout=15000)
                except Exception:
                    print("\n  [WARN] #productTitle not found after 15s — page may be a CAPTCHA or bot-check.")
                    print(f"  [DIAG] Browser URL : {page.url}")
                    print(f"  [DIAG] Page title  : {page.title()}")
                    if debug:
                        from pathlib import Path
                        ss_path = Path("data/evaluation/debug_screenshot.png")
                        ss_path.parent.mkdir(parents=True, exist_ok=True)
                        page.screenshot(path=str(ss_path), full_page=False)
                        print(f"  [DIAG] Screenshot  : {ss_path}")
                    # Give a few more seconds in case the page is still loading
                    page.wait_for_timeout(5000)

                if debug:
                    self._debug_dump(page)

                triples = self._extract_from_page(page)
                self.scraped_data = self._collect_text_content(page)
                return triples
            finally:
                browser.close()

    # ------------------------------------------------------------------
    # Internal extraction methods
    # ------------------------------------------------------------------

    def _debug_dump(self, page: Page) -> None:
        """Print a quick probe of every key selector to locate failures."""
        print("\n  --- DEBUG DUMP ---")
        print(f"  Current URL : {page.url}")
        print(f"  Page title  : {page.title()!r}")

        probes: dict[str, str] = {
            "#productTitle":                    "product title",
            "#bylineInfo":                      "byline/brand",
            "#feature-bullets":                 "feature bullets",
            "#productOverview_feature_div":     "product overview table",
            "#productDetails_techSpec_section_1": "tech spec table",
            "#productDetails_db_sections":      "additional info table",
            "table.prodDetTable":               "product info table (prodDetTable)",
            "#detailBullets_feature_div":       "detail bullets",
            "#wayfinding-breadcrumbs_feature_div": "breadcrumbs",
            ".a-price .a-offscreen":            "price",
        }
        for selector, label in probes.items():
            try:
                count = page.locator(selector).count()
                if count > 0:
                    snippet = page.locator(selector).first.inner_text()[:80].replace("\n", " ")
                    print(f"  [{count:2d} hit ] {label:35s} → {snippet!r}")
                else:
                    print(f"  [  MISS ] {label}")
            except Exception as e:
                print(f"  [ ERROR ] {label}: {e}")
        print("  --- END DEBUG ---\n")

    def _extract_from_page(self, page: Page) -> list[Triple]:
        product_name = self._get_title(page)
        if not product_name:
            return []

        triples: list[Triple] = []
        triples.extend(self._extract_byline(page, product_name))
        triples.extend(self._extract_overview_table(page, product_name))
        triples.extend(self._extract_table(page, "#productDetails_techSpec_section_1 tr", product_name))
        triples.extend(self._extract_table(page, "#productDetails_db_sections tr", product_name))
        # prodDetTable is used on many product categories (e.g. smart home, thermostats)
        # as an alternative to the techSpec/db_sections IDs above
        triples.extend(self._extract_table(page, "table.prodDetTable tr", product_name))
        triples.extend(self._extract_detail_bullets(page, product_name))
        triples.extend(self._extract_feature_bullets(page, product_name))
        triples.extend(self._extract_breadcrumbs(page, product_name))
        triples.extend(self._extract_rating(page, product_name))
        triples.extend(self._extract_price(page, product_name))

        return self._deduplicate(triples)

    def _get_title(self, page: Page) -> str | None:
        try:
            # Use .first — Amazon renders #productTitle on multiple elements
            # (visible + hidden for responsive layout), and Playwright's
            # inner_text() throws a strict-mode violation when count > 1.
            return _clean(page.locator("#productTitle").first.inner_text())
        except Exception:
            return None

    def _make_triple(self, product_name: str, predicate: str, obj_value: str) -> Triple:
        return Triple(
            subject=TripleNode(node_type="device", value=product_name),
            predicate=predicate,
            object=TripleNode(
                node_type=OBJECT_TYPES.get(predicate, "property"),
                value=obj_value.strip(),
            ),
        )

    def _key_to_predicate(self, key: str) -> str:
        normalized = _clean(key).lower().rstrip(":").strip()
        return PREDICATE_MAP.get(normalized, "hasProperty")

    def _rows_to_triples(self, rows: list[tuple[str, str]], product_name: str) -> list[Triple]:
        triples = []
        for raw_key, raw_value in rows:
            key = _clean(raw_key)
            value = _clean(raw_value)
            if not key or not value:
                continue
            predicate = self._key_to_predicate(key)
            if predicate in MULTI_VALUE_PREDICATES:
                for v in re.split(r"[,;/]", value):
                    v = v.strip()
                    if v:
                        triples.append(self._make_triple(product_name, predicate, v))
            else:
                triples.append(self._make_triple(product_name, predicate, value))
        return triples

    def _extract_byline(self, page: Page, product_name: str) -> list[Triple]:
        try:
            text = _clean(page.locator("#bylineInfo").inner_text())
        except Exception:
            return []

        for pattern in [
            r"Brand[:\s]+([^\n\t]+)",
            r"Visit the (.+?) Store",
            r"^[Bb]y (.+?)$",
        ]:
            m = re.search(pattern, text, re.MULTILINE)
            if m:
                brand = m.group(1).strip()
                return [self._make_triple(product_name, "manufacturedBy", brand)]
        return []

    def _extract_overview_table(self, page: Page, product_name: str) -> list[Triple]:
        # Pair up all <td> elements in the overview div — more robust than
        # table > tr > td navigation, which breaks when Amazon uses nested divs
        # or adds a <tbody> layer between table and tr.
        rows: list[tuple[str, str]] = []
        try:
            tds = page.locator("#productOverview_feature_div td").all()
            for i in range(0, len(tds) - 1, 2):
                try:
                    key = _clean(tds[i].inner_text())
                    value = _clean(tds[i + 1].inner_text())
                    if key and value:
                        rows.append((key, value))
                except Exception:
                    pass
        except Exception:
            pass
        return self._rows_to_triples(rows, product_name)

    def _extract_table(self, page: Page, selector: str, product_name: str) -> list[Triple]:
        rows: list[tuple[str, str]] = []
        try:
            for row in page.locator(selector).all():
                try:
                    key = _clean(row.locator("th").first.inner_text())
                    value = _clean(row.locator("td").first.inner_text())
                    if key and value:
                        rows.append((key, value))
                except Exception:
                    pass
        except Exception:
            pass
        return self._rows_to_triples(rows, product_name)

    def _extract_detail_bullets(self, page: Page, product_name: str) -> list[Triple]:
        """Extract from the newer-style #detailBullets_feature_div list items."""
        triples = []
        try:
            for item in page.locator("#detailBullets_feature_div ul li").all():
                try:
                    spans = item.locator("span").all()
                    if len(spans) >= 2:
                        key = _clean(spans[0].inner_text()).rstrip(":")
                        value = _clean(spans[1].inner_text())
                        if key and value:
                            predicate = self._key_to_predicate(key)
                            if predicate in MULTI_VALUE_PREDICATES:
                                for v in re.split(r"[,;]", value):
                                    v = v.strip()
                                    if v:
                                        triples.append(self._make_triple(product_name, predicate, v))
                            else:
                                triples.append(self._make_triple(product_name, predicate, value))
                except Exception:
                    pass
        except Exception:
            pass
        return triples

    def _extract_feature_bullets(self, page: Page, product_name: str) -> list[Triple]:
        """
        Parse feature bullet points. Known patterns produce typed triples;
        unmatched bullets become hasFeature triples.
        """
        triples = []
        try:
            for bullet in page.locator("#feature-bullets .a-list-item").all():
                try:
                    text = _clean(bullet.inner_text())
                    if not text or "make sure this fits" in text.lower():
                        continue

                    matched = False
                    for pattern, predicate in BULLET_PATTERNS:
                        m = re.search(pattern, text)
                        if m:
                            value = m.group(1).strip().rstrip(".")
                            if predicate in MULTI_VALUE_PREDICATES:
                                for v in re.split(r"[,;]", value):
                                    v = v.strip()
                                    if v:
                                        triples.append(self._make_triple(product_name, predicate, v))
                            else:
                                triples.append(self._make_triple(product_name, predicate, value))
                            matched = True
                            break

                    if not matched:
                        triples.append(self._make_triple(product_name, "hasFeature", text))
                except Exception:
                    pass
        except Exception:
            pass
        return triples

    def _extract_breadcrumbs(self, page: Page, product_name: str) -> list[Triple]:
        triples = []
        try:
            for crumb in page.locator("#wayfinding-breadcrumbs_feature_div a").all():
                try:
                    text = _clean(crumb.inner_text())
                    if text:
                        triples.append(self._make_triple(product_name, "hasCategory", text))
                except Exception:
                    pass
        except Exception:
            pass
        return triples

    def _extract_rating(self, page: Page, product_name: str) -> list[Triple]:
        for selector in [
            "#acrPopover span.a-icon-alt",
            ".a-icon-star-medium .a-icon-alt",
            "#averageCustomerReviews .a-icon-alt",
        ]:
            try:
                text = _clean(page.locator(selector).first.inner_text())
                if text:
                    return [self._make_triple(product_name, "hasRating", text)]
            except Exception:
                pass
        return []

    def _extract_price(self, page: Page, product_name: str) -> list[Triple]:
        try:
            text = _clean(page.locator(".a-price .a-offscreen").first.inner_text())
            if text:
                return [self._make_triple(product_name, "hasPrice", text)]
        except Exception:
            pass
        return []

    def _collect_text_content(self, page: Page) -> dict[str, str]:
        """
        Collect human-readable text from key page sections.
        Used as input for the LLM extractor so the page doesn't need reloading.
        """
        sections = {
            "title": "#productTitle",
            "byline": "#bylineInfo",
            "features": "#feature-bullets",
            "overview": "#productOverview_feature_div",
            "tech_specs": "#productDetails_techSpec_section_1",
            "product_details": "#productDetails_db_sections",
            "product_info_table": "table.prodDetTable",
            "detail_bullets": "#detailBullets_feature_div",
            "breadcrumbs": "#wayfinding-breadcrumbs_feature_div",
        }
        data: dict[str, str] = {}
        for key, selector in sections.items():
            try:
                # .first avoids strict-mode violations on selectors with
                # multiple matches (e.g. #productTitle has 2 hits on Amazon).
                text = _clean(page.locator(selector).first.inner_text())
                if text:
                    data[key] = text
            except Exception:
                pass
        return data

    @staticmethod
    def _deduplicate(triples: list[Triple]) -> list[Triple]:
        seen: set[tuple[str, str, str]] = set()
        unique = []
        for t in triples:
            key = (t.subject.value, t.predicate, t.object.value)
            if key not in seen:
                seen.add(key)
                unique.append(t)
        return unique
