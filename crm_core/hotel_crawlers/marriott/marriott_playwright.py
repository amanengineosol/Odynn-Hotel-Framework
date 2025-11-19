import json
import logging
import random as rand
import time
from datetime import datetime
from enum import verify

from playwright.sync_api import sync_playwright , TimeoutError as PlaywrightTimeoutError
from urllib.parse import urlparse, quote
from .proxy_manager import ProxyManager
from .random_user_agent import get_random_sec_ch_headers, USER_AGENT
import requests

# ---------------- Log configuration ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("marriott.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def human_delay(a, b):
    time.sleep(rand.uniform(a, b))


class ExtractMarriott:

    def __init__(self):
        self._proxy_fetcher = ProxyManager()

    def linux_format_marriott_date(self, dt_str):
        dt = datetime.strptime(dt_str, "%Y-%m-%d")
        # Format like: Tue, Nov 4
        return dt.strftime("%a %b %d %Y")   #linux

    def windows_format_marriott_date(self, dt_str):
        dt = datetime.strptime(dt_str, "%Y-%m-%d")
        # Format like: Tue, Nov 4
        return dt.strftime("%a %b %d %Y")   # On Windows use

    def build_response(self, success: bool, data: any, status_code: int):
        return {
            "success": success,
            "data": data,
            "status_code": status_code
        }

    def get_search_data(self, hotel_id, check_in_date, check_out_date, guest_count, max_retries=3):
        logger.info("Getting proxy IP for current session")
        _proxy_url = self._proxy_fetcher.fetch_proxy()
        proxies = {
            'http': _proxy_url,
            'https': _proxy_url
        }
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

        session = requests.Session()
        session.proxies.update(proxies)
        session.headers.update(_headers)
        # logger.info(f"Session Headers :: {session.headers}")

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
                    proxy=proxy,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--start-maximized",
                        "--disable-dev-shm-usage",
                        "--no-sandbox",
                        "--disable-gpu",
                        "--disable-infobars",
                        "--ignore-certificate-errors",
                        "--enable-features=NetworkService,NetworkServiceInProcess",
                        '--disable-features=VizDisplayCompositor',
                        '--disable-extensions',
                        '--disable-plugins-discovery',
                        '--window-size=1366, 768',
                        '--view-port=1366, 768',
                        '--disable-gpu',
                        '--disable-dev-hooks',
                        '--disable-logging',
                        '--disable-popup-buttons',
                        '--disable-popup-content',
                        '--disable-popup-menu',
                        '--disable-popup-notifications',
                        '--disable-popup-polling',
                        '--disable-popup-templates',
                        '--disable-popup-widgets',
                        '--disable-popup-widget-notifications',
                        '--disable-popup-layouts',
                        '--mute-audio',
                        '--enable-javascript',
                        '--lang=en-US,en;q=0.9',
                        '--disable-renderer-backgrounding',
                        '--disable-infobars',
                    ],
                )
                try:
                    logger.info("Sending Home page request....")
                    extra_headers = {
                        k: v for k, v in _headers.items() if k.lower() != "user-agent"
                    }

                    logger.info(f"Selected UA: {_headers['user-agent']}")

                    context = browser.new_context(
                        # user_agent=_headers["user-agent"],
                        # locale="en-US",
                        # extra_http_headers=extra_headers
                        viewport=None,
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
                        locale="en-US",
                        permissions=["geolocation"],
                    )

                    page = context.new_page()
                    page.set_viewport_size({"width": 1920, "height": 1080})
                    page.set_default_timeout(100000)

                    for attempt in range(1, max_retries + 1):
                        try:
                            page.goto("https://www.marriott.com/", wait_until="load", timeout=120000)
                            human_delay(6, 12)

                            page.get_by_role("button", name="Find Hotels").wait_for(timeout=120000)

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
                                return self.build_response(success=False,
                                                           data={"details": f"Failed after retries: {pwex}"},
                                                           status_code=103)

                    def go_to_month(page, target_month_year: str):
                        """
                        target_month_year should be like 'October 2025'.
                        """
                        while True:
                            captions = page.query_selector_all(
                                "//*[contains(@class, 'DayPicker-Caption')]//div[@data-scroll-date-marker]")
                            months = [c.inner_text().strip() for c in captions]

                            if target_month_year in months:
                                break

                            next_button = page.query_selector("//*[contains(@class, 'DayPicker-NavButton--next')]")
                            if next_button and next_button.is_visible():
                                next_button.click()
                                time.sleep(rand.uniform(1, 2))
                            else:
                                raise Exception(f"Could not find month {target_month_year}")

                    # ---- Destination ----
                    dest_input = page.query_selector('input[id="downshift-1-input"]')
                    dest_input.wait_for_element_state("visible", timeout=120_000)
                    dest_input.click()
                    human_delay(1, 3)
                    dest_input.type(hotel_name, delay=500)

                    # Select first dropdown suggestion
                    human_delay(1, 1.8)
                    suggest_hotelcheck = page.query_selector("//*[@role='option']")
                    suggest_hotelcheck.wait_for_element_state("visible", timeout=5000)
                    suggest_hotel = page.query_selector_all("//*[@role='option']")
                    if not suggest_hotel:
                        raise Exception("No hotel suggestions found in dropdown!")
                    suggest_hotel[0].click()
                    human_delay(1.2, 2.5)

                #     # Open calendar
                #     date_input = page.query_selector("//input[@aria-label='date-picker']")
                #     date_input.wait_for_element_state("visible", timeout=120_000)
                #     date_input.click()
                #     human_delay(1, 2)
                #
                #     if _headers["sec-ch-ua-platform"] == '"Linux"':
                #         check_in_label = self.linux_format_marriott_date(check_in_date)
                #         check_out_label = self.linux_format_marriott_date(check_out_date)
                #     else:
                #         check_in_label = self.windows_format_marriott_date(check_in_date)
                #         check_out_label = self.windows_format_marriott_date(check_out_date)
                #
                #     checkin_month_year = datetime.strptime(check_in_date, "%Y-%m-%d").strftime("%B %Y")
                #     checkout_month_year = datetime.strptime(check_out_date, "%Y-%m-%d").strftime("%B %Y")
                #
                #     logger.info(f"Checkin month year: {checkin_month_year}")
                #     logger.info(f"Checkout month year: {checkout_month_year}")
                #     logger.info(f"check_in_label: {check_in_label}")
                #     logger.info(f"check_out_label: {check_out_label}")
                #
                # # Navigate to check-in month
                #     human_delay(1, 2)
                #     go_to_month(page, checkin_month_year)
                #     check_in_button = page.query_selector(
                #         f"//div[contains(@class, 'DayPicker-Day') and @aria-label='{check_in_label}']")
                #     check_in_button.wait_for_element_state("visible", timeout=120_000)
                #     check_in_button.click()
                #     human_delay(6, 12)
                #
                #     # Navigate to check-out month
                #     go_to_month(page, checkout_month_year)
                #     check_out_button = page.query_selector(
                #         f"//div[contains(@class, 'DayPicker-Day') and @aria-label='{check_out_label}']")
                #     check_out_button.wait_for_element_state("visible", timeout=120_000)
                #     check_out_button.click()
                #     human_delay(1.3, 2.6)
                #
                #     done_button = page.query_selector("//button[@aria-label='Done']")
                #     done_button.wait_for_element_state("visible", timeout=120_000)
                #     done_button.click()
                #     human_delay(1, 2)

                    # ---- Use Points/Awards ----
                    use_points_label = page.query_selector("//label[@for='usepoints-checkbox']")
                    use_points_label.wait_for_element_state("visible", timeout=120_000)
                    human_delay(0.5, 1.5)
                    use_points_label.click()
                    human_delay(6, 12)

                    # ---- Find Hotels ----
                    find_hotels_button = page.query_selector(
                        "//button[contains(@class, 'update-search-btn') and contains(text(), 'Find Hotels')]")
                    find_hotels_button.wait_for_element_state("visible", timeout=120_000)
                    find_hotels_button.click()
                    time.sleep(10)
                    human_delay(0.5, 1.5)
                    page.wait_for_timeout(100000)  # Wait for API responses

                    # # ---- View Rates ----
                    # human_delay(2, 6)
                    # viewRates_button = page.query_selector(
                    #     "//a[contains(@class, 'view-rates-button-container') and @aria-label='View Rates']")
                    # viewRates_button.wait_for_element_state("visible", timeout=240000)
                    # viewRates_button.click()
                    #
                    # time.sleep(9)


                except Exception as ex:
                    logger.exception(f"Exception occurred during scraping: {ex}")
                    return {"success": False, "details": f"Exception occurred during scraping: {ex}"}
                finally:
                    logger.info("Closing browser...")
                    browser.close()

                    # # --- Parse API responses ---
                    # if api_responses:
                    #     logger.info("Captured Marriott API responses:")
                    #     for url, resp in api_responses.items():
                    #         edges = resp["data"]["searchProductsByProperty"]["edges"]
                    #         has_standard = any(
                    #             edge["node"]["availabilityAttributes"]["rateCategory"]["type"]["code"] == "standard" for
                    #             edge in edges)
                    #         has_redemption = any(
                    #             edge["node"]["availabilityAttributes"]["rateCategory"]["type"]["code"] == "redemption"
                    #             for edge in edges)
                    #
                    #         if '"Invalid Property Code"' in str(resp):
                    #             logger.error("Property Code is invalid.")
                    #             return {"success": True, "details": "Property Code is invalid."}
                    #         elif has_standard and has_redemption:
                    #             logger.info("Response fetched successfully from Roomrate API")
                    #             return {"success": True, "data": resp}
                    #         elif has_standard and not has_redemption:
                    #             logger.error("Hotel is not available at selected date.")
                    #             return {"success": True, "details": "Hotel is not available at selected date."}
                    # else:
                    #     logger.error("Roomrate API failed")
                    #     return {"success": False, "details": "Roomrate API failed"}


        except Exception as ex:
            logger.exception(f"Critical Error: {ex}")
            message = {
                "details": f"Critical Error: {ex}"
            }
            return self.build_response(success=False, data=message, status_code=100)

# Example run
if __name__ == "__main__":
    crawl = ExtractMarriott()
    data = crawl.get_search_data(
        hotel_id="swfhr-inn-at-bellefield-hyde-park",
        check_in_date="2025-12-04",
        check_out_date="2025-12-08",
        guest_count=1,
    )
    if data:
        print("API data fetched successfully")
    else:
        print("API data could not be fetched with current cookies")

#                     # ---- Room rates API calls ----
#                     # context.add_cookies([{"name": "rate_filter", "value": "woh", "domain": "hyatt.com", "path": "/"}])
#                     cookies = context.cookies()
#                     for cookie in cookies:
#                         if cookie['name'] == "MI_SITE":
#                             cookie['value'] = "prod17"
#                     cookie_header = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
#                     logger.info(f"Cookies: {cookie_header}")
#                     ghar = 'false'
#                     api_url = "https://www.marriott.com/mi/query/PhoenixBookSearchProductsByProperty"
# #                     api_payload = {
# #     "operationName": "PhoenixBookSearchProductsByProperty",
# #     "variables": {
# #         "search": {
# #             "options": {
# #                 "startDate": "2025-11-12",
# #                 "endDate": "2025-11-14",
# #                 "quantity": 1,
# #                 "numberInParty": 1,
# #                 "childAges": [],
# #                 "productRoomType": [
# #                     "ALL"
# #                 ],
# #                 "productStatusType": [
# #                     "AVAILABLE"
# #                 ],
# #                 "rateRequestTypes": [
# #                     {
# #                         "value": "",
# #                         "type": "STANDARD"
# #                     },
# #                     {
# #                         "value": "",
# #                         "type": "PREPAY"
# #                     },
# #                     {
# #                         "value": "",
# #                         "type": "PACKAGES"
# #                     },
# #                     {
# #                         "value": "MRM",
# #                         "type": "CLUSTER"
# #                     },
# #                     {
# #                         "value": "",
# #                         "type": "REDEMPTION"
# #                     }
# #                 ],
# #                 "isErsProperty": ghar
# #             },
# #             "propertyId": "SWFHR"
# #         },
# #         "offset": 0,
# #         "limit": 150
# #     },
# #     "query": "query PhoenixBookSearchProductsByProperty($search: ProductByPropertySearchInput, $offset: Int, $limit: Int) {\n  searchProductsByProperty(search: $search, offset: $offset, limit: $limit) {\n    edges {\n      node {\n        ... on HotelRoom {\n          availabilityAttributes {\n            rateCategory {\n              type {\n                code\n                __typename\n              }\n              value\n              __typename\n            }\n            isNearSellout\n            __typename\n          }\n          rates {\n            name\n            description\n            rateAmounts {\n              amount {\n                origin {\n                  amount\n                  currency\n                  valueDecimalPoint\n                  __typename\n                }\n                __typename\n              }\n              points\n              pointsSaved\n              pointsToPurchase\n              __typename\n            }\n            localizedDescription {\n              translatedText\n              sourceText\n              __typename\n            }\n            localizedName {\n              translatedText\n              sourceText\n              __typename\n            }\n            rateAmountsByMode {\n              averageNightlyRatePerUnit {\n                amount {\n                  origin {\n                    amount\n                    currency\n                    valueDecimalPoint\n                    __typename\n                  }\n                  __typename\n                }\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          basicInformation {\n            type\n            name\n            localizedName {\n              translatedText\n              __typename\n            }\n            description\n            localizedDescription {\n              translatedText\n              __typename\n            }\n            membersOnly\n            oldRates\n            representativeRoom\n            housingProtected\n            actualRoomsAvailable\n            depositRequired\n            roomsAvailable\n            roomsRequested\n            ratePlan {\n              ratePlanType\n              ratePlanCode\n              marketCode\n              __typename\n            }\n            freeCancellationUntil\n            __typename\n          }\n          roomAttributes {\n            attributes {\n              id\n              description\n              groupID\n              category {\n                code\n                description\n                __typename\n              }\n              accommodationCategory {\n                code\n                description\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          totalPricing {\n            quantity\n            rateAmountsByMode {\n              grandTotal {\n                amount {\n                  origin {\n                    value: amount\n                    valueDecimalPoint\n                    __typename\n                  }\n                  __typename\n                }\n                __typename\n              }\n              subtotalPerQuantity {\n                amount {\n                  origin {\n                    currency\n                    value: amount\n                    valueDecimalPoint\n                    __typename\n                  }\n                  __typename\n                }\n                __typename\n              }\n              totalMandatoryFeesPerQuantity {\n                amount {\n                  origin {\n                    currency\n                    value: amount\n                    valueDecimalPoint\n                    __typename\n                  }\n                  __typename\n                }\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          id\n          __typename\n        }\n        id\n        __typename\n      }\n      __typename\n    }\n    total\n    status {\n      ... on UserInputError {\n        httpStatus\n        messages {\n          user {\n            message\n            field\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      ... on DateRangeTooLongError {\n        httpStatus\n        messages {\n          user {\n            message\n            field\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n"
# # }
#                     # api_headers = {
#                     #     'application-name': 'book',
#                     #     'x-request-id': '',
#                     #     'graphql-operation-name': 'PhoenixBookSearchProductsByProperty',
#                     #     'graphql-force-safelisting': 'true',
#                     #     # 'user_agent': _headers["user-agent"],
#                     #     'accept': '*/*',
#                     #     'apollographql-client-version': '1',
#                     #     'content-type': 'application/json',
#                     #     'apollographql-client-name': 'phoenix_book',
#                     #     'graphql-require-safelisting': 'true',
#                     #     'accept-language': 'en-US',
#                     #     'graphql-operation-signature': 'a1079a703a2d21d82c0c65e4337271c3029c69028c6189830f30882170075756',
#                     #     'origin': 'https://www.marriott.com',
#                     #     'sec-fetch-site': 'same-origin',
#                     #     'sec-fetch-mode': 'cors',
#                     #     'sec-fetch-dest': 'document',
#                     #     'referer': 'https://www.marriott.com/reservation/rateListMenu.mi',
#                     #     'cookie': cookie_header
#                     # }
#
#                     api_paylod  = '{"operationName":"PhoenixBookSearchProductsByProperty","variables":{"search":{"options":{"startDate":"2025-11-04","endDate":"2025-11-08","quantity":1,"numberInParty":1,"childAges":[],"productRoomType":["ALL"],"productStatusType":["AVAILABLE"],"rateRequestTypes":[{"value":"","type":"STANDARD"},{"value":"","type":"PREPAY"},{"value":"","type":"PACKAGES"},{"value":"MRM","type":"CLUSTER"},{"value":"","type":"REDEMPTION"}],"isErsProperty":false},"propertyId":"SNABP"},"offset":0,"limit":150},"query":"query PhoenixBookSearchProductsByProperty($search: ProductByPropertySearchInput, $offset: Int, $limit: Int) {\n  searchProductsByProperty(search: $search, offset: $offset, limit: $limit) {\n    edges {\n      node {\n        ... on HotelRoom {\n          availabilityAttributes {\n            rateCategory {\n              type {\n                code\n                __typename\n              }\n              value\n              __typename\n            }\n            isNearSellout\n            __typename\n          }\n          rates {\n            name\n            description\n            rateAmounts {\n              amount {\n                origin {\n                  amount\n                  currency\n                  valueDecimalPoint\n                  __typename\n                }\n                __typename\n              }\n              points\n              pointsSaved\n              pointsToPurchase\n              __typename\n            }\n            localizedDescription {\n              translatedText\n              sourceText\n              __typename\n            }\n            localizedName {\n              translatedText\n              sourceText\n              __typename\n            }\n            rateAmountsByMode {\n              averageNightlyRatePerUnit {\n                amount {\n                  origin {\n                    amount\n                    currency\n                    valueDecimalPoint\n                    __typename\n                  }\n                  __typename\n                }\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          basicInformation {\n            type\n            name\n            localizedName {\n              translatedText\n              __typename\n            }\n            description\n            localizedDescription {\n              translatedText\n              __typename\n            }\n            membersOnly\n            oldRates\n            representativeRoom\n            housingProtected\n            actualRoomsAvailable\n            depositRequired\n            roomsAvailable\n            roomsRequested\n            ratePlan {\n              ratePlanType\n              ratePlanCode\n              marketCode\n              __typename\n            }\n            freeCancellationUntil\n            __typename\n          }\n          roomAttributes {\n            attributes {\n              id\n              description\n              groupID\n              category {\n                code\n                description\n                __typename\n              }\n              accommodationCategory {\n                code\n                description\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          totalPricing {\n            quantity\n            rateAmountsByMode {\n              grandTotal {\n                amount {\n                  origin {\n                    value: amount\n                    valueDecimalPoint\n                    __typename\n                  }\n                  __typename\n                }\n                __typename\n              }\n              subtotalPerQuantity {\n                amount {\n                  origin {\n                    currency\n                    value: amount\n                    valueDecimalPoint\n                    __typename\n                  }\n                  __typename\n                }\n                __typename\n              }\n              totalMandatoryFeesPerQuantity {\n                amount {\n                  origin {\n                    currency\n                    value: amount\n                    valueDecimalPoint\n                    __typename\n                  }\n                  __typename\n                }\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          id\n          __typename\n        }\n        id\n        __typename\n      }\n      __typename\n    }\n    total\n    status {\n      ... on UserInputError {\n        httpStatus\n        messages {\n          user {\n            message\n            field\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      ... on DateRangeTooLongError {\n        httpStatus\n        messages {\n          user {\n            message\n            field\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n"}'
#
#
#                     logger.info(
#                         f"Navigating to roomrate API with headers:: {api_url} ::")
#
#                     response = page.request.post(url=api_url, data=api_paylod)
#
#                     logger.info(f"Final Page Content content-type Headers: {response.headers.get('content-type')}")
#                     logger.info(f"Final Page Content Data: {response.text()[:200]}")
#
#                     decodedResponse = response.text()
#                     if '"Invalid Property Code"' in decodedResponse:
#                         logging.error("Property Code is invalid.")
#                         message = {
#                             "details": "Property Code is invalid."
#                         }
#                         return self.build_response(success=True, data=message, status_code=response.status)
#
#                     data_json = None
#                     if response.status == 200 and decodedResponse:
#                         try:
#                             data_json = json.loads(decodedResponse)
#                         except Exception as e:
#                             message = {
#                                 "details": f"Response Json not available {e}"
#                             }
#                             return self.build_response(success=False, data=message, status_code=response.status)
#
#                     if response.status == 200 and data_json and '"code":"standard"' in decodedResponse and '"code":"redemption"' in decodedResponse:
#                         logger.info(f"Response fetched successfully from Roomrate API")
#                         return self.build_response(success=True, data=data_json, status_code=response.status)
#                     elif response.status == 200 and data_json and '"code":"standard"' in decodedResponse and '"code":"redemption"' not in decodedResponse:
#                         logger.error(f"Hotel is not available at selected date.")
#                         message = {
#                             "details": "Hotel is not available at selected date."
#                         }
#                         return self.build_response(success=True, data=message, status_code=response.status)
#                     else:
#                         logger.error(f"Roomrate API failed with status {response.status}")
#                         message = {
#                             "details": f"Roomrate API failed with status {response.status}"
#                         }
#                         return self.build_response(success=False, data=message, status_code=response.status)
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
#         except Exception as ex:
#             logger.exception(f"Critical Error: {ex}")
#             message = {
#                 "details": f"Critical Error: {ex}"
#             }
#             return self.build_response(success=False, data=message, status_code=100)
#
#
# if __name__ =="__main__":
#     crawl = ExtractMarriott()
#     data = crawl.get_search_data(
#         hotel_id="SWFHR-swfhr-inn-at-bellefield-hyde-park",
#         check_in_date="2025-11-04",
#         check_out_date="2025-11-08",
#         guest_count=1,
#     )
#     if data:
#         print("API data fetched successfully")
#     else:
#         print("API data could not be fetched with current cookies")