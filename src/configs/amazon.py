AMAZON_SELECTOR = {
  "title": "#productTitle",
  "features": "#feature-bullets"
}


"""
search box: role, <input type="search"> element implicitly has role="searchbox"
search box name: aria-label or place holder
product urls: amazon has their href for products marked as detail page, we are avoiding the sponsors and ads
"""

AMAZON_PRODUCT_URL_SELECTOR = {
    "home_url": "https://www.amazon.com/",
    "search_box": {
      "role": "searchbox",
      "name": "Search Amazon",
    },
    "product_urls":  'a[href*="/dp/"]:not([href*="/sspa/"]):not([href*="/slredirect/"])',
    "next_button": 'a[aria-label*="next page"]'
}