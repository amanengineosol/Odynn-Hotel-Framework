import json
import logging
import os
import random as rand
import time
import zipfile
from datetime import datetime
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
        # while browser_family != "chromium":
        #     browser_family, headers = get_random_sec_ch_headers(USER_AGENT)
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
            # options.add_argument(f'--proxy-server={parsed.scheme}://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port}')
            # options.add_argument('--window-size=1920,1080')
            options.start_timeout = 20
            options.headless = False

            async with Chrome(options=options) as browser:
                tab = await browser.start()
                try:
                    logger.info("Sending Home page request....")

                    await tab.go_to('https://www.hyatt.com/')
                    human_delay(6, 12)

                    logger.info("Home page request completed successfully.....")

                    api_url = (
                        f"https://www.hyatt.com/shop/service/rooms/roomrates/{hotel_id}"
                        f"?spiritCode={hotel_id}&rooms=1&adults={guest_count}"
                        f"&location={encoded_hotel_name}"
                        f"&checkinDate={check_in_date}&checkoutDate={check_out_date}"
                        f"&kids=0&rate=Standard&suiteUpgrade=true"
                    )

                    ref_url = f"https://www.hyatt.com/shop/rooms/{hotel_id}?location={encoded_hotel_name}&checkinDate={check_in_date}&checkoutDate={check_out_date}&rooms=1&adults={guest_count}&kids=0&rate=Standard&rateFilter=woh"

                headers = [
                        # {"name": "content-length", "value": "5190"},
                        {"name": "application-name", "value": "book"},
                        {"name": "x-request-id", "value": ""},
                        # {"name": "sec-ch-ua-platform", "value": "\"Windows\""},
                        {"name": "graphql-operation-name", "value": "PhoenixBookSearchProductsByProperty"},
                        # {"name": "x-dtpc", "value": "10$97512768_715h7vUTFRMEHMMAEFPKKDKVPROITOLAKMMHRS-0e0"},
                        # {"name": "sec-ch-ua",
                        #  "value": "\"Chromium\";v=\"140\", \"Not=A?Brand\";v=\"24\", \"Google Chrome\";v=\"140\""},
                        # {"name": "sec-ch-ua-mobile", "value": "?0"},
                        {"name": "graphql-force-safelisting", "value": "true"},
                        {"name": "accept", "value": "*/*"},
                        {"name": "apollographql-client-version", "value": "1"},
                        {"name": "content-type", "value": "application/json"},
                        {"name": "apollographql-client-name", "value": "phoenix_book"},
                        {"name": "graphql-require-safelisting", "value": "true"},
                        {"name": "accept-language", "value": "en-US"},
                        {"name": "graphql-operation-signature",
                         "value": "a1079a703a2d21d82c0c65e4337271c3029c69028c6189830f30882170075756"},
                        # {"name": "user-agent",
                        #  "value": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"},
                        {"name": "origin", "value": "https://www.marriott.com"},
                        # {"name": "sec-fetch-site", "value": "same-origin"},
                        # {"name": "sec-fetch-mode", "value": "cors"},
                        # {"name": "sec-fetch-dest", "value": "empty"},
                        {"name": "referer", "value": "https://www.marriott.com/reservation/rateListMenu.mi"},
                        # {"name": "accept-encoding", "value": "gzip, deflate, br, zstd"},
                        # {"name": "priority", "value": "u=1, i"},
                    ]

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
                                    "productRoomType": ["ALL"],
                                    "productStatusType": ["AVAILABLE"],
                                    "rateRequestTypes": [
                                        {"value": "", "type": "STANDARD"},
                                        {"value": "", "type": "PREPAY"},
                                        {"value": "", "type": "PACKAGES"},
                                        {"value": "MRM", "type": "CLUSTER"},
                                        {"value": "", "type": "REDEMPTION"},
                                    ],
                                    "isErsProperty": False,
                                },
                                "propertyId": "SNABP",
                            },
                            "offset": 0,
                            "limit": 150,
                        },
                        "query": """query PhoenixBookSearchProductsByProperty($search: ProductByPropertySearchInput, $offset: Int, $limit: Int) {
                          searchProductsByProperty(search: $search, offset: $offset, limit: $limit) {
                            edges {
                              node {
                                id
                                __typename
                              }
                            }
                          }
                        }"""
                    }

                    response = await tab.request.post(api_url, json=api_payload, headers=headers)

                    logger.info(
                        f"Navigating to roomrate API with headers:: {api_url}")

                    # response = await tab.request.post(api_url, json={api_payload: True}, headers=headers)

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
        crawl = ExtractHyatt()
        data = await crawl.get_search_data(
            hotel_id="snabp-courtyard-anaheim-buena-park",
            check_in_date="2025-11-04",
            check_out_date="2025-11-08",
            guest_count=1,
        )
        if data:
            print("API data fetched successfully")
        else:
            print("API data could not be fetched with current cookies")

    asyncio.run(main())