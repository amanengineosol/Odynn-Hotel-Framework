import json
import logging
import random as rand
import time
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from urllib.parse import urlparse, quote
from .proxy_manager import ProxyManager
from .random_user_agent import get_random_sec_ch_headers, USER_AGENT

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
        # while browser_family != "chromium":
        #     browser_family, headers = get_random_sec_ch_headers(USER_AGENT)
        _headers = headers
        _headers["cache-control"] = "no-cache"

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
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    proxy=proxy,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--start-maximized",
                        "--disable-dev-shm-usage",
                        "--no-sandbox",
                        "--disable-gpu",
                        "--disable-infobars",
                        "--ignore-certificate-errors",
                        "--enable-features=NetworkService,NetworkServiceInProcess"
                    ],
                )
                try:
                    logger.info("Sending Home page request....")
                    extra_headers = {
                        k: v for k, v in _headers.items() if k.lower() != "user-agent"
                    }

                    logger.info(f"Selected UA: {_headers['user-agent']}")

                    context = browser.new_context(
                        user_agent=_headers["user-agent"],
                        locale="en-US",
                        extra_http_headers=extra_headers,
                    )

                    page = context.new_page()
                    page.set_default_timeout(100000)

                    for attempt in range(1, max_retries + 1):
                        try:
                            page.goto("https://www.hyatt.com/", wait_until="load", timeout=120000)
                            human_delay(6, 12)

                            page.locator('input[data-id="location"]').wait_for(timeout=120000)
                            page.get_by_role("button", name="Find Hotels")

                            logger.info("Home page request completed successfully.....")

                            # ---- Mouse movement ----
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

                        except PlaywrightTimeoutError as pwex:
                            logger.warning(f"Attempt {attempt} failed: {pwex}")
                            if attempt < max_retries:
                                time.sleep(2)
                            else:
                                return self.build_response(success=False, data={"details": f"Failed after retries: {pwex}"}, status_code=103)

                    # ---- Room rates API calls ----
                    context.add_cookies([{"name": "rate_filter", "value": "woh", "domain": "hyatt.com", "path": "/"}])
                    cookies = context.cookies()
                    cookie_header = "; ".join([f"{c['name']}={c['value']}" for c in cookies])

                    api_url = (
                        f"https://www.hyatt.com/shop/service/rooms/roomrates/{hotel_id}"
                        f"?spiritCode={hotel_id}&rooms=1&adults={guest_count}"
                        f"&location={encoded_hotel_name}"
                        f"&checkinDate={check_in_date}&checkoutDate={check_out_date}"
                        f"&kids=0&rate=Standard&suiteUpgrade=true"
                    )

                    ref_url = f"https://www.hyatt.com/shop/rooms/{hotel_id}?location={encoded_hotel_name}&checkinDate={check_in_date}&checkoutDate={check_out_date}&rooms=1&adults={guest_count}&kids=0&rate=Standard&rateFilter=woh"

                    api_headers = {
                        'host': 'www.hyatt.com',
                        'sec-ch-ua-platform': _headers["sec-ch-ua-platform"],
                        'user-agent': _headers["user-agent"],
                        'sec-ch-ua': _headers["sec-ch-ua"],
                        'sec-ch-ua-mobile': _headers["sec-ch-ua-mobile"],
                        'accept': '*/*',
                        'sec-fetch-site': 'same-origin',
                        'sec-fetch-mode': 'cors',
                        'sec-fetch-dest': 'empty',
                        'referer': ref_url,
                        'accept-encoding': 'gzip, deflate, br, zstd',
                        # 'accept-language': 'en-US,en;q=0.9'
                        'cookie': cookie_header
                    }

                    logger.info(f"Navigating to roomrate API with reference, headers:: {api_url} :: {ref_url} :: {api_headers}")

                    response = page.request.get(url=api_url, headers=api_headers)

                    logger.info(f"Final Page Content content-type Headers: {response.headers.get('content-type')}")
                    logger.info(f"Final Page Content Data: {response.text()[:200]}")

                    decodedResponse = response.text()
                    if decodedResponse == "":
                    # if decodedResponse == "" and response.status == 200:
                        logger.info(f"Navigating to roomrate API Again with reference, headers:: {api_url} :: {ref_url} :: {api_headers}")

                        response = page.request.get(url=api_url, headers=api_headers)

                        logger.info(f"Final Page Content content-type Headers: {response.headers.get('content-type')}")
                        logger.info(f"Final Page Content Data: {response.text()[:200]}")
                        decodedResponse = response.text()
                        if decodedResponse == "" and response.status == 200:
                            status = 429
                            message = {
                                "details": f"Blank page occurred {status}"
                            }
                            return self.build_response(success=False, data=message, status_code=status)
                        elif decodedResponse == "":
                            message = {
                                "details": f"Blank page occurred {response.status}"
                            }
                            return self.build_response(success=False, data=message, status_code=response.status)




                    if '"invalidSpiritCode"' in decodedResponse:
                        logging.error("Property Code is invalid.")
                        message = {
                            "details": "Property Code is invalid."
                        }
                        return self.build_response(success=True, data=message, status_code=response.status)

                    data_json = None
                    if response.status == 200 and decodedResponse:
                        try:
                            data_json = json.loads(decodedResponse)
                        except Exception as e:
                            message = {
                                "details": f"Response Json not available {e}"
                            }
                            return self.build_response(success=False, data=message, status_code=response.status)

                    if response.status == 200 and data_json and "roomRates" in decodedResponse and "lowestAvgPointValue" in decodedResponse:
                        logger.info(f"Response fetched successfully from Roomrate API")
                        return self.build_response(success=True, data=data_json, status_code=response.status)
                    elif response.status == 200 and data_json and "roomRates" in decodedResponse and "lowestAvgPointValue" not in decodedResponse:
                        logger.error(f"Hotel is not available at selected date.")
                        message = {
                            "details": "Hotel is not available at selected date."
                        }
                        return self.build_response(success=True, data=message, status_code=response.status)
                    else:
                        logger.error(f"Roomrate API failed with status {response.status}")
                        message = {
                            "details": f"Roomrate API failed with status {response.status}"
                        }
                        return self.build_response(success=False, data=message, status_code=response.status)

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


# ---------------- Runner ----------------
if __name__ == "__main__":
    crawl = ExtractHyatt()
    data = crawl.get_search_data(
        hotel_id="yulzm-Hyatt Place Montreal - Downtown",
        check_in_date="2026-01-28",
        check_out_date="2026-01-29",
        guest_count=1,
        # hotel_id="m0207-Kinsterna Hotel",
        # check_in_date="2025-12-21",
        # check_out_date="2025-12-23",
        # guest_count=1,
    )
    if data:
        print("API data fetched successfully")
    else:
        print("API data could not be fetched with current cookies")
