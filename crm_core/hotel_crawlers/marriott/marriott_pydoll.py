import json
import logging
import os
import random as rand
import time
import zipfile
from datetime import datetime
from enum import verify

from playwright.sync_api import sync_playwright , TimeoutError as PlaywrightTimeoutError
from urllib.parse import urlparse, quote
from .proxy_manager import ProxyManager
from .random_user_agent import get_random_sec_ch_headers, USER_AGENT
import requests
from pydoll.browser import Chrome
from pydoll.browser.options import ChromiumOptions as Options
import asyncio

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

    async def linux_format_marriott_date(self, dt_str):
        dt = datetime.strptime(dt_str, "%Y-%m-%d")
        # Format like: Tue, Nov 4
        return dt.strftime("%a %b %d %Y")   #linux

    async def windows_format_marriott_date(self, dt_str):
        dt = datetime.strptime(dt_str, "%Y-%m-%d")
        # Format like: Tue, Nov 4
        return dt.strftime("%a %b %d %Y")   # On Windows use

    def build_response(self, success: bool, data: any, status_code: int):
        return {
            "success": success,
            "data": data,
            "status_code": status_code
        }

    async def get_search_data(self, hotel_id, check_in_date, check_out_date, guest_count, max_retries=3):
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

        # Create a temporary Chrome extension for proxy auth
        manifest_json = {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Proxy Auth Extension",
            "permissions": ["proxy", "tabs", "unlimitedStorage", "storage", "<all_urls>", "webRequest",
                            "webRequestBlocking"],
            "background": {
                "scripts": ["background.js"]
            }
        }

        background_js = f"""
        chrome.proxy.settings.set({{value: {{
            mode: "fixed_servers",
            rules: {{
              singleProxy: {{
                scheme: "{parsed.scheme}",
                host: "{parsed.hostname}",
                port: parseInt({parsed.port})
              }},
              bypassList: ["localhost"]
            }}
        }}, scope: "regular"}}, function() {{}});

        chrome.webRequest.onAuthRequired.addListener(
            function(details, callback) {{
                callback({{authCredentials: {{username: "{parsed.username}", password: "{parsed.password}"}}}});
            }},
            {{urls: ["<all_urls>"]}},
            ['blocking']
        );
        """

        # Save to a zip file (Chrome extension)
        pluginfile = 'proxy_auth_plugin.zip'
        with zipfile.ZipFile(pluginfile, 'w') as zp:
            zp.writestr("manifest.json", json.dumps(manifest_json))
            zp.writestr("background.js", background_js)

        try:
            # Configure browser options
            options = Options()
            options.add_argument(f'--load-extension={os.path.abspath(pluginfile)}')
            options.add_argument('--window-size=1920,1080')
            # options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.start_timeout = 20
            options.headless = False
            # options.add_argument('--headless=new')
            options.add_argument('--start-maximized')
            options.add_argument('--disable-notifications')
            options.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"

            async with Chrome(options=options) as browser:
                tab = await browser.start()
                try:
                    logger.info("Sending Home page request....")

                    await tab.go_to('https://www.marriott.com/default.mi')
                    human_delay(6, 12)

                    # Wait for "Find Hotels" button
                    logger.info("Waiting for 'Find Hotels' button...")
                    find_hotels_btn = await tab.find(text="Find Hotels")
                    await find_hotels_btn.wait_until(is_visible=True, timeout=120)

                    if not find_hotels_btn:
                        logger.error("Find Hotels button not found!")
                        return False

                    logger.info("Home page request completed successfully.....")

                    all_cookies = await browser.get_cookies()

                    logger.info(f"Cookies: {all_cookies}")


                    api_url = "https://www.marriott.com/mi/query/PhoenixBookSearchProductsByProperty"
                    # api_payload = json.dumps('{"operationName":"PhoenixBookSearchProductsByProperty","variables":{"search":{"options":{"startDate":"2025-11-04","endDate":"2025-11-08","quantity":1,"numberInParty":1,"childAges":[],"productRoomType":["ALL"],"productStatusType":["AVAILABLE"],"rateRequestTypes":[{"value":"","type":"STANDARD"},{"value":"","type":"PREPAY"},{"value":"","type":"PACKAGES"},{"value":"MRM","type":"CLUSTER"},{"value":"","type":"REDEMPTION"}],"isErsProperty":false},"propertyId":"SNABP"},"offset":0,"limit":150},"query":"query PhoenixBookSearchProductsByProperty($search: ProductByPropertySearchInput, $offset: Int, $limit: Int) {\n  searchProductsByProperty(search: $search, offset: $offset, limit: $limit) {\n    edges {\n      node {\n        ... on HotelRoom {\n          availabilityAttributes {\n            rateCategory {\n              type {\n                code\n                __typename\n              }\n              value\n              __typename\n            }\n            isNearSellout\n            __typename\n          }\n          rates {\n            name\n            description\n            rateAmounts {\n              amount {\n                origin {\n                  amount\n                  currency\n                  valueDecimalPoint\n                  __typename\n                }\n                __typename\n              }\n              points\n              pointsSaved\n              pointsToPurchase\n              __typename\n            }\n            localizedDescription {\n              translatedText\n              sourceText\n              __typename\n            }\n            localizedName {\n              translatedText\n              sourceText\n              __typename\n            }\n            rateAmountsByMode {\n              averageNightlyRatePerUnit {\n                amount {\n                  origin {\n                    amount\n                    currency\n                    valueDecimalPoint\n                    __typename\n                  }\n                  __typename\n                }\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          basicInformation {\n            type\n            name\n            localizedName {\n              translatedText\n              __typename\n            }\n            description\n            localizedDescription {\n              translatedText\n              __typename\n            }\n            membersOnly\n            oldRates\n            representativeRoom\n            housingProtected\n            actualRoomsAvailable\n            depositRequired\n            roomsAvailable\n            roomsRequested\n            ratePlan {\n              ratePlanType\n              ratePlanCode\n              marketCode\n              __typename\n            }\n            freeCancellationUntil\n            __typename\n          }\n          roomAttributes {\n            attributes {\n              id\n              description\n              groupID\n              category {\n                code\n                description\n                __typename\n              }\n              accommodationCategory {\n                code\n                description\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          totalPricing {\n            quantity\n            rateAmountsByMode {\n              grandTotal {\n                amount {\n                  origin {\n                    value: amount\n                    valueDecimalPoint\n                    __typename\n                  }\n                  __typename\n                }\n                __typename\n              }\n              subtotalPerQuantity {\n                amount {\n                  origin {\n                    currency\n                    value: amount\n                    valueDecimalPoint\n                    __typename\n                  }\n                  __typename\n                }\n                __typename\n              }\n              totalMandatoryFeesPerQuantity {\n                amount {\n                  origin {\n                    currency\n                    value: amount\n                    valueDecimalPoint\n                    __typename\n                  }\n                  __typename\n                }\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          id\n          __typename\n        }\n        id\n        __typename\n      }\n      __typename\n    }\n    total\n    status {\n      ... on UserInputError {\n        httpStatus\n        messages {\n          user {\n            message\n            field\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      ... on DateRangeTooLongError {\n        httpStatus\n        messages {\n          user {\n            message\n            field\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n"}')
                    logger.info(f"Navigating to roomrate API with headers:: {api_url}")
                    # headers.update({"name": "application-name", "value": "book"},
                    #     {"name": "x-request-id", "value": ""},
                    #     # {"name": "sec-ch-ua-platform", "value": "\"Windows\""},
                    #     {"name": "graphql-operation-name", "value": "PhoenixBookSearchProductsByProperty"},
                    #     # {"name": "x-dtpc", "value": "10$97512768_715h7vUTFRMEHMMAEFPKKDKVPROITOLAKMMHRS-0e0"},
                    #     # {"name": "sec-ch-ua",
                    #     #  "value": "\"Chromium\";v=\"140\", \"Not=A?Brand\";v=\"24\", \"Google Chrome\";v=\"140\""},
                    #     # {"name": "sec-ch-ua-mobile", "value": "?0"},
                    #     {"name": "graphql-force-safelisting", "value": "true"},
                    #     {"name": "accept", "value": "*/*"},
                    #     {"name": "apollographql-client-version", "value": "1"},
                    #     {"name": "content-type", "value": "application/json"},
                    #     {"name": "apollographql-client-name", "value": "phoenix_book"},
                    #     {"name": "graphql-require-safelisting", "value": "true"},
                    #     {"name": "accept-language", "value": "en-US"},
                    #     {"name": "graphql-operation-signature",
                    #      "value": "a1079a703a2d21d82c0c65e4337271c3029c69028c6189830f30882170075756"},
                    #     {"name": "user-agent",
                    #      "value": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"},
                    #     {"name": "origin", "value": "https://www.marriott.com"},
                    #     # {"name": "sec-fetch-site", "value": "same-origin"},
                    #     # {"name": "sec-fetch-mode", "value": "cors"},
                    #     # {"name": "sec-fetch-dest", "value": "empty"},
                    #     {"name": "referer", "value": "https://www.marriott.com/reservation/rateListMenu.mi"},
                    #     # {"name": "accept-encoding", "value": "gzip, deflate, br, zstd"},
                    #     # {"name": "priority", "value": "u=1, i"},
                    # )

                    # headers = [
                    #     # {"name": "content-length", "value": "5190"},
                    #     {"name": "application-name", "value": "book"},
                    #     {"name": "x-request-id", "value": ""},
                    #     # {"name": "sec-ch-ua-platform", "value": "\"Windows\""},
                    #     {"name": "graphql-operation-name", "value": "PhoenixBookSearchProductsByProperty"},
                    #     # {"name": "x-dtpc", "value": "10$97512768_715h7vUTFRMEHMMAEFPKKDKVPROITOLAKMMHRS-0e0"},
                    #     # {"name": "sec-ch-ua",
                    #     #  "value": "\"Chromium\";v=\"140\", \"Not=A?Brand\";v=\"24\", \"Google Chrome\";v=\"140\""},
                    #     # {"name": "sec-ch-ua-mobile", "value": "?0"},
                    #     {"name": "graphql-force-safelisting", "value": "true"},
                    #     {"name": "accept", "value": "*/*"},
                    #     {"name": "apollographql-client-version", "value": "1"},
                    #     {"name": "content-type", "value": "application/json"},
                    #     {"name": "apollographql-client-name", "value": "phoenix_book"},
                    #     {"name": "graphql-require-safelisting", "value": "true"},
                    #     {"name": "accept-language", "value": "en-US"},
                    #     {"name": "graphql-operation-signature",
                    #      "value": "a1079a703a2d21d82c0c65e4337271c3029c69028c6189830f30882170075756"},
                    #     {"name": "user-agent",
                    #      "value": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"},
                    #     {"name": "origin", "value": "https://www.marriott.com"},
                    #     # {"name": "sec-fetch-site", "value": "same-origin"},
                    #     # {"name": "sec-fetch-mode", "value": "cors"},
                    #     # {"name": "sec-fetch-dest", "value": "empty"},
                    #     {"name": "referer", "value": "https://www.marriott.com/reservation/rateListMenu.mi"},
                    #     # {"name": "accept-encoding", "value": "gzip, deflate, br, zstd"},
                    #     # {"name": "priority", "value": "u=1, i"},
                    # ]

                    # api_payload = {
                    #     "operationName": "PhoenixBookSearchProductsByProperty",
                    #     "variables": {
                    #         "search": {
                    #             "options": {
                    #                 "startDate": "2025-11-04",
                    #                 "endDate": "2025-11-08",
                    #                 "quantity": 1,
                    #                 "numberInParty": 1,
                    #                 "childAges": [],
                    #                 "productRoomType": ["ALL"],
                    #                 "productStatusType": ["AVAILABLE"],
                    #                 "rateRequestTypes": [
                    #                     {"value": "", "type": "STANDARD"},
                    #                     {"value": "", "type": "PREPAY"},
                    #                     {"value": "", "type": "PACKAGES"},
                    #                     {"value": "MRM", "type": "CLUSTER"},
                    #                     {"value": "", "type": "REDEMPTION"},
                    #                 ],
                    #                 "isErsProperty": False,
                    #             },
                    #             "propertyId": "SNABP",
                    #         },
                    #         "offset": 0,
                    #         "limit": 150,
                    #     },
                    #     "query": """query PhoenixBookSearchProductsByProperty($search: ProductByPropertySearchInput, $offset: Int, $limit: Int) {
                    #                                   searchProductsByProperty(search: $search, offset: $offset, limit: $limit) {
                    #                                     edges {
                    #                                       node {
                    #                                         id
                    #                                         __typename
                    #                                       }
                    #                                     }
                    #                                   }
                    #                                 }"""
                    # }

                    ftp_value = 'false'

                    api_payload = {
    "operationName": "PhoenixBookSearchProductsByProperty",
    "variables": {
        "search": {
            "options": {
                "startDate": "2025-11-04",
                "endDate": "2025-11-08",
                "quantity": 1,
                "numberInParty": 1,
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
                "isErsProperty": ftp_value
            },
            "propertyId": "SWFHR"
        },
        "offset": 0,
        "limit": 150
    },
    "query": "query PhoenixBookSearchProductsByProperty($search: ProductByPropertySearchInput, $offset: Int, $limit: Int) {\n  searchProductsByProperty(search: $search, offset: $offset, limit: $limit) {\n    edges {\n      node {\n        ... on HotelRoom {\n          availabilityAttributes {\n            rateCategory {\n              type {\n                code\n                __typename\n              }\n              value\n              __typename\n            }\n            isNearSellout\n            __typename\n          }\n          rates {\n            name\n            description\n            rateAmounts {\n              amount {\n                origin {\n                  amount\n                  currency\n                  valueDecimalPoint\n                  __typename\n                }\n                __typename\n              }\n              points\n              pointsSaved\n              pointsToPurchase\n              __typename\n            }\n            localizedDescription {\n              translatedText\n              sourceText\n              __typename\n            }\n            localizedName {\n              translatedText\n              sourceText\n              __typename\n            }\n            rateAmountsByMode {\n              averageNightlyRatePerUnit {\n                amount {\n                  origin {\n                    amount\n                    currency\n                    valueDecimalPoint\n                    __typename\n                  }\n                  __typename\n                }\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          basicInformation {\n            type\n            name\n            localizedName {\n              translatedText\n              __typename\n            }\n            description\n            localizedDescription {\n              translatedText\n              __typename\n            }\n            membersOnly\n            oldRates\n            representativeRoom\n            housingProtected\n            actualRoomsAvailable\n            depositRequired\n            roomsAvailable\n            roomsRequested\n            ratePlan {\n              ratePlanType\n              ratePlanCode\n              marketCode\n              __typename\n            }\n            freeCancellationUntil\n            __typename\n          }\n          roomAttributes {\n            attributes {\n              id\n              description\n              groupID\n              category {\n                code\n                description\n                __typename\n              }\n              accommodationCategory {\n                code\n                description\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          totalPricing {\n            quantity\n            rateAmountsByMode {\n              grandTotal {\n                amount {\n                  origin {\n                    value: amount\n                    valueDecimalPoint\n                    __typename\n                  }\n                  __typename\n                }\n                __typename\n              }\n              subtotalPerQuantity {\n                amount {\n                  origin {\n                    currency\n                    value: amount\n                    valueDecimalPoint\n                    __typename\n                  }\n                  __typename\n                }\n                __typename\n              }\n              totalMandatoryFeesPerQuantity {\n                amount {\n                  origin {\n                    currency\n                    value: amount\n                    valueDecimalPoint\n                    __typename\n                  }\n                  __typename\n                }\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          id\n          __typename\n        }\n        id\n        __typename\n      }\n      __typename\n    }\n    total\n    status {\n      ... on UserInputError {\n        httpStatus\n        messages {\n          user {\n            message\n            field\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      ... on DateRangeTooLongError {\n        httpStatus\n        messages {\n          user {\n            message\n            field\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n"
}
                    response = await tab.request.post(api_url, data=api_payload)

                    logger.info(f"Final Page Status: {response.status_code}")
                    logger.info(f"Final Page Data: {response.text[:200]}")
                    logger.info(f"Final Page Data: {response.request_headers}")

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
                    await tab.close()
                    await browser.stop()


        except Exception as ex:
            logger.exception(f"Critical Error: {ex}")
            message = {
                "details": f"Critical Error: {ex}"
            }
            return self.build_response(success=False, data=message, status_code=100)


if __name__ == "__main__":
    async def main():
        crawl = ExtractMarriott()
        data = await crawl.get_search_data(
            hotel_id="swfhr-swfhr inn at bellefield hyde park",
            check_in_date="2025-11-04",
            check_out_date="2025-11-08",
            guest_count=1,
        )
        if data:
            print("API data fetched successfully")
        else:
            print("API data could not be fetched with current cookies")

    asyncio.run(main())