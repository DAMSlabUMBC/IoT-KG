TARGET_SELECTOR = {
    "title": "div[data-module-type='ProductDetailTitle']",
    "price": "span[data-test='product-price']",
    "description": "div[data-test='item-details-description']",
    "features": "div[data-test='item-details-specifications']",
    "images": "section[aria-label='Image gallery']",
}

TARGET_PRODUCT_URL_SELECTOR = {
    "home_url": "https://www.target.com/",
    "search_box": {
      "role": "searchbox",
      "name": "What can we help you find? suggestions appear below",
    },
    "product_urls":  'a[href*="/p/"]',
    "next_button": 'button[aria-label="next page"]'
}
