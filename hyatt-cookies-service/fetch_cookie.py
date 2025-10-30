import asyncio
import time
import logging
from playwright.async_api import async_playwright
from urllib.parse import quote_plus
from ua import user_agent
import random as rand
from urllib.parse import urlparse
from proxy_manager import ProxyManager
from random_user_agent import get_random_sec_ch_headers
from datetime import datetime, timedelta


# ---------------- Log configuration ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[ logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

async def human_delay(a: float, b: float):
    await asyncio.sleep(rand.uniform(a, b))

BROWSER_MAP = {
    "chrome": "chromium",
    "edge": "chromium",
    "opera": "chromium",
    "firefox": "firefox",
    "safari": "webkit"
}

HOTEL_LIST = [
    "Hyatt Place Montreal - Downtown",
    "Hyatt Centric Montreal",
    "The Anndore House",
    "The Walper Hotel",
    "Hyatt House Montreal/Downtown",
    "Hyatt House Anchorage",
    "Hyatt Place Kelowna",
    "Hyatt Place Prince George",
    "Hyatt Regency Vancouver",
    "Hyatt Place Ottawa - West",
]

def get_random_hotel():
    """Selects a random hotel and URL-encodes it safely for query usage."""
    hotel_name = rand.choice(HOTEL_LIST)
    encoded_hotel = quote_plus(hotel_name)  # replaces spaces with '+'
    return encoded_hotel

def parse_proxy(proxy_url: str):
    if not proxy_url:
        return None
    parsed = urlparse(proxy_url)
    proxy = {"server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"}
    if parsed.username and parsed.password:
        proxy["username"] = parsed.username
        proxy["password"] = parsed.password
    return proxy

def generate_random_dates():
    today = datetime.today()
    checkin_offset = rand.randint(5, 65)
    checkin_date = today + timedelta(days=checkin_offset)
    checkout_offset = rand.randint(3, 10)
    checkout_date = checkin_date + timedelta(days=checkout_offset)
    checkin_str = checkin_date.strftime("%Y-%m-%d")
    checkout_str = checkout_date.strftime("%Y-%m-%d")
    return checkin_str, checkout_str

check_in , check_out = generate_random_dates()
encoded_location = get_random_hotel()
SEARCH_URL = (
        f"https://www.hyatt.com/HyattSearch?location={encoded_location}"
        f"&checkinDate={check_in}&checkoutDate={check_out}&rooms=1&adults=1&kids=0"
        "&spiritCode=yulzm&locale=en-US&rate=Standard&childAge1=&childAge2=&childAge3="
        "&childAge4=&offercode=&corp_id=&rateFilter=woh&accessibilityCheck=false&roomTypeCode="
    )

class UserAgentExecutor:
    """Iterates through all user agents for the given browser and runs Playwright contexts."""
    def __init__(self, browser_name: str, user_agents: dict):
        if browser_name not in BROWSER_MAP:
            raise ValueError(f"Unsupported browser: {browser_name}")
        self.playwright_browser = BROWSER_MAP[browser_name]
        self.headers={}
        self.cookies_data = {}
        self.browser_name = browser_name
        self._proxy_fetcher = ProxyManager()
        self.WATCH_COOKIES = ["x-kpsdk-ct", "tkrm_alpekz_s1.3-ssn"]
        self.user_agents = user_agents.get(browser_name, [])
        if not self.user_agents:
            raise ValueError(f"No user agents found for browser '{browser_name}'.")

    
    async def wait_for_cookies(self, context, names, timeout_s=20, poll_interval=0.5):
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            cookies = await context.cookies()
            cookie_names = {c["name"] for c in cookies}
            if all(name in cookie_names for name in names):
                return cookies
            await asyncio.sleep(poll_interval)
        return await context.cookies()
    
    async def create_context(self, playwright, user_agent: str, use_proxy = True):
        _proxy_url = self._proxy_fetcher.fetch_proxy() if use_proxy else None
        proxy = parse_proxy(_proxy_url) if _proxy_url else None
        if use_proxy and not proxy:
            logger.warning("Proxy enabled but parse failed; continuing without proxy")
        browser_type = getattr(playwright, self.playwright_browser)
        args = []
        if self.playwright_browser == "chromium":
            args = [
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox'
            ]
        browser = await browser_type.launch(headless=False, proxy=proxy, args= args)
        context = await browser.new_context(user_agent=user_agent, locale="en-US",
                        extra_http_headers={k: v for k, v in self.headers.items() if k.lower() != "user-agent"})
        return browser, context
    
    async def execute(self):
        async with async_playwright() as playwright:
            for ua in self.user_agents:
                browser_family,self.headers = get_random_sec_ch_headers(ua)
                logger.info(f"Launching {self.browser_name} with UA:{ua}")
                browser, context = await self.create_context(playwright, ua)
                page = await context.new_page()
                # await page.add_style_tag(content="*, *::before, *::after {transition:none!important;animation:none!important;}")
                raw_cookies_list = []
                async def handle_response(response):
                        if '/shop/rooms/' in response.url:
                            try:
                                headers = await response.all_headers()
                                if "set-cookie" in headers:
                                    raw_cookies_list.append(headers["set-cookie"])
                            except Exception:
                                pass

                page.on("response", handle_response)
                page.defult_timeout = 100000
                try:
                    await page.goto("https://www.hyatt.com/loyalty/en-US", wait_until="load", timeout=120000)
                    logger.info(f"Loaded Home Page")
                    await human_delay(4, 8)
                    await asyncio.sleep(rand.randint(3,6))
                    logger.info(f"Navigating to SEARCH_URLw to trigger cookies")
                    await page.goto(SEARCH_URL, wait_until="load", timeout=120000)
                    await human_delay(3, 6)
                    cookies = await self.wait_for_cookies(context, self.WATCH_COOKIES, timeout_s=25)
                    for c in cookies:
                        if c.get("name") in self.WATCH_COOKIES:
                            self.cookies_data[c["name"]] = c.get("value")       
                    result = {"cookies": self.cookies_data, "raw_cookies": cookies}
                    print(result)
                    await asyncio.sleep(3)
                except Exception as e:
                    logger.error(f"⚠️ Navigation failed for UA:{e}")
                finally:
                    await browser.close()
                    logger.info(f"Closed instance")


async def main():
    browser_name = "firefox"  
    executor = UserAgentExecutor(browser_name, user_agent)
    await executor.execute()


if __name__ == "__main__":
    asyncio.run(main())
