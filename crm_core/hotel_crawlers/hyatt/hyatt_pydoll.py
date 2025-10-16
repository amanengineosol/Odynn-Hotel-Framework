import json
import logging
import os
import random as rand
import zipfile
from datetime import datetime
from urllib.parse import urlparse, quote
from .proxy_manager import ProxyManager
from .random_user_agent import get_random_sec_ch_headers, USER_AGENT
from pydoll.browser import Chrome
from pydoll.browser.options import ChromiumOptions as Options
import asyncio
from pydoll.constants import Key
import json
from pydoll.protocol.network.events import NetworkEvent
from functools import partial



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


async def human_delay(a, b):
    """Async version of human delay"""
    await asyncio.sleep(rand.uniform(a, b))


class ExtractHyatt:

    def __init__(self):
        self._proxy_fetcher = ProxyManager()

    def build_response(self, success: bool, data: any, status_code: int):
        return {
            "success": success,
            "data": data,
            "status_code": status_code
        }

    # ---------------- Add inside ExtractHyatt ----------------

    async def get_search_data(self, hotel_id, check_in_date, check_out_date, guest_count, max_retries=3):
        api_responses = {}

        async def capture_hyatt_api(new_tab, event):
            try:
                params = event.get("params", {})
                response = params.get("response", {})
                request_id = params.get("requestId")
                url = response.get("url", "")
                # Look for Hyatt room rate API calls
                if "roomrates" in url:
                    logger.info(f" Captured Hyatt rates API: {url}")

                    # Fetch the response body
                    body_bytes = await new_tab.get_network_response_body(request_id)
                    body_text = (
                        body_bytes.decode("utf-8", errors="ignore")
                        if isinstance(body_bytes, (bytes, bytearray))
                        else body_bytes
                    )
                    # Try parsing JSON
                    try:
                        data = json.loads(body_text)
                        api_responses[url] = data
                        return self.build_response(success=True, data=data, status_code=200)

                    except json.JSONDecodeError:
                        logger.warning(f"Response is not JSON — storing as raw text")
                        api_responses[url] = body_text


            except Exception as e:
                logger.error(f"Error in network callback: {e}")

        logger.info("Getting proxy IP for current session")
        _proxy_url = self._proxy_fetcher.fetch_proxy()
        if not _proxy_url:
            message = "Proxy url not retrieved from the server"
            return self.build_response(success=False, data=message, status_code=101)

        parsed = urlparse(_proxy_url)
        if not (parsed.username and parsed.password):
            message = "Proxy authentication credentials missing"
            return self.build_response(success=False, data=message, status_code=101)

        logger.info("Proxy url dict created for request")
        logger.info("Setting up crawler to extract data")

        # browser_family, headers = get_random_sec_ch_headers(USER_AGENT)
        # _headers = headers

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

        # Create Chrome extension for proxy authentication
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

        for attempt in range(1, max_retries - 1):
            try:
                options = Options()
                # options.binary_location = "/usr/bin/chromium"
                # browser_family, headers = get_random_sec_ch_headers(USER_AGENT)
                # options.add_argument(f'--user-agent={headers["user-agent"]}')
                # options.add_argument("--no-sandbox")
                # options.add_argument("--disable-dev-shm-usage")
                # options.add_argument("--disable-gpu")
                # options.add_argument("--disable-web-security")
                # options.add_argument("--disable-blink-features=AutomationControlled")
                options.args = [
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-web-security",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-features=AutomationControlled",
                    "--disable-extensions",
                    "--disable-software-rasterizer",
                    "--disable-dev-tools",
                    "--no-zygote",
                    "--single-process",
                ]
                # Also explicitly disable automation flags if possible
                try:
                    options.add_argument = options.args.append  # If PyDoll doesn't expose add_argument()
                except:
                    pass

                options.binary_location = "/usr/bin/chromium"  # or /usr/bin/google-chrome depending on install

                options.add_argument(f'--proxy-auth-plugin={pluginfile}')
                options.user_data_dir = os.path.abspath("./chrome_profile")

                from pydoll.browser.managers.temp_dir_manager import TempDirectoryManager
                TempDirectoryManager.AUTO_CLEANUP = False  # disable auto cleanup

                # options.user_data_dir = os.path.abspath("./chrome_profile")  # fixed folder

                async with Chrome(options=options) as browser:
                    tab = await browser.start()

                    try:
                        await tab.execute_script("""Object.defineProperty(navigator, 'webdriver', {get: () => undefined});""")
                        await tab.execute_script("""
                            Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4]});
                            Object.defineProperty(navigator, 'languages', {get: () => ['en-US','en']});
                        """)
                        await tab.execute_script("""
                        window.chrome = {runtime: {}};
                        """)

                        logger.info("Sending Home page request....")
                        await tab.go_to('https://www.hyatt.com/')
                        await human_delay(6, 12)

                        logger.info("Home page loaded successfully.....")

                        # ---- Mouse movement to mimic human behavior ----
                        logger.info("Performing mouse simulation.....")
                        await human_delay(2, 5)

                        # Scroll simulation
                        await tab.execute_script("window.scrollBy(0, 100)")
                        await human_delay(1, 2)
                        await tab.execute_script("window.scrollBy(0, -100)")
                        await human_delay(1, 2)

                        logger.info("Mouse movement completed.....")

                        # Handle cookie banner (OneTrust)
                        try:
                            cookie_btn = await tab.find(id="onetrust-accept-btn-handler", timeout=5, raise_exc=False)
                            if cookie_btn:
                                await cookie_btn.click()
                                logger.info("Cookie banner accepted.")
                        except Exception:
                            logger.info("No cookie banner found or already accepted.")

                        await tab.execute_script(f"""
                        const el = document.querySelector('#search-term');
                        const hotelName = `{hotel_name}`;
                        if (el) {{
                            el.scrollIntoView({{behavior: 'instant', block: 'center'}});
                            el.focus();

                            let i = 0;

                            function typeChar() {{
                                if (i < hotelName.length) {{
                                    const char = hotelName[i];
                                    el.value += char;
                                    el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                    i++;
                                    setTimeout(typeChar, 150); // 150ms delay between keystrokes
                                }} else {{
                                    // After typing is done, simulate arrow down + enter
                                    setTimeout(() => {{
                                        el.dispatchEvent(new KeyboardEvent('keydown', {{ key: 'ArrowDown', bubbles: true }}));
                                        el.dispatchEvent(new KeyboardEvent('keydown', {{ key: 'Enter', bubbles: true }}));
                                    }}, 500);
                                }}
                            }}

                            typeChar();
                        }}
                        """)

                        # ===== SET DATES VIA COMPONENT ATTRIBUTES =====
                        logger.info(f"Setting dates on be-datepicker component: {check_in_date} to {check_out_date}")
                        await human_delay(2, 3)

                        # Set dates by updating the component's attributes
                        await tab.execute_script(f"""
                            const datepicker = document.querySelector('be-datepicker');

                            // Update component attributes - this triggers the component's internal logic
                            datepicker.setAttribute('initial-start-date', '{check_in_date}');
                            datepicker.setAttribute('initial-end-date', '{check_out_date}');

                            // Also set the shadow DOM inputs for good measure
                            if (datepicker.shadowRoot) {{
                                const shadow = datepicker.shadowRoot;
                                const checkinInput = shadow.querySelector('input[name="checkin-date"]');
                                const checkoutInput = shadow.querySelector('input[name="checkout-date"]');

                                if (checkinInput) {{
                                    checkinInput.value = '{check_in_date}';
                                    checkinInput.dispatchEvent(new Event('change', {{bubbles: true, composed: true}}));
                                }}

                                if (checkoutInput) {{
                                    checkoutInput.value = '{check_out_date}';
                                    checkoutInput.dispatchEvent(new Event('change', {{bubbles: true, composed: true}}));
                                }}
                            }}

                            // Trigger component update event
                            datepicker.dispatchEvent(new Event('change', {{bubbles: true}}));
                            datepicker.dispatchEvent(new CustomEvent('date-changed', {{
                                detail: {{startDate: '{check_in_date}', endDate: '{check_out_date}'}},
                                bubbles: true
                            }}));
                        """)

                        logger.info("Dates set on component")
                        await human_delay(2, 3)

                        # Find and click the "Use Points" checkbox
                        # ===== CHECK USE POINTS CHECKBOX =====
                        logger.info("Checking Use Points checkbox...")

                        await tab.execute_script("""
                            const checkbox = document.querySelector('be-checkbox[name="use-points"]');
                            if (checkbox) {
                                checkbox.checked = true;
                                checkbox.dispatchEvent(new Event('change', { bubbles: true }));
                            }
                        """)

                        logger.info("Use Points checkbox checked")
                        await human_delay(2, 3)

                        # Wait for and click the search button using CSS selector
                        # ===== CLICK FIND HOTELS BUTTON =====
                        logger.info("Clicking Find Hotels button...")
                        # await tab.execute_script("""
                        #     const button = document.querySelector('be-button[label="Find Hotels"] button');
                        #     if (button) {
                        #         button.click();
                        #     }
                        # """)

                        await tab.execute_script(
                            """
                                const button = document.querySelector('be-button[label="Find Hotels"] button');
                                if (button) {
                                    button.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
                                }
                            """
                        )

                        logger.info("Find Hotels button clicked")
                        # Scroll to bottom to trigger lazy load
                        await tab.execute_script("""
                            window.scrollTo(0, document.body.scrollHeight);
                        """)
                        await asyncio.sleep(2)

                        logger.info("Waiting for search results page to load...")
                        for attempt in range(30):  # retry every 1s up to 30s
                            button_exists = await tab.execute_script("""
                                return document.querySelectorAll('be-button[href*="shop/rooms"] a span.be-button-label').length > 0;
                            """)
                            print("View Rates@@@@@@@@@@@@@@@@@@@@@@@@")
                            print(button_exists)
                            if button_exists['result']['result']['value']:
                                logger.info(" 'View Rates' button found.")
                                break
                            await asyncio.sleep(1)
                        else:
                            logger.error(" 'View Rates' button not found after 30 seconds.")
                            return self.build_response(
                                success=False,
                                data={"error": "'View Rates' button not found after waiting."},
                                status_code=102
                            )
                        button_info = await tab.execute_script("""
                            const btn = document.querySelector('be-button[href*="shop/rooms"], a[href*="shop/rooms"]');
                            if (!btn) return null;

                            const textEl = btn.querySelector('.be-button-label') || btn;
                            return {
                                text: textEl.textContent.trim(),
                                href: btn.getAttribute('href') || btn.href || null
                            };
                        """)
                        print("button_info*********************")
                        print(button_info)

                        if not button_info:
                            logger.error(" Could not extract first 'View Rates' button details.")
                            return self.build_response(
                                success=False,
                                data={"error": "No valid 'View Rates' button found."},
                                status_code=103
                            )

                        logger.info(f"Found 'View Rates' button: {button_info}")

                        # ===== OPEN 'VIEW RATES' IN NEW TAB =====
                        # Get the href of the first "View Rates" button
                        # view_rates_url = await tab.execute_script("""
                        #     const btn = document.querySelector('be-button a.be-button-shop');
                        #     return btn ? btn.href : null;
                        # """)

                        # ===== WAIT FOR SEARCH RESULTS PAGE AND GET VIEW RATES URL =====
                        logger.info("Waiting for 'View Rates' buttons to appear (shadow DOM aware)...")
                        # Inject the helper function into the page
                        await tab.execute_script("""
                        function waitForShadowSelector(rootSelector, shadowSelector, maxRetries = 30) {
                            return new Promise((resolve, reject) => {
                                let retries = 0;
                                const interval = setInterval(() => {
                                    const root = document.querySelector(rootSelector);
                                    if (root && root.shadowRoot) {
                                        const el = root.shadowRoot.querySelector(shadowSelector);
                                        if (el) {
                                            clearInterval(interval);
                                            resolve(el);
                                        }
                                    }
                                    retries++;
                                    if (retries > maxRetries) {
                                        clearInterval(interval);
                                        reject('Element not found');
                                    }
                                }, 1000);
                            });
                        }
                        """)

                        view_rates_url = None
                        for _ in range(30):  # Wait up to 30s
                            view_rates_url = await tab.execute_script("""
                                const btn = document.querySelector('.be-button[href*="shop/rooms"], a[href*="shop/rooms"]');
                                return btn ? btn.getAttribute('href') : null;
                            """)
                            if view_rates_url['result']['result']['value']:
                                break
                            await asyncio.sleep(1)

                        if not view_rates_url['result']['result']['value']:
                            logger.error("View Rates URL could not be retrieved")
                        else:
                            logger.info(f"View Rates URL found: {view_rates_url}")


                        # ===== OPEN 'VIEW RATES' IN NEW TAB =====
                        new_tab = await browser.new_tab()
                        await asyncio.sleep(1)
                        await new_tab.enable_network_events()
                        await new_tab.on(NetworkEvent.RESPONSE_RECEIVED, partial(capture_hyatt_api, new_tab))
                        logger.info("Network listener attached")
                        await new_tab.go_to(view_rates_url['result']['result']['value'])
                        await asyncio.sleep(12)




                    except Exception as ex:
                        logger.exception(f"Exception occurred during scraping: {ex}")
                        if attempt < max_retries:
                            logger.info(f"Retrying... Attempt {attempt + 1}/{max_retries}")
                            await asyncio.sleep(2)
                            continue
                        else:
                            message = {"details": f"Exception occurred during scraping: {ex}"}
                            return self.build_response(success=False, data=message, status_code=103)

            except Exception as ex:
                logger.exception(f"Critical Error: {ex}")
                if attempt < max_retries:
                    logger.info(f"Retrying... Attempt {attempt + 1}/{max_retries}")
                    await asyncio.sleep(2)
                    continue
                else:
                    message = {"details": f"Critical Error: {ex}"}
                    return self.build_response(success=False, data=message, status_code=100)

if __name__ == "__main__":
    async def main():
        crawl = ExtractHyatt()
        data = await crawl.get_search_data(
            hotel_id="yulzm-Hyatt Place Montreal - Downtown",
            check_in_date="2025-11-04",
            check_out_date="2025-11-08",
            guest_count=1,
        )
        if data:
            print("API data fetched successfully", data)
        else:
            print("API data could not be fetched with current cookies")


    asyncio.run(main())
