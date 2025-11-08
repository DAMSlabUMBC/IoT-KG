# Selector for product info (name, price, description, url)
WALMART_PRODUCT_SELECTOR = {
  "title": "#main-title"
}

WALMART_PRODUCT_URL_SELECTOR = {
    "home_url": "https://www.walmart.com/",
    "search_box": {
      "role": "searchbox",
      "name": "Search",
    },
    "product_urls": 'a[href*="/ip/"]',
    "next_button": ""
}