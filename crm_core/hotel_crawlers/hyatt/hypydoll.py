import asyncio
import logging
import random as rand
import time
from datetime import datetime
from urllib.parse import urlparse, quote
from .proxy_manager import ProxyManager
from .random_user_agent import get_random_sec_ch_headers, USER_AGENT
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

# ---------------- Log configuration ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("hyatt.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def human_delay(a, b):
    # Synchronous sleep for demo (can use asyncio.sleep in async flow)
    time.sleep(rand.uniform(a, b))


class ExtractHyatt:

    def __init__(self):
        self._proxy_fetcher = ProxyManager()

    def build_response(self, success: bool, data: any, status_code: int):
        return {
            "success": success,
            "data": data,
            "status_code": status_code
        }

    async def get_search_data(self, hotel_id, check_in_date, check_out_date, guest_count, max_retries=3):
        # logger.info("Getting proxy IP for current session")
        # _proxy_url = self._proxy_fetcher.fetch_proxy()
        # if not _proxy_url:
        #     message = "Proxy url not retrieved from the server"
        #     return self.build_response(success=False, data=message, status_code=101)
        #
        # parsed = urlparse(_proxy_url)
        # proxy = None
        # if parsed.username and parsed.password:
        #     proxy = {
        #         "server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}",
        #         "username": parsed.username,
        #         "password": parsed.password,
        #     }
        #
        # logger.info("Proxy url dict created for request")
        # logger.info("Setting up crawler to extract data")

        browser_family, headers = get_random_sec_ch_headers(USER_AGENT)
        _headers = headers

        check_in = datetime.strptime(check_in_date, "%Y-%m-%d")
        check_out = datetime.strptime(check_out_date, "%Y-%m-%d")
        length_of_stay = (check_out - check_in).days
        if not hotel_id or length_of_stay <= 0 or guest_count <= 0:
            raise ValueError("hotel_id/no_of_stays/guest must have valid values.")

        hotel_id_name = hotel_id
        parts = hotel_id_name.split("-", 1)
        hotel_id = parts[0].strip()
        logger.info(f"Hotel ID: {hotel_id}")
        hotel_name = parts[1].strip() if len(parts) > 1 else ""
        logger.info(f"Hotel Name: {hotel_name}")
        encoded_hotel_name = quote(hotel_name, safe="")

        # --- Pydoll setup ---
        options = ChromiumOptions()
        options.headless = False  # or False for debugging
        # if proxy:
        #     options.add_argument(f'--proxy-server={_proxy_url}')
            # Handle proxy authentication via page if needed

        # User-agent and headers
        # options.add_argument(f'--user-agent={_headers["user-agent"]}')
        # # options.add_argument('--no-first-run')
        # # options.add_argument('--no-default-browser-check')
        # # options.add_argument('--disable-blink-features=AutomationControlled')
        # # options.add_argument('--disable-http2')
        # # options.add_argument('--disable-web-security')
        # # options.add_argument('--disable-3d-apis')
        # # options.add_argument('--disable-webrtc-encryption')
        # # options.add_argument('--disable-features=WebRtcHideLocalIpsWithMdns')
        # # options.add_argument('--disable-features=VizDisplayCompositor')
        # # options.add_argument('--disable-dev-shm-usage')
        # # options.add_argument('--no-sandbox')
        # # options.add_argument('--disable-setuid-sandbox')
        # # options.add_argument('--disable-background-timer-throttling')
        # # options.add_argument('--disable-backgrounding-occluded-windows')
        # # options.add_argument('--disable-renderer-backgrounding')

        api_url_part = f"/shop/service/rooms/roomrates/{hotel_id}"
        api_data = {}

        try:
            async with Chrome(options=options) as browser:
                tab = await browser.start()
                # await tab.set_default_timeout(100_000)

                # Set extra headers (except user-agent, which is set above)
                # extra_headers = {k: v for k, v in _headers.items() if k.lower() != "user-agent"}
                # await tab.set_extra_http_headers(extra_headers)

                # # Response handler for API
                # async def handle_response(response):
                #     if api_url_part in response.url:
                #         try:
                #             api_data["value"] = await response.json()
                #         except Exception:
                #             api_data["value"] = await response.text()
                #
                # tab.on_response(handle_response)

                # Home page and interaction
                logger.info("Loading Hyatt homepage...")
                await tab.go_to("https://www.hyatt.com/")
                await asyncio.sleep(rand.uniform(6, 12))

                # find_hotels_button = await tab.find('text="Find Hotels"')
                # find_hotels_button = None
                # for attempt in range(10):  # retry ~10 times
                #     try:
                #         find_hotels_button = await tab.find('text="Find Hotels"')
                #         if find_hotels_button:
                #             break
                #     except KeyError:
                #         logger.warning(f"Attempt {attempt + 1}: Node not yet available, retrying...")
                #     await asyncio.sleep(1)
                #
                # if not find_hotels_button:
                #     logger.error("Could not find 'Find Hotels' button after retries!")
                # else:
                #     logger.info("'Find Hotels' button found successfully.")

                # await tab.wait_for_selector('.quickbookDestinationSearchField', timeout=30_000)
                # await asyncio.sleep(3)

                logger.info("Home page request completed successfully.")

                api_url = (
                    f"https://www.hyatt.com/shop/service/rooms/roomrates/{hotel_id}"
                    f"?spiritCode={hotel_id}&rooms=1&adults={guest_count}"
                    f"&location={encoded_hotel_name}"
                    f"&checkinDate={check_in_date}&checkoutDate={check_out_date}"
                    f"&kids=0&rate=Standard&suiteUpgrade=true"
                )

                await tab.go_to(api_url)

                # Mouse movement
                # logger.info("Simulate mouse movement...")
                # await asyncio.sleep(rand.uniform(2, 5))
                # await tab.mouse.move(rand.randint(0, 2), rand.randint(3, 8))
                # await tab.mouse.down()
                # await tab.mouse.move(0, rand.randint(100, 120))
                # await tab.mouse.move(rand.randint(100, 120), rand.randint(100, 120))
                # await tab.mouse.move(rand.randint(100, 120), 0)
                # await tab.mouse.move(0, 0)
                # await tab.mouse.up()
                # await tab.keyboard.press("PageDown")
                # await asyncio.sleep(rand.uniform(1, 3))
                # await tab.keyboard.press("PageUp")
                # await asyncio.sleep(rand.uniform(2, 4))


                # # Cookie banner
                # try:
                #     await tab.click('button#onetrust-accept-btn-handler', timeout=5000)
                #     logger.info("Cookie banner accepted.")
                # except Exception:
                #     logger.info("No cookie banner found or already accepted.")
                #
                # # Location search
                # await tab.wait_for_selector('input[data-id="location"]', timeout=10_000)
                # await tab.focus('input[data-id="location"]')
                # await tab.click('.quickbookDestinationSearchField')
                # await tab.type('input[data-id="location"]', hotel_name, delay=120)
                # await tab.keyboard.press('Tab')
                # await asyncio.sleep(rand.uniform(1, 3))
                #
                # await tab.fill('input[data-id="checkinDate"]', check_in_date)
                # await tab.keyboard.press('Tab')
                # await asyncio.sleep(rand.uniform(1, 3))
                # await tab.fill('input[data-id="checkoutDate"]', check_out_date)
                # await asyncio.sleep(rand.uniform(1, 3))
                # await tab.keyboard.press('Tab')
                # await asyncio.sleep(rand.uniform(1, 3))
                # await tab.keyboard.press('Tab')
                # await tab.keyboard.press('Tab')
                # await tab.keyboard.press('Enter')
                #
                # # Use Points checkbox
                # use_points_label = await tab.wait_for_selector('label.input-checkbox', timeout=30_000)
                # await use_points_label.click()
                # await asyncio.sleep(rand.uniform(2, 6))
                # await asyncio.sleep(rand.uniform(1, 3))
                #
                # # Wait for and click the search button
                # button = await tab.wait_for_selector('button[data-js="quickbookSearchFormButton"]:not([disabled])', timeout=30_000)
                # await button.scroll_into_view_if_needed()
                # await button.click(force=True)

                # # Wait for API response
                # for _ in range(120):
                #     if "value" in api_data:
                #         break
                #     await asyncio.sleep(1)
                #
                # decodedResponse = api_data.get("value", {})

                # decodedResponse = ""
                #
                # if not decodedResponse:
                #     logger.error("No API response received.")
                #     await tab.screenshot(path="headless_fail.png")
                #     message = {"details": "No API response received. Screenshot saved as headless_fail.png"}
                #     return self.build_response(success=False, data=message, status_code=104)
                #
                # if isinstance(decodedResponse, str) and '"invalidSpiritCode"' in decodedResponse:
                #     logger.error("Property Code is invalid.")
                #     message = {"details": "Property Code is invalid."}
                #     return self.build_response(success=True, data=message, status_code=12)
                #
                # data_json = decodedResponse
                # room_rates = data_json.get("roomRates", {})
                # lowest_avg_exists = any(
                #     "lowestAvgPointValue" in rate_info
                #     for rate_info in room_rates.values()
                # )
                #
                # if room_rates and lowest_avg_exists:
                #     logger.info("Response fetched successfully from Roomrate API")
                #     return self.build_response(success=True, data=data_json, status_code=200)
                # elif room_rates and not lowest_avg_exists:
                #     logger.error("Hotel is not available at selected date.")
                #     message = {"details": "Hotel is not available at selected date."}
                #     return self.build_response(success=True, data=message, status_code=204)
                # else:
                #     logger.error("Roomrate API failed or unknown error.")
                #     message = {"details": "Unknown Error or Roomrate API failed"}
                #     return self.build_response(success=False, data=message, status_code=500)

        except Exception as ex:
            logger.exception(f"Critical Error: {ex}")
            message = {"details": f"Critical Error: {ex}"}
            return self.build_response(success=False, data=message, status_code=100)


# ---------------- Runner ----------------
if __name__ == "__main__":
    import sys
    try:
        crawl = ExtractHyatt()
        data = asyncio.run(crawl.get_search_data(
            hotel_id="goazg-Hyatt Place Goa Candolim",
            check_in_date="2026-01-07",
            check_out_date="2026-01-08",
            guest_count=1,
        ))
        if data:
            print("API data fetched successfully", data)
        else:
            print("API data could not be fetched with current cookies")
    except Exception as e:
        logger.exception(f"Exception in main: {e}")