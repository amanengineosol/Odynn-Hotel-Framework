import json
import logging
import random as rand
import time
from datetime import datetime
from urllib.parse import urlparse, quote
from .proxy_manager import ProxyManager
from .random_user_agent import get_random_sec_ch_headers, USER_AGENT
from pydoll.sync_api import Doll, TimeoutError as PydollTimeoutError  # Updated import

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

    def get_search_data(self, hotel_id, check_in_date, check_out_date, guest_count, max_retries=3):
        logger.info("Getting proxy IP for current session")
        _proxy_url = self._proxy_fetcher.fetch_proxy()
        if not _proxy_url:
            message = "Proxy url not retrieved from the server"
            return self.build_response(success=False, data=message, status_code=101)

        parsed = urlparse(_proxy_url)
        if parsed.username and parsed.password:
            proxy = {
                "server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}",
                "username": parsed.username,
                "password": parsed.password,
            }

        logger.info("Proxy url dict created for request")
        logger.info("Setting up crawler to extract data")

        browser_family, headers = get_random_sec_ch_headers(USER_AGENT)
        _headers = headers

        # Validate inputs
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

        try:
            with Doll(headless=True, proxy=proxy, geoip=True) as browser:  # Use pydoll's main entrypoint
                try:
                    logger.info("Sending Home page request....")
                    extra_headers = {
                        k: v for k, v in _headers.items() if k.lower() != "user-agent"
                    }

                    logger.info(f"Selected UA: {_headers['user-agent']}")
                    context = browser.new_context(
                        viewport={"width": 1920, "height": 1080},
                        user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"),
                        locale="en-US"
                    )
                    page = context.new_page()
                    page.set_default_timeout(100000)

                    for attempt in range(1, max_retries + 1):
                        try:
                            page.goto("https://www.hyatt.com/", wait_until="domcontentloaded")
                            human_delay(6, 12)
                            page.locator('input[data-id="location"]').wait_for(timeout=120000)
                            page.get_by_role("button", name="Find Hotels")
                            page.wait_for_selector('.quickbookDestinationSearchField', timeout=30000)
                            page.wait_for_timeout(3000)

                            logger.info("Home page request completed successfully.....")

                            logger.info("Sleeping for few seconds for mouse movement.....")
                            human_delay(2, 5)
                            page.mouse.move(rand.randint(0, 2), rand.randint(3, 8))
                            page.mouse.down()
                            page.mouse.move(0, rand.randint(100, 120))
                            page.mouse.move(rand.randint(100, 120), rand.randint(100, 120))
                            page.mouse.move(rand.randint(100, 120), 0)
                            page.mouse.move(0, 0)
                            page.mouse.up()

                            page.keyboard.press("PageDown")
                            human_delay(1, 3)
                            page.keyboard.press("PageUp")
                            human_delay(2, 4)

                            logger.info("Mouse movement completed.....")
                            break

                        except PydollTimeoutError as pwex:
                            logger.warning(f"Attempt {attempt} failed: {pwex}")
                            if attempt < max_retries:
                                time.sleep(2)
                            else:
                                return self.build_response(success=False, data={"details": f"Failed after retries: {pwex}"}, status_code=103)

                    api_url_part = f"/shop/service/rooms/roomrates/{hotel_id}"

                    # Handle cookie banner (OneTrust)
                    try:
                        page.click('button#onetrust-accept-btn-handler', timeout=5000)
                        logger.info("Cookie banner accepted.")
                    except Exception:
                        logger.info("No cookie banner found or already accepted.")

                    page.wait_for_selector('input[data-id="location"]', timeout=10000)
                    page.focus('input[data-id="location"]')
                    page.click('.quickbookDestinationSearchField')

                    page.type('input[data-id="location"]', hotel_name, delay=565)
                    human_delay(0.2, 1.5)
                    if not page.locator(".typeahead-content li.property").count():
                        print("⚠️ No dropdown options found. HTML snapshot:")
                        html_content = page.content()
                        with open("hyatt_page.html", "w", encoding="utf-8") as f:
                            f.write(html_content)
                    page.locator(".typeahead-content.is-open li.property").first.wait_for(timeout=30000)
                    page.locator(".typeahead-content.is-open li.property").first.click()

                    page.keyboard.press('Tab')
                    human_delay(1, 3)

                    page.fill('input[data-id="checkinDate"]', check_in_date)
                    page.keyboard.press('Tab')
                    human_delay(1, 3)

                    page.fill('input[data-id="checkoutDate"]', check_out_date)
                    human_delay(1, 3)
                    page.keyboard.press('Tab')
                    human_delay(1, 3)
                    page.keyboard.press('Tab')
                    human_delay(1, 3)
                    page.keyboard.press('Tab')
                    page.keyboard.press('Tab')
                    page.keyboard.press('Enter')

                    use_points_label = page.locator('label.input-checkbox', has_text='Use Points')
                    use_points_label.wait_for(state='visible', timeout=30000)
                    use_points_label.click()
                    human_delay(2, 6)
                    human_delay(1, 3)

                    page.wait_for_selector('button[data-js="quickbookSearchFormButton"]:not([disabled])', timeout=30000)

                    api_data = None

                    def handle_response(response):
                        nonlocal api_data
                        if api_url_part in response.url:
                            try:
                                api_data = response.json()
                            except:
                                api_data = response.text()

                    page.on("response", handle_response)

                    button = page.locator('button[data-js="quickbookSearchFormButton"]')
                    button.wait_for(state="visible", timeout=15000)
                    button.scroll_into_view_if_needed()
                    button.click(force=True)

                    for _ in range(120):
                        if api_data is not None:
                            break
                        time.sleep(1)

                    if api_data:
                        print("API data received:", api_data)
                    else:
                        page.screenshot(path="headless_fail.png")
                        print("No API response received. Screenshot saved as headless_fail.png")

                    decodedResponse = api_data

                    if '"invalidSpiritCode"' in decodedResponse:
                        logger.error("Property Code is invalid.")
                        message = {
                            "details": "Property Code is invalid."
                        }
                        return self.build_response(success=True, data=message, status_code=12)

                    data_json = decodedResponse
                    room_rates = decodedResponse.get("roomRates", {})
                    lowest_avg_exists = any(
                        "lowestAvgPointValue" in rate_info
                        for rate_info in room_rates.values()
                    )

                except Exception as ex:
                    logger.exception(f"Exception occurred during scraping: {ex}")
                    message = {
                        "details": f"Exception occurred during scraping: {ex}"
                    }
                    return self.build_response(success=False, data=message, status_code=103)

                finally:
                    logger.info("Closing browser...")
                    browser.close()

        except Exception as ex:
            logger.exception(f"Critical Error: {ex}")
            message = {
                "details": f"Critical Error: {ex}"
            }
            return self.build_response(success=False, data=message, status_code=100)


if __name__ == "__main__":
    crawl = ExtractHyatt()
    data = crawl.get_search_data(
        hotel_id="goazg-Hyatt Place Goa Candolim",
        check_in_date="2026-01-07",
        check_out_date="2026-01-08",
        guest_count=1,
    )
    if data:
        print("API data fetched successfully", data)
    else:
        print("API data could not be fetched with current cookies")