import json
import logging
import random
import time
from datetime import datetime, timezone
import requests
from playwright.sync_api import sync_playwright
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
    time.sleep(random.uniform(a, b))


class ExtractHyatt:
    COOKIE_FILE = "./hyatt_cookies.json"

    def __init__(self):
        self._proxy_fetcher = ProxyManager()
        self._proxy_url = self._proxy_fetcher.fetch_proxy()
        browser_family, headers = get_random_sec_ch_headers(USER_AGENT)
        while browser_family != "chromium":
            browser_family, headers = get_random_sec_ch_headers(USER_AGENT)
        self._headers = headers
        self._headers["cache-control"] = "no-cache"

    def build_response(self, success: bool, data, status_code: int):
        return {
            "Success": success,
            "data": data,
            "status_code": status_code
        }

    def wait_for_cookies(self, context, timeout=60, poll_interval=2):
        waited = 0
        while waited < timeout:
            cookies = context.cookies()
            for cookie in cookies:
                if cookie["name"].startswith("tkrm_alpekz_s1.3"):
                    logger.info(f"Required cookies found: {cookie['name']}")
                    return cookies
            time.sleep(poll_interval)
            waited += poll_interval
        return context.cookies()

    def save_cookies_to_file(self, cookies):
        with open(self.COOKIE_FILE, "w", encoding="utf-8") as f:
            json.dump(cookies, f, ensure_ascii=False, indent=4)
        logger.info(f"Cookies saved to {self.COOKIE_FILE}")

    def load_cookies_from_file(self):
        try:
            with open(self.COOKIE_FILE, "r", encoding="utf-8") as f:
                cookies = json.load(f)
            logger.info(f"Loaded cookies from {self.COOKIE_FILE}")

            now = datetime.now(timezone.utc).timestamp()
            valid_cookies = []
            for c in cookies:
                if "expires" in c and c["expires"] and c["expires"] < now:
                    logger.info(f"Cookie {c['name']} expired at {c['expires']}, skipping")
                else:
                    valid_cookies.append(c)

            if not valid_cookies:
                logger.warning("Cookies expired. Need to fetch new ones.")
                return None

            return valid_cookies

        except FileNotFoundError:
            logger.error("No cookie file found.")
            return None

    def get_freshCookies(self, hotel_id, check_in_date, check_out_date, guest_count):
        logger.info("Getting proxy IP for current session")
        if not self._proxy_url:
            raise Exception("ERROR-101 : Proxy url not retrieved from the server")

        parsed = urlparse(self._proxy_url)
        proxy = {
            "server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}",
            "username": parsed.username,
            "password": parsed.password,
        }

        logger.info("Proxy url dict created for request")
        logger.info("Setting up crawler to extract data")

        # Validate inputs
        check_in = datetime.strptime(check_in_date, "%Y-%m-%d")
        check_out = datetime.strptime(check_out_date, "%Y-%m-%d")
        length_of_stay = (check_out - check_in).days
        if not hotel_id or length_of_stay <= 0 or guest_count <= 0:
            raise ValueError("hotel_id/no_of_stays/guest must have valid values.")

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
                        k: v for k, v in self._headers.items() if k.lower() != "user-agent"
                    }

                    logger.info(f"Selected UA: {self._headers['user-agent']}")

                    context = browser.new_context(
                        user_agent=self._headers["user-agent"],
                        locale="en-US",
                        extra_http_headers=extra_headers,
                    )

                    page = context.new_page()
                    page.set_default_timeout(100000)

                    page.goto("https://www.hyatt.com/", wait_until="load", timeout=120000)
                    human_delay(12, 30)

                    page.locator('input[data-id="location"]').wait_for(timeout=120000)
                    page.get_by_role("button", name="Find Hotels").wait_for(timeout=80000)

                    logger.info("Home page request completed successfully.....")

                    cookies = self.wait_for_cookies(context)
                    if not cookies:
                        logger.error("No cookies captured, retrying...")
                        return None
                    time.sleep(35)
                    logger.info("Cookies captured:")
                    self.save_cookies_to_file(cookies)
                    return cookies

                except Exception as ex:
                    logger.exception(f"Exception occurred during scraping: {ex}")
                finally:
                    logger.info("Closing browser...")
                    browser.close()
        except Exception as ex:
            logger.exception(f"Critical Error: {ex}")

    def transfer_cookies_to_session(self, cookies):
        proxies_requests = {"http": self._proxy_url, "https": self._proxy_url}
        sess = requests.Session()
        for cookie in cookies:
            sess.cookies.set(
                cookie["name"],
                cookie["value"],
                domain=cookie.get("domain", ""),
                path=cookie.get("path", "/"),
            )
        sess.proxies.update(proxies_requests)
        return sess

    def get_search_data(self, hotel_id, check_in_date, check_out_date, guest_count, max_retries=2):
        hotel_id_name = hotel_id
        parts = hotel_id_name.split("-", 1)
        hotel_id = parts[0].strip()
        logger.info(f"Hotel ID: {hotel_id}")
        hotel_name = parts[1].strip() if len(parts) > 1 else ""
        logger.info(f"Hotel Name: {hotel_name}")
        encoded_hotel_name = quote(hotel_name, safe="")

        # ---------------- Retry Loop ----------------
        for attempt in range(max_retries):
            # ---------------- Cookie Handling ----------------
            cookies = self.load_cookies_from_file()
            if not cookies:
                logger.info("No valid cookies found. Fetching new cookies...")
                cookies = self.get_freshCookies(hotel_id, check_in_date, check_out_date, guest_count)
                if not cookies:
                    logger.error("No cookies captured, aborting")
                    return None

            # ---------------- Session Setup ----------------
            sess = self.transfer_cookies_to_session(cookies)
            try:
                suggestion_url = (
                    f"https://www.hyatt.com/quickbook/autocomplete?"
                    f"query={encoded_hotel_name.replace('%2F', '/')}&locale=en-US&includeGoogleSuggestions=true"
                )

                logger.info(f"[Attempt {attempt + 1}] Suggestion API: {suggestion_url}")
                sess.headers.update({
                    'x-requested-with': 'XMLHttpRequest',
                    'user-agent': self._headers["user-agent"],
                    'accept': 'application/json, text/javascript, */*; q=0.01',
                    'sec-fetch-site': 'same-origin',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-dest': 'empty',
                    'referer': 'https://www.hyatt.com/',
                    'accept-language': 'en-US,en;q=0.9',
                })

                suggestion_response = sess.get(suggestion_url)
                if suggestion_response.status_code == 401:
                    logger.warning("Cookies rejected at suggestion API.")
                    if attempt + 1 < max_retries:
                        cookies = self.get_freshCookies(hotel_id, check_in_date, check_out_date, guest_count)
                        sess = self.transfer_cookies_to_session(cookies)
                        continue
                    else:
                        return self.build_response(False, suggestion_response.text, suggestion_response.status_code)

                selectHotel_url = (
                    f"https://www.hyatt.com/HyattSearch?locale=en-US&spiritCode={hotel_id}"
                    f"&newAutocomplete=&location={encoded_hotel_name.replace('%20', '+')}"
                    f"&checkinDate={check_in_date}&checkoutDate={check_out_date}"
                    f"&rooms=1&adults={guest_count}&kids=0&rate=Standard"
                    f"&offercode=&corp_id=&rateFilter=woh"
                    f"&searchFilters=locale%3Den-US%26spiritCodes%3D{hotel_id}&externalBookingURL="
                )

                logger.info(f"Selecting Hotel :: {selectHotel_url}")
                sess.headers.pop("x-requested-with", None)
                sess.headers.update({
                    'upgrade-insecure-requests': '1',
                    'user-agent': self._headers["user-agent"],
                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'sec-fetch-site': 'same-origin',
                    'sec-fetch-mode': 'navigate',
                    'sec-fetch-user': '?1',
                    'sec-fetch-dest': 'document',
                    'referer': 'https://www.hyatt.com/',
                    'accept-language': 'en-US,en;q=0.9'
                })

                selectHotel_response = sess.get(selectHotel_url)
                ref_url = selectHotel_response.url
                logger.info(f"Redirected to Hotel :: {selectHotel_response.status_code} {ref_url}")

                if selectHotel_response.status_code >= 400:
                    logger.warning("Cookies rejected at hotel selection.")
                    if attempt + 1 < max_retries:
                        cookies = self.get_freshCookies(hotel_id, check_in_date, check_out_date, guest_count)
                        sess = self.transfer_cookies_to_session(cookies)
                        continue
                    else:
                        return self.build_response(False, selectHotel_response.text, selectHotel_response.status_code)

                # Roomrate API
                url = (
                    f"https://www.hyatt.com/shop/service/rooms/roomrates/{hotel_id}"
                    f"?spiritCode={hotel_id}&rooms=1&adults={guest_count}"
                    f"&location={encoded_hotel_name}"
                    f"&checkinDate={check_in_date}&checkoutDate={check_out_date}"
                    f"&kids=0&rate=Standard&suiteUpgrade=true"
                )
                logger.info(f"Roomrate API: {url}")

                sess.headers.update({
                    "Accept": "*/*",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Referer": ref_url,
                    "user-agent": self._headers["user-agent"],
                    "Sec-Fetch-Dest": "empty",
                    "Sec-Fetch-Mode": "cors",
                    "Sec-Fetch-Site": "same-origin",
                })

                response = sess.get(url)
                text_resp = response.text

                if response.status_code == 200:
                    logger.info(f"Response fetched successfully from Roomrate API")
                    try:
                        json_data = json.dumps(text_resp)
                        return self.build_response(True, response.json(), response.status_code)
                    except json.JSONDecodeError:
                        logger.warning("Response is not valid JSON")
                        json_data = {"raw_response": text_resp}
                        return self.build_response(False, json_data, response.status_code)

                else:
                    logger.error(f"Roomrate API failed with status {response.status_code}")
                    return self.build_response(False, text_resp, response.status_code)


            except Exception as ex:
                logger.exception(f"Attempt {attempt + 1} failed: {ex}")
                if attempt + 1 == max_retries:
                    raise
                else:
                    logger.info("Retrying...")

        return None

# ---------------- Runner ----------------
if __name__ == "__main__":
    crawl = ExtractHyatt()
    data = crawl.get_search_data(
        hotel_id="bhmhr-Hyatt Regency Birmingham - The Wynfrey Hotel",
        check_in_date="2025-11-02",
        check_out_date="2025-11-04",
        guest_count=1,
    )
    if data:
        print("API data fetched successfully")
    else:
        print("API data could not be fetched with current cookies")
