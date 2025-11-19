import asyncio

from src.configs.amazon import AMAZON_SELECTOR
from src.configs.walmart import WALMART_SELECTOR

from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

URL = 'https://www.amazon.com/Amazon-vibrant-helpful-routines-Charcoal/dp/B09B8V1LZ3/ref=sr_1_1?crid=1FILQKC6UQ9B5&dib=eyJ2IjoiMSJ9.z0kBrN5J4yDwE3Z69yvpFvmwHHypkHHD1EEB0Tq7d-twKIMmrd6CdpzAKHt3QwCIqpCGWOtUGso25ArgjUeQiby0wRAtPziXyEv_Tf6qw3ScIhyK8WiI5tvRhkwcaZAYJpqeIDTu_m3cf2k1gyY2IF6h7Q-TpQpXqLkVlwxHcP1Ckn7GRQitYbsIXzmMdVt_vBDTTWAeeARk7Yo7VrzCI4_YLLlMbjp_5sTMWrY7dRA.M_EhWcOAkjfHtGyy6bJoS1n8Dh5KYN-aTbt1Uez3DW0&dib_tag=se&keywords=echo%2Bdot&qid=1759097324&sprefix=echo%2Bdo%2Cspecialty-aps%2C87&sr=8-1-catcorr&srs=17938598011&ufe=app_do%3Aamzn1.fos.74097168-0c10-4b8a-b96b-8388a1a12daf&th=1'
# URL = 'https://www.walmart.com/ip/HomePod-mini-Midnight/8103503224?classType=VARIANT&athbdg=L1600&from=/search'

def main(url: str) -> list | None:
        with sync_playwright() as p:
            try:

                result = []

                browser = p.firefox.launch(headless=False)
                page =  browser.new_page()
                stealth_sync(page)
                page.goto(url, wait_until='domcontentloaded')

                page.wait_for_timeout(5000)

                for key, value in AMAZON_SELECTOR.items():
                     result.append(page.locator(value).inner_text())

                return result
            except:
                return None
            finally:
                browser.close()


if __name__ == '__main__':
    print(main(URL))