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
        while browser_family != "chromium":
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
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=False,
                    # proxy=proxy,
                    args=[
                        # '--no-first-run',
                        # '--no-default-browser-check',
                        '--disable-blink-features=AutomationControlled',
                        # '--disable-http2',
                        # '--disable-web-security',
                        # '--disable-3d-apis',
                        # '--disable-webrtc-encryption',
                        # '--disable-features=WebRtcHideLocalIpsWithMdns',
                        # '--disable-features=VizDisplayCompositor',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        # '--disable-background-timer-throttling',
                        # '--disable-backgrounding-occluded-windows',
                        # '--disable-renderer-backgrounding'

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

                    api_url_part = f"/shop/service/rooms/roomrates/{hotel_id}"
                    # ✅ Handle cookie banner (OneTrust)
                    try:
                        page.click('button#onetrust-accept-btn-handler', timeout=5000)
                        print("Cookie banner accepted.")
                    except:
                        print("No cookie banner found or already accepted.")

                        # ✅ Wait for the location input to be visible and not blocked
                    page.wait_for_selector('input[data-id="location"]', timeout=10000)

                    # ✅ Click into the location field
                    page.focus('input[data-id="location"]')
                    page.click('.quickbookDestinationSearchField')

                    # ✅ Type with a delay (simulating human typing)
                    page.type('input[data-id="location"]', hotel_name, delay=120)

                    # ✅ Press Tab to trigger blur or suggestions
                    page.keyboard.press('Tab')

                    # ✅ Optional: wait for suggestion dropdown or location autofill to complete
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

                    with page.expect_response(lambda response: api_url_part in response.url,timeout=120000) as response_info:
                        page.focus('button[data-js="quickbookSearchFormButton"]')
                        page.wait_for_timeout(200)  # Wait 200 ms (optional, improves stability)
                        page.click('button[data-js="quickbookSearchFormButton"]')
                        human_delay(2, 6)
                        page.keyboard.press("PageDown")
                    response = response_info.value
                    decodedResponse = response.json()
                    if decodedResponse == "":
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

                    data_json = decodedResponse
                    #if response.status == 200 and decodedResponse:
                        # try:
                        #     data_json = json.loads(decodedResponse)
                        # except Exception as e:
                        #     message = {
                        #         "details": f"Response Json not available {e}"
                        #     }
                        #return self.build_response(success=False, data=message, status_code=response.status)

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
                            "details": f"Unknown Error{response.text()} with status: {response.status}"
                        }
                        if response.status == 522:
                            message = {
                                "details": f"Hyatt connection Error {response.text()}with status: {response.status}"
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
        print("API data fetched successfully", data)
    else:
        print("API data could not be fetched with current cookies")

# import json
# import logging
# import random as rand
# import time
# from datetime import datetime
# from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
# from urllib.parse import urlparse, quote
# from .proxy_manager import ProxyManager
# from .random_user_agent import get_random_sec_ch_headers, USER_AGENT
# from camoufox.sync_api import Camoufox
#
# # ---------------- Log configuration ----------------
# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s - %(levelname)s - %(message)s",
#     handlers=[
#         logging.FileHandler("hyatt.log"),
#         logging.StreamHandler()
#     ]
# )
# logger = logging.getLogger(__name__)
#
#
# def human_delay(a, b):
#     time.sleep(rand.uniform(a, b))
#
#
# class ExtractHyatt:
#
#     def __init__(self):
#         self._proxy_fetcher = ProxyManager()
#
#     def build_response(self, success: bool, data: any, status_code: int):
#         return {
#             "success": success,
#             "data": data,
#             "status_code": status_code
#         }
#
#     def get_search_data(self, hotel_id, check_in_date, check_out_date, guest_count, max_retries=3):
#         logger.info("Getting proxy IP for current session")
#         _proxy_url = self._proxy_fetcher.fetch_proxy()
#         if not _proxy_url:
#             message = "Proxy url not retrieved from the server"
#             return self.build_response(success=False, data=message, status_code=101)
#
#         parsed = urlparse(_proxy_url)
#         if parsed.username and parsed.password:
#             proxy = {
#                 "server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}",
#                 "username": parsed.username,
#                 "password": parsed.password,
#             }
#
#         logger.info("Proxy url dict created for request")
#         logger.info("Setting up crawler to extract data")
#
#         browser_family, headers = get_random_sec_ch_headers(USER_AGENT)
#         # You can force chromium if needed:
#         # while browser_family != "chromium":
#         #     browser_family, headers = get_random_sec_ch_headers(USER_AGENT)
#         _headers = headers
#
#         # Validate inputs
#         check_in = datetime.strptime(check_in_date, "%Y-%m-%d")
#         check_out = datetime.strptime(check_out_date, "%Y-%m-%d")
#         length_of_stay = (check_out - check_in).days
#         if not hotel_id or length_of_stay <= 0 or guest_count <= 0:
#             raise ValueError("hotel_id/no_of_stays/guest must have valid values.")
#
#         hotel_id_name = hotel_id
#         parts = hotel_id_name.split("-", 1)
#         hotel_id = parts[0].strip()
#         logger.info(f"Hotel ID: {hotel_id}")
#         hotel_name = parts[1].strip() if len(parts) > 1 else ""
#         logger.info(f"Hotel Name: {hotel_name}")
#         encoded_hotel_name = quote(hotel_name, safe="")
#
#         try:
#             with Camoufox(headless=True,proxy=proxy,geoip=True) as browser:
#                 # browser = p.chromium.launch(
#                 #     headless=True,
#                 #     proxy=proxy,
#                 #     args=[
#                 #         '--no-first-run',
#                 #         '--no-default-browser-check',
#                 #         '--disable-blink-features=AutomationControlled',
#                 #         '--disable-http2',
#                 #         '--disable-web-security',
#                 #         '--disable-3d-apis',
#                 #         '--disable-webrtc-encryption',
#                 #         '--disable-features=WebRtcHideLocalIpsWithMdns',
#                 #         '--disable-features=VizDisplayCompositor',
#                 #         '--disable-dev-shm-usage',
#                 #         '--no-sandbox',
#                 #         '--disable-setuid-sandbox',
#                 #         '--disable-background-timer-throttling',
#                 #         '--disable-backgrounding-occluded-windows',
#                 #         '--disable-renderer-backgrounding'
#                 #         "--start-maximized",
#                 #         "--disable-gpu",
#                 #         "--disable-infobars",
#                 #         "--ignore-certificate-errors",
#                 #         "--enable-features=NetworkService,NetworkServiceInProcess"
#                 #     ],
#                 # )
#                 try:
#                     logger.info("Sending Home page request....")
#                     extra_headers = {
#                         k: v for k, v in _headers.items() if k.lower() != "user-agent"
#                     }
#
#                     logger.info(f"Selected UA: {_headers['user-agent']}")
#                     context = browser.new_context(viewport={"width": 1920, "height": 1080},
#                                                   user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
#                                                               "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"),
#                                                   locale="en-US")
#
#                     # context = browser.new_context(
#                     #     viewport={"width": 1920, "height": 1080},
#                     #     user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
#                     #     # user_agent=_headers["user-agent"],
#                     #     # locale="en-US",
#                     #     # extra_http_headers=extra_headers,
#                     #     # viewport={"width": 1920, "height": 1080},
#                     # )
#
#                     page = context.new_page()
#                     page.set_default_timeout(100000)
#
#                     # Disable animations for smoother operation in headed mode
#                     # page.add_style_tag(content="""
#                     #     *, *::before, *::after {
#                     #         transition: none !important;
#                     #         animation: none !important;
#                     #     }
#                     # """)
#
#                     for attempt in range(1, max_retries + 1):
#                         try:
#                             page.goto("https://www.hyatt.com/", wait_until="domcontentloaded")
#                             human_delay(6, 12)
#                             # page.wait_for_load_state("networkidle", timeout=60000)
#
#
#                             page.locator('input[data-id="location"]').wait_for(timeout=120000)
#                             page.get_by_role("button", name="Find Hotels")
#                             page.wait_for_selector('.quickbookDestinationSearchField', timeout=30000)
#                             page.wait_for_timeout(3000)
#
#
#                             logger.info("Home page request completed successfully.....")
#
#                             # ---- Mouse movement to mimic human behavior ----
#                             logger.info("Sleeping for few seconds for mouse movement.....")
#                             human_delay(2, 5)
#                             page.mouse.move(rand.randint(0, 2), rand.randint(3, 8))
#                             page.mouse.down()
#                             page.mouse.move(0, rand.randint(100, 120))
#                             page.mouse.move(rand.randint(100, 120), rand.randint(100, 120))
#                             page.mouse.move(rand.randint(100, 120), 0)
#                             page.mouse.move(0, 0)
#                             page.mouse.up()
#
#                             page.keyboard.press("PageDown")
#                             human_delay(1, 3)
#                             page.keyboard.press("PageUp")
#                             human_delay(2, 4)
#
#                             logger.info("Mouse movement completed.....")
#                             break
#
#                         except PlaywrightTimeoutError as pwex:
#                             logger.warning(f"Attempt {attempt} failed: {pwex}")
#                             if attempt < max_retries:
#                                 time.sleep(2)
#                             else:
#                                 return self.build_response(success=False, data={"details": f"Failed after retries: {pwex}"}, status_code=103)
#
#                     api_url_part = f"/shop/service/rooms/roomrates/{hotel_id}"
#
#                     # Handle cookie banner (OneTrust)
#                     try:
#                         page.click('button#onetrust-accept-btn-handler', timeout=5000)
#                         logger.info("Cookie banner accepted.")
#                     except Exception:
#                         logger.info("No cookie banner found or already accepted.")
#
#                     # Wait for location input ready
#                     page.wait_for_selector('input[data-id="location"]', timeout=10000)
#                     page.focus('input[data-id="location"]')
#                     page.click('.quickbookDestinationSearchField')
#
#                     # Type hotel name with delay to mimic human typing
#                     page.type('input[data-id="location"]', hotel_name, delay=565)
#                     human_delay(0.2, 1.5)
#                     if not page.locator(".typeahead-content li.property").count():
#                         print("⚠️ No dropdown options found. HTML snapshot:")
#                         html_content = page.content()
#
#                         # Save to file
#                         with open("hyatt_page.html", "w", encoding="utf-8") as f:
#                             f.write(html_content)
#                     page.locator(".typeahead-content.is-open li.property").first.wait_for(timeout=30000)
#                     page.locator(".typeahead-content.is-open li.property").first.click()
#
#
#                     page.keyboard.press('Tab')
#                     human_delay(1, 3)
#
#                     page.fill('input[data-id="checkinDate"]', check_in_date)
#                     page.keyboard.press('Tab')
#                     human_delay(1, 3)
#
#                     page.fill('input[data-id="checkoutDate"]', check_out_date)
#                     human_delay(1, 3)
#                     page.keyboard.press('Tab')
#                     human_delay(1, 3)
#                     page.keyboard.press('Tab')
#                     human_delay(1, 3)
#                     page.keyboard.press('Tab')
#                     page.keyboard.press('Tab')
#                     page.keyboard.press('Enter')
#
#                     use_points_label = page.locator('label.input-checkbox', has_text='Use Points')
#                     use_points_label.wait_for(state='visible', timeout=30000)
#                     use_points_label.click()
#                     human_delay(2, 6)
#                     human_delay(1, 3)
#
#                     # page.wait_for_load_state("networkidle", timeout=60000)
#                     page.wait_for_selector('button[data-js="quickbookSearchFormButton"]:not([disabled])', timeout=30000)
#
#                     # Optional debug: log all requests
#                     # page.on("request", lambda request: print("Request:", request.url))
#
#                     # Initialize a variable to store API response
#                     api_data = None
#
#                     # Define response handler
#                     def handle_response(response):
#                         nonlocal api_data
#                         if api_url_part in response.url:
#                             try:
#                                 api_data = response.json()
#                             except:
#                                 api_data = response.text()
#
#                     # Attach the response handler
#                     page.on("response", handle_response)
#
#                     # Wait until the button is visible
#                     button = page.locator('button[data-js="quickbookSearchFormButton"]')
#                     button.wait_for(state="visible", timeout=15000)  # wait up to 15 sec
#
#                     # Scroll button into view and click forcefully
#                     button.scroll_into_view_if_needed()
#                     button.click(force=True)
#
#                     # Wait for API response (timeout 120 seconds)
#                     for _ in range(120):
#                         if api_data is not None:
#                             break
#                         time.sleep(1)
#
#                     # Debugging if response not received
#                     if api_data:
#                         print("API data received:", api_data)
#                     else:
#                         page.screenshot(path="headless_fail.png")
#                         print("No API response received. Screenshot saved as headless_fail.png")
#
#                     # with page.expect_response(lambda response: api_url_part in response.url,
#                     #                           timeout=120000) as response_info:
#                     #     page.click('button[data-js="quickbookSearchFormButton"]')
#                     #
#                     # response = response_info.value
#                     decodedResponse = api_data
#
#                     # # Wait for the search button to be visible and enabled before clicking
#                     # page.wait_for_selector('button[data-js="quickbookSearchFormButton"]', state='visible', timeout=30000)
#                     #
#                     # # # Correct usage of expect_response: only click inside
#                     # # with page.expect_response(lambda response: api_url_part in response.url, timeout=120000) as response_info:
#                     # #     page.click('button[data-js="quickbookSearchFormButton"]')
#                     # #
#                     # # response = response_info.value
#                     #
#                     # with page.expect_request(lambda request: api_url_part in request.url,
#                     #                          timeout=120000) as request_info:
#                     #     page.click('button[data-js="quickbookSearchFormButton"]')
#                     #
#                     # request = request_info.value
#                     # response = request.response()
#                     #
#                     # decodedResponse = response.json()
#
#                     # if decodedResponse == "":
#                     #     if response.status == 200:
#                     #         status = 429
#                     #         message = {
#                     #             "details": f"Blank page occurred {status}"
#                     #         }
#                     #         return self.build_response(success=False, data=message, status_code=status)
#                     #     else:
#                     #         message = {
#                     #             "details": f"Blank page occurred {response.status}"
#                     #         }
#                     #         return self.build_response(success=False, data=message, status_code=response.status)
#
#                     if '"invalidSpiritCode"' in decodedResponse:
#                         logger.error("Property Code is invalid.")
#                         message = {
#                             "details": "Property Code is invalid."
#                         }
#                         return self.build_response(success=True, data=message, status_code=12)
#
#                     data_json = decodedResponse
#                     room_rates = decodedResponse.get("roomRates", {})
#                     lowest_avg_exists = any(
#                         "lowestAvgPointValue" in rate_info
#                         for rate_info in room_rates.values()
#                     )
#                     #
#                     # if response.status == 200 and data_json and "roomRates" in decodedResponse and lowest_avg_exists:
#                     #     logger.info(f"Response fetched successfully from Roomrate API")
#                     #     return self.build_response(success=True, data=data_json, status_code=response.status)
#                     # elif response.status == 200 and data_json and "roomRates" in decodedResponse and not lowest_avg_exists:
#                     #     logger.error(f"Hotel is not available at selected date.")
#                     #     message = {
#                     #         "details": "Hotel is not available at selected date."
#                     #     }
#                     #     return self.build_response(success=True, data=message, status_code=response.status)
#                     # else:
#                     #     logger.error(f"Roomrate API failed with status {response.status}")
#                     #     message = {
#                     #         "details": f"Unknown Error {response.text()} with status: {response.status}"
#                     #     }
#                     #     if response.status == 522:
#                     #         message = {
#                     #             "details": f"Hyatt connection Error {response.text()} with status: {response.status}"
#                     #         }
#                     #     return self.build_response(success=False, data=message, status_code=response.status)
#
#                 except Exception as ex:
#                     logger.exception(f"Exception occurred during scraping: {ex}")
#                     message = {
#                         "details": f"Exception occurred during scraping: {ex}"
#                     }
#                     return self.build_response(success=False, data=message, status_code=103)
#
#                 finally:
#                     logger.info("Closing browser...")
#                     browser.close()
#
#         except Exception as ex:
#             logger.exception(f"Critical Error: {ex}")
#             message = {
#                 "details": f"Critical Error: {ex}"
#             }
#             return self.build_response(success=False, data=message, status_code=100)
#
#
# # ---------------- Runner ----------------
# if __name__ == "__main__":
#     crawl = ExtractHyatt()
#     data = crawl.get_search_data(
#         hotel_id="goazg-Hyatt Place Goa Candolim",
#         check_in_date="2026-01-07",
#         check_out_date="2026-01-08",
#         guest_count=1,
#     )
#     if data:
#         print("API data fetched successfully", data)
#     else:
#         print("API data could not be fetched with current cookies")
#
