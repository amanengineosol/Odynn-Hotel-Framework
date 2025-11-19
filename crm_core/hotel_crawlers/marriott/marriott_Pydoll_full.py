import json
import logging
import os
import random as rand
import time
import zipfile
from datetime import datetime
from urllib.parse import urlparse, quote
from .proxy_manager import ProxyManager
from .random_user_agent import get_random_sec_ch_headers, USER_AGENT
from pydoll.browser import Chrome
from pydoll.browser.options import ChromiumOptions as Options
import asyncio
from functools import partial
from pydoll.protocol.network.events import NetworkEvent

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
        api_responses = {}
        search_responses = {}

        async def capture_marriott_api(tab, event):
            request_id = event['params']['requestId']
            response = event['params']['response']
            url = response['url']

            # Only capture the Marriott rates API response
            if 'PhoenixBookSearchProductsByProperty' in url and response['status'] == 200:
                try:
                    body = await tab.get_network_response_body(request_id)
                    try:
                        data = json.loads(body)
                        api_responses[url] = data
                        logger.info(f"Marriott API response from: {url}")
                    except json.JSONDecodeError:
                        api_responses[url] = body
                        logger.info(f"Non-JSON response from: {url}")
                        message = {
                            "details": f"Response Json not available"
                        }
                        return self.build_response(success=False, data=message, status_code=response['status'])
                except Exception as e:
                    logger.error(f"Failed to get response: {e}")
                    message = {
                        "details": f"Failed to get response: {e}"
                    }
                    return self.build_response(success=False, data=message, status_code=response['status'])

        async def capture_marriott_search(tab, event):
            request_id = event['params']['requestId']
            response = event['params']['response']
            url = response['url']

            # Only capture the Marriott rates API response
            if 'https://www.marriott.com/default.mi' in url:
                try:
                    body = await tab.get_network_response_body(request_id)
                    search_responses[url] = body
                    logger.info(f"Marriott search response from: {url}")
                except Exception as e:
                    logger.error(f"Failed to get search response: {e}")
                    message = {
                        "details": f"Failed to get search response: {e}"
                    }
                    return self.build_response(success=False, data=message, status_code=response['status'])


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
            ua = _headers["user-agent"]
            # Configure browser options
            options = Options()
            options.start_timeout = 40
            options.headless = False
            # options.add_argument('--headless')
            # options.user_agent = _headers["user-agent"]
            options.add_argument(f"--user-agent={ua}")
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-features=VizDisplayCompositor')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-plugins-discovery')
            options.add_argument('--window-size=1366, 768')
            options.add_argument(f'--load-extension={os.path.abspath(pluginfile)}')
            options.add_argument('--view-port=1366, 768')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-dev-hooks')
            options.add_argument('--disable-logging')
            options.add_argument('--disable-popup-buttons')
            options.add_argument('--disable-popup-content')
            options.add_argument('--disable-popup-menu')
            options.add_argument('--disable-popup-notifications')
            options.add_argument('--disable-popup-polling')
            options.add_argument('--disable-popup-templates')
            options.add_argument('--disable-popup-widgets')
            options.add_argument('--disable-popup-widget-notifications')
            options.add_argument('--disable-popup-layouts')
            options.add_argument('--mute-audio')
            options.add_argument('--enable-javascript')
            options.add_argument('--lang=en-US,en;q=0.9')
            options.add_argument('--disable-renderer-backgrounding')
            options.add_argument('--disable-infobars')
            # options.add_argument('--remote-debugging-port=9222')


            async with Chrome(options=options) as browser:
                tab = await browser.start()
                # === Register network event capture ===
                await tab.enable_network_events()
                await tab.on(NetworkEvent.RESPONSE_RECEIVED, partial(capture_marriott_api, tab))
                await tab.on(NetworkEvent.RESPONSE_RECEIVED, partial(capture_marriott_search, tab))
                # result = await tab.call_method("Runtime.evaluate", expression="navigator.userAgent")
                # user_agent = result["result"]["value"]
                print(ua)

                try:
                    logger.info("Sending Home page request....")

                    await tab.go_to('https://www.marriott.com/default.mi')
                    human_delay(6, 12)

                    # === Access and log the captured API data ===
                    if search_responses:
                        logger.info("Captured Marriott Search responses:")
                        for url, resp in search_responses.items():
                            logger.info(f"\t{resp}")

                    # Wait for "Find Hotels" button
                    logger.info("Waiting for 'Find Hotels' button...")
                    find_hotels_btn = await tab.find(text="Find Hotels")
                    await find_hotels_btn.wait_until(is_visible=True, timeout=120)

                    if not find_hotels_btn:
                        logger.error("Find Hotels button not found!")
                        return False

                    logger.info("Home page request completed successfully.....")

                    # ---- Destination ----
                    dest_input = await tab.query('//input[@placeholder="Search city, hotel, address and more..."]')
                    await dest_input.wait_until(is_visible=True, timeout=120)
                    await dest_input.click()
                    human_delay(1, 3)
                    await dest_input.type_text(hotel_name,interval=0.5)

                    # Select first dropdown suggestion
                    human_delay(1, 1.8)
                    suggest_hotelcheck = await tab.query("//*[@role='option']")
                    await suggest_hotelcheck.wait_until(is_visible=True, timeout=5000)
                    suggest_hotel = await tab.query("//*[@role='option']",find_all=True)
                    if not suggest_hotel:
                        raise Exception("No hotel suggestions found in dropdown!")
                    await suggest_hotel[0].click()
                    human_delay(1.2, 2.5)

                    # Open calendar
                    date_input = await tab.query("//input[@aria-label='date-picker']")
                    await date_input.wait_until(is_visible=True, timeout=120)
                    await date_input.click()
                    human_delay(1, 2)

                    if _headers["sec-ch-ua-platform"] == '"Linux"':
                        check_in_label = await self.linux_format_marriott_date(check_in_date)
                        check_out_label = await self.linux_format_marriott_date(check_out_date)
                        date_range_str = f"{check_in_label} - {check_out_label}"
                    else:
                        check_in_label = await self.windows_format_marriott_date(check_in_date)
                        check_out_label = await self.windows_format_marriott_date(check_out_date)
                        date_range_str = f"{check_in_label} - {check_out_label}"

                    async def go_to_month(tab, target_month_year: str):
                        """
                        target_month_year should be like 'October 2025'.
                        """
                        while True:
                            # Get all currently visible month captions
                            captions = await tab.query(
                                "//*[contains(@class, 'DayPicker-Caption')]//div[@data-scroll-date-marker]",
                                find_all=True)
                            months = [(await c.text).strip() for c in
                                      captions]  # Await .text property if it's a coroutine

                            if target_month_year in months:
                                break  # target month is visible, stop clicking

                            # Re-query the next button in case the DOM has changed
                            next_button = await tab.query("//*[contains(@class, 'DayPicker-NavButton--next')]")
                            if await next_button.is_visible():
                                await next_button.click()
                                await asyncio.sleep(rand.uniform(1, 2))  # Use asyncio.sleep in async functions
                            else:
                                raise Exception(f"Could not find month {target_month_year}")

                    # Format like 'October 2025'
                    human_delay(1, 2)
                    checkin_month_year = datetime.strptime(check_in_date, "%Y-%m-%d").strftime("%B %Y")
                    logger.info(f"Checkin month year: {checkin_month_year}")
                    checkout_month_year = datetime.strptime(check_out_date, "%Y-%m-%d").strftime("%B %Y")
                    logger.info(f"Checkout month year: {checkout_month_year}")
                    logger.info(f"check_in_label: {check_in_label}")
                    logger.info(f"check_out_label: {check_out_label}")

                    # Navigate to check-in month
                    await go_to_month(tab, checkin_month_year)
                    check_in_button = await tab.query(f"//div[contains(@class, 'DayPicker-Day') and @aria-label='{check_in_label}']")
                    await check_in_button.wait_until(is_visible=True,timeout=120)
                    await check_in_button.click()
                    human_delay(6, 12)

                    # Navigate to check-out month
                    await go_to_month(tab, checkout_month_year)
                    check_out_button = await tab.query(f"//div[contains(@class, 'DayPicker-Day') and @aria-label='{check_out_label}']")
                    await check_out_button.wait_until(is_visible=True,timeout=120)
                    await check_out_button.click()
                    human_delay(1.3, 2.6)

                    done_button = await tab.query("//button[@aria-label='Done']")
                    await done_button.wait_until(is_visible=True,timeout=120)
                    await done_button.click()
                    human_delay(1, 2)

                    # # ---- Use Points/Awards ----
                    use_points_label = await tab.query("//label[@for='usepoints-checkbox']")
                    await use_points_label.wait_until(is_visible=True,timeout=120)
                    human_delay(0.5, 1.5)
                    await use_points_label.click()
                    human_delay(6, 12)

                    # Click Find Hotels button
                    find_hotels_button = await tab.query("//button[contains(@class, 'update-search-btn') and contains(text(), 'Find Hotels')]")
                    await find_hotels_button.wait_until(is_visible=True,timeout=120)
                    await find_hotels_button.click()
                    # checkResponse = tab.content()
                    # logger.info(f"Find hotels: {checkResponse}")
                    await asyncio.sleep(10)
                    human_delay(0.5, 1.5)

                    # # === Access and log the captured API data ===
                    # if search_responses:
                    #     logger.info("Captured Marriott Search responses:")
                    #     for url, resp in search_responses.items():
                    #         logger.info(f"\t{resp}")

                    # Click View rates
                    human_delay(2, 6)
                    viewRates_button = await tab.query("//a[contains(@class, 'view-rates-button-container') and @aria-label='View Rates']")
                    await viewRates_button.wait_until(is_visible=True, timeout=24000)
                    await viewRates_button.click()

                    # Wait for the network response to be received and parsed
                    await asyncio.sleep(9)

                    # === Access and log the captured API data ===
                    if api_responses:
                        logger.info("Captured Marriott API responses:")
                        for url, resp in api_responses.items():

                            edges = resp["data"]["searchProductsByProperty"]["edges"]
                            # logger.info(f"\t{edges}")

                            # Check for codes
                            has_standard = any(
                                edge["node"]["availabilityAttributes"]["rateCategory"]["type"]["code"] == "standard"
                                for edge in edges
                            )

                            has_redemption = any(
                                edge["node"]["availabilityAttributes"]["rateCategory"]["type"]["code"] == "redemption"
                                for edge in edges
                            )

                            if '"Invalid Property Code"' in resp:
                                logging.error("Property Code is invalid.")
                                message = {
                                    "details": "Property Code is invalid."
                                }
                                return self.build_response(success=True, data=message, status_code=200)
                            elif has_standard and has_redemption:
                                logger.info(f"Response fetched successfully from Roomrate API")
                                return self.build_response(success=True, data=resp, status_code=200)
                            elif has_standard and not has_redemption:
                                logger.error(f"Hotel is not available at selected date.")
                                message = {
                                    "details": "Hotel is not available at selected date."
                                }
                                return self.build_response(success=True, data=message, status_code=200)
                    else:
                        logger.error(f"Roomrate API failed")
                        message = {
                            "details": f"Roomrate API failed"
                        }
                        return self.build_response(success=False, data=message, status_code=429)

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
            hotel_id="swfhr-inn at bellefield hyde park",
            check_in_date="2026-01-06",
            check_out_date="2026-01-08",
            guest_count=1,
        )
        if data:
            print("API data fetched successfully")
        else:
            print("API data could not be fetched with current cookies")

    asyncio.run(main())