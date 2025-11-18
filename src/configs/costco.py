COSTCO_SELECTOR = {
    "title": "div[data-testid='Text_brand-name']",
    "integerPartOfPrice": "span[data-testid='Text_single-price-whole-value']",
    "decimalPartOfPrice": "span[data-testid='Text_single-price-decimal-value']",
    "description": "div[id='product-details-summary']",
    "features": "div[data-testid='VerticalTableContainer_ProductSpecifications']",
    "images": "div[data-testid='product-hero']"
}

COSTCO_PRODUCT_URL_SELECTOR = {
    "home_url": "http://costco.com/",
    "search_box": {
      "role": "combobox",
      "name": "Search Costco",
    },
    "product_urls":  'a[href*=".product."]',
    "next_button": 'a[aria-label="Go to next page"]'
}