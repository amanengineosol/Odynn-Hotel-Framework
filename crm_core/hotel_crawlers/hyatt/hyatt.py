import asyncio
import json
import logging
import random as rand
from datetime import datetime
from urllib.parse import urlparse, quote

from seleniumbase import SB
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
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


async def human_delay(a, b):
    await asyncio.sleep(rand.uniform(a, b))


class ExtractHyatt:

    def __init__(self):
        self._proxy_fetcher = ProxyManager()
        browser_family, headers = get_random_sec_ch_headers(USER_AGENT)
        self._headers = headers

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
            with SB(
                uc=True,
                undetectable=True,
                test=True,

                # locale / privacy
                locale="en",
                do_not_track=True,
                # incognito=True,

                # proxy
                proxy=_proxy_url,
                proxy_bypass_list="*",

                # fingerprint / stealth
                agent=self._headers['user-agent'],
                ad_block=True,
                disable_csp=True,

                # # browser stability
                # no_sandbox=True,
                # disable_gpu=True,
                # disable_web_security=True,

                # extra chrome args
                chromium_arg=[
                    "--disable-infobars",
                    "--no_sandbox",
                    "--disable_gpu",
                    "--disable_web_security"
                ],

                # timing
                timeout_multiplier=2.0,
                slow=False,
                # verify_delay=0.5,

                headless=True,
            ) as sb:
                self.
                sb.set_window_size(1280 + rand.randint(-100, 100),
                                   720 + rand.randint(-50, 50))
                sb.sleep(0.2)
                logger.info("Browser launched successfully.")

                # -------------------------------------------------------
                # Step 1: Go to homepage
                # -------------------------------------------------------
                for attempt in range(1, max_retries + 1):
                    # 1. Navigate and setup
                    url = "https://www.hyatt.com/loyalty/en-US"
                    logger.info(f"Navigating to base URL: {url}")
                    try:
                        self.sb.activate_cdp_mode(url)
                        self.sb.sleep(3.5)
                    except WebDriverException as e:
                        logger.critical(f"Failed to navigate or activate CDP mode. Check network/proxy. Error: {e}")
                        return self.build_response(success=False, data=None, status_code=503,
                                                   error_message="Navigation failed. Check browser setup or network.")

                    # 2. Handle popups and cookies
                    self.sb.click_if_visible('button[aria-label="Close"]', timeout=3)
                    self.sb.click_if_visible("#onetrust-reject-all-handler", timeout=3)
                    self.sb.sleep(1)

                    # 3. Set Location
                    if not self._safe_click('input[id="search-term"]', "Search Term Input"): return False
                    self.sb.sleep(1)
                    if not self._safe_type('input[id="search-term"]', self.location, "Location Text"): return False
                    self.sb.sleep(3)
                    if not self._safe_click('li[data-js="suggestion"]', "Location Suggestion"): return False
                    self.sb.sleep(1)

                    # 4. Set Dates and Loyalty (Shadow DOM interaction)
                    logger.info(f"Setting Check-in Date to {self.check_in_date}")
                    try:
                        self.sb.execute_script(f"""
                                    document.querySelector("#qb-form-container > div > form > div.quickbook-form_datePicker__gU5Ll > be-datepicker")
                                        .shadowRoot.querySelector("#checkin-date").value = '{self.check_in_date}'
                                """)
                        self.sb.sleep(1)
                    except Exception as e:
                        logger.error(f"Failed to set check-in date via JS (Shadow DOM). Error: {e}")
                        return False

                    logger.info(f"Setting Check-out Date to {self.check_out_date}")
                    try:
                        self.sb.execute_script(f"""
                                    document.querySelector("#qb-form-container > div > form > div.quickbook-form_datePicker__gU5Ll > be-datepicker")
                                        .shadowRoot.querySelector("#checkout-date").value = '{self.check_out_date}'
                                """)
                        self.sb.sleep(3)
                    except Exception as e:
                        logger.error(f"Failed to set check-out date via JS (Shadow DOM). Error: {e}")
                        return False

                    # 5. Select "Use Points" checkbox
                    logger.info("Selecting 'Use Points' checkbox.")
                    try:
                        self.sb.execute_script("""
                                    const checkbox = document.querySelector('be-checkbox[name="use-points"]');
                                    if (checkbox) {
                                        checkbox.checked = true;
                                        checkbox.dispatchEvent(new Event('change', { bubbles: true }));
                                    }
                                """)
                        self.sb.sleep(1)
                    except Exception as e:
                        logger.warning(f"Failed to check 'Use Points' via JS. Proceeding anyway. Error: {e}")

                    # 6. Click Search
                    logger.info("before clicking to find hotel, generating page cookies")
                    # print(self.sb.get_cookies())
                    logger.info("Clicking 'Find Hotels' button...")
                    if not self._safe_click("button.be-button-shop", "Find Hotels Button", sleep_time=6): return False

                    # 7. Ensure all rooms are loaded by scrolling
                    logger.info("Scrolling to ensure dynamic content loads...")
                    self.sb.scroll_to_bottom()
                    self.sb.sleep(5)

        except Exception as ex:
            logger.exception(f"Critical Error: {ex}")
            message = {"details": f"Critical Error: {ex}"}
            return self.build_response(False, message, 100)

        finally:
            try:
                await browser.stop()
                logger.info("Browser stopped successfully.")
            except Exception:
                logger.warning("Browser already stopped or failed to close cleanly.")


# ---------------- Runner ----------------
if __name__ == "__main__":
    async def main():
        crawl = ExtractHyatt()
        data = await crawl.get_search_data(
            hotel_id="yulzm-Hyatt Place Montreal - Downtown",
            check_in_date="2025-11-28",
            check_out_date="2025-11-29",
            guest_count=1,
        )
        if data:
            print("API data fetched successfully", data)
        else:
            print("API data could not be fetched")

    asyncio.run(main())
