WALMART_SELECTOR = {
  "title": "#main-title",
  "price": "span[itemprop='price']",
  "description": "div[data-testid='product-description-content']",
  "features": "span[id='product-smart-summary-lineClmap']",
  "images": "div[data-testid='vertical-carousel-container']",
}

WALMART_PRODUCT_URL_SELECTOR = {
    "home_url": "https://www.walmart.com/",
    "search_box": {
      "role": "searchbox",
      "name": "Search",
    },
    "product_urls": 'a[href*="/ip/"]',
    "next_button": 'a[aria-label="Next Page"]'
}