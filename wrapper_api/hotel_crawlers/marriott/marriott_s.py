import json
import logging
import random as rand
import time
from datetime import datetime
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

        proxies = {
            'http': _proxy_url,
            'https': _proxy_url
        }
        logger.info("Proxy url dict created for request")

        # ---------- Session Setup ----------
        session = requests.Session()
        session.proxies.update(proxies)

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
                            page.goto("https://www.marriott.com/default.mi", wait_until="load", timeout=120000)
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

                    # ---- Room rates API calls ----s
                    cookies = context.cookies()
                    cookie_header = "; ".join([f"{c['name']}={c['value']}" for c in cookies])

                    # ---------- Book Property Page ----------
                    BookPropertyUrl = "https://www.marriott.com/mi/query/PhoenixBookProperty"
                    BookPropertyPayload = json.dumps({
                        "operationName": "PhoenixBookProperty",
                        "variables": {
                            "propertyId": hotel_id.upper()
                        },
                        "query": "query PhoenixBookProperty($propertyId: ID!) {\n  property(id: $propertyId) {\n    ... on Hotel {\n      basicInformation {\n        ... on HotelBasicInformation {\n          descriptions {\n            type {\n              code\n              __typename\n            }\n            text\n            __typename\n          }\n          isAdultsOnly\n          resort\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n"
                    })
                    session.headers.update({
                        'host': 'www.marriott.com',
                        'application-name': 'book',
                        'x-request-id': '',
                        'sec-ch-ua-platform': _headers["sec-ch-ua-platform"],
                        'user-agent': _headers["user-agent"],
                        'sec-ch-ua': _headers["sec-ch-ua"],
                        'sec-ch-ua-mobile': _headers["sec-ch-ua-mobile"],
                        'graphql-operation-name': 'PhoenixBookProperty',
                        'graphql-force-safelisting': 'true',
                        'accept': '*/*',
                        'apollographql-client-version': '1',
                        'content-type': 'application/json',
                        'apollographql-client-name': 'phoenix_book',
                        'graphql-require-safelisting': 'true',
                        'accept-language': 'en-US',
                        'graphql-operation-signature': '9f165424df22961c9a0d1664c26b9130e2fcf0318bc78c25972cc2e505455376',
                        'origin': 'https://www.marriott.com',
                        'sec-fetch-site': 'same-origin',
                        'sec-fetch-mode': 'cors',
                        'sec-fetch-dest': 'empty',
                        'referer': 'https://www.marriott.com/reservation/rateListMenu.mi',
                        'accept-encoding': 'gzip, deflate, br, zstd',
                        'cookie': cookie_header,
                    })

                    BookPropertyResponse = session.post(url=BookPropertyUrl, data=BookPropertyPayload)
                    logger.info(f"PhoenixBookProperty Status: {BookPropertyResponse.status_code}")
                    logger.info(f"PhoenixBookProperty Data: {BookPropertyResponse.text[:200]}")

                    # ---------- Rate List API ----------
                    api_url = "https://www.marriott.com/mi/query/PhoenixBookSearchProductsByProperty"
                    api_payload = json.dumps({
                          "operationName": "PhoenixBookSearchProductsByProperty",
                          "variables": {
                            "search": {
                              "options": {
                                "startDate": check_in_date,
                                "endDate": check_out_date,
                                "quantity": 1,
                                "numberInParty": guest_count,
                                "childAges": [],
                                "productRoomType": [
                                  "ALL"
                                ],
                                "productStatusType": [
                                  "AVAILABLE"
                                ],
                                "rateRequestTypes": [
                                  {
                                    "value": "",
                                    "type": "STANDARD"
                                  },
                                  {
                                    "value": "",
                                    "type": "PREPAY"
                                  },
                                  {
                                    "value": "",
                                    "type": "PACKAGES"
                                  },
                                  {
                                    "value": "MRM",
                                    "type": "CLUSTER"
                                  },
                                  {
                                    "value": "",
                                    "type": "REDEMPTION"
                                  }
                                ],
                                "isErsProperty": False
                              },
                              "propertyId": hotel_id.upper()
                            },
                            "offset": 0,
                            "limit": 150
                          },
                          "query": "query PhoenixBookSearchProductsByProperty($search: ProductByPropertySearchInput, $offset: Int, $limit: Int) {\n  searchProductsByProperty(search: $search, offset: $offset, limit: $limit) {\n    edges {\n      node {\n        ... on HotelRoom {\n          availabilityAttributes {\n            rateCategory {\n              type {\n                code\n                __typename\n              }\n              value\n              __typename\n            }\n            isNearSellout\n            __typename\n          }\n          rates {\n            name\n            description\n            rateAmounts {\n              amount {\n                origin {\n                  amount\n                  currency\n                  valueDecimalPoint\n                  __typename\n                }\n                __typename\n              }\n              points\n              pointsSaved\n              pointsToPurchase\n              __typename\n            }\n            localizedDescription {\n              translatedText\n              sourceText\n              __typename\n            }\n            localizedName {\n              translatedText\n              sourceText\n              __typename\n            }\n            rateAmountsByMode {\n              averageNightlyRatePerUnit {\n                amount {\n                  origin {\n                    amount\n                    currency\n                    valueDecimalPoint\n                    __typename\n                  }\n                  __typename\n                }\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          basicInformation {\n            type\n            name\n            localizedName {\n              translatedText\n              __typename\n            }\n            description\n            localizedDescription {\n              translatedText\n              __typename\n            }\n            membersOnly\n            oldRates\n            representativeRoom\n            housingProtected\n            actualRoomsAvailable\n            depositRequired\n            roomsAvailable\n            roomsRequested\n            ratePlan {\n              ratePlanType\n              ratePlanCode\n              marketCode\n              __typename\n            }\n            freeCancellationUntil\n            __typename\n          }\n          roomAttributes {\n            attributes {\n              id\n              description\n              groupID\n              category {\n                code\n                description\n                __typename\n              }\n              accommodationCategory {\n                code\n                description\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          totalPricing {\n            quantity\n            rateAmountsByMode {\n              grandTotal {\n                amount {\n                  origin {\n                    value: amount\n                    valueDecimalPoint\n                    __typename\n                  }\n                  __typename\n                }\n                __typename\n              }\n              subtotalPerQuantity {\n                amount {\n                  origin {\n                    currency\n                    value: amount\n                    valueDecimalPoint\n                    __typename\n                  }\n                  __typename\n                }\n                __typename\n              }\n              totalMandatoryFeesPerQuantity {\n                amount {\n                  origin {\n                    currency\n                    value: amount\n                    valueDecimalPoint\n                    __typename\n                  }\n                  __typename\n                }\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          id\n          __typename\n        }\n        id\n        __typename\n      }\n      __typename\n    }\n    total\n    status {\n      ... on UserInputError {\n        httpStatus\n        messages {\n          user {\n            message\n            field\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      ... on DateRangeTooLongError {\n        httpStatus\n        messages {\n          user {\n            message\n            field\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n"
                    })

                    session.headers.update({
                        'graphql-operation-name': 'PhoenixBookSearchProductsByProperty',
                        'graphql-operation-signature': 'a1079a703a2d21d82c0c65e4337271c3029c69028c6189830f30882170075756',
                    })

                    logger.info(f"Navigating to roomrate API :: {api_url}")

                    response = session.post(url=api_url, data=api_payload)

                    logger.info(f"Final Page Status: {response.status_code}")
                    logger.info(f"Final Page Data: {response.text[:200]}")

                    decodedResponse = response.text
                    if '"Invalid Property Code"' in decodedResponse:
                        logging.error("Property Code is invalid.")
                        message = {
                            "details": "Property Code is invalid."
                        }
                        return self.build_response(success=True, data=message, status_code=response.status_code)

                    data_json = None
                    if response.status_code == 200 and decodedResponse:
                        try:
                            data_json = json.loads(decodedResponse)
                        except Exception as e:
                            message = {
                                "details": f"Response Json not available {e}"
                            }
                            return self.build_response(success=False, data=message, status_code=response.status_code)

                    if response.status_code == 200 and data_json and '"code":"standard"' in decodedResponse and '"code":"redemption"' in decodedResponse:
                        logger.info(f"Response fetched successfully from Roomrate API")
                        return self.build_response(success=True, data=data_json, status_code=response.status_code)
                    elif response.status_code == 200 and data_json and '"code":"standard"' in decodedResponse and '"code":"redemption"' not in decodedResponse:
                        logger.error(f"Hotel is not available at selected date.")
                        message = {
                            "details": "Hotel is not available at selected date."
                        }
                        return self.build_response(success=True, data=message, status_code=response.status_code)
                    else:
                        logger.error(f"Roomrate API failed with status {response.status_code}")
                        message = {
                            "details": f"Roomrate API failed with status {response.status_code}"
                        }
                        return self.build_response(success=False, data=message, status_code=response.status_code)

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


if __name__ =="__main__":
    crawl = ExtractMarriott()
    data = crawl.get_search_data(
        hotel_id="snabp-courtyard-anaheim-buena-park",
        check_in_date="2025-11-04",
        check_out_date="2025-11-08",
        guest_count=1,
    )
    if data:
        print("API data fetched successfully")
    else:
        print("API data could not be fetched with current cookies")