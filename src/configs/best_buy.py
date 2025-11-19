BEST_BUY_SELECTOR = {
    "title": "h1.h4",
    "price": "div[data-testid='price-block-customer-price'] span",
    "description": "div[data-testid='brix-sheet-content']",
    "features": "div[data-testid='brix-sheet-content']",  
    "images": "div.pr-300.flex.flex-col.items-start"
}

BEST_BUY_PRODUCT_URL_SELECTOR = {
    "home_url": "https://www.bestbuy.com/",
    "search_box": {
      "role": "textbox",
      "name": "Search",
    },
    "product_urls": 'a.product-list-item-link',
    "next_button": 'a[aria-label="Next page"]'
}