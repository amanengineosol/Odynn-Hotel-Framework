import json
import logging
import random as rand
import asyncio
import time
from urllib.parse import urlparse
from patchright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

from proxy_manager import ProxyManager
from random_user_agent import get_random_sec_ch_headers, USER_AGENT
from cache_processor import CrawlerRedisClient   # adjust import to your project layout

# ---------------- Log configuration ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("hyatt.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ---------------- Utility ----------------
async def human_delay(a: float, b: float):
    await asyncio.sleep(rand.uniform(a, b))

def parse_proxy(proxy_url: str):
    if not proxy_url:
        return None
    parsed = urlparse(proxy_url)
    proxy = {"server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"}
    if parsed.username and parsed.password:
        proxy["username"] = parsed.username
        proxy["password"] = parsed.password
    return proxy

class CookiesFetcher:
    def __init__(self):
        self._proxy_fetcher = ProxyManager()
        self._redis_client = CrawlerRedisClient(1)

    def build_response(self, success: bool, data: any, status_code: int):
        return {"success": success, "data": data, "status_code": status_code}

    async def save_cookie_to_redis(self, cookie_value: str):
        try:
            save_fn = getattr(self._redis_client, "save_cookie", None)
            if save_fn:
                if asyncio.iscoroutinefunction(save_fn):
                    await save_fn(cookie_value)
                else:
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, save_fn, cookie_value)
                logger.info("Cookie saved to Redis")
            else:
                logger.warning("Redis client does not implement save_cookie()")
        except Exception:
            logger.exception("Failed to save cookie to Redis (ignored)")

    @staticmethod
    def cookies_to_header(cookies_list):
        return "; ".join(f"{c['name']}={c['value']}" for c in cookies_list if c.get("name") and c.get("value"))

    async def wait_for_cookies(self, context, names, timeout_s=20, poll_interval=0.5):
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            cookies = await context.cookies()
            cookie_names = {c["name"] for c in cookies}
            if all(name in cookie_names for name in names):
                return cookies
            await asyncio.sleep(poll_interval)
        return await context.cookies()

    async def get_cookies(self, max_retries=3, headless=True, use_proxy=True, save_local_json=True):
        _proxy_url = self._proxy_fetcher.fetch_proxy() if use_proxy else None
        proxy = parse_proxy(_proxy_url) if _proxy_url else None
        if use_proxy and not proxy:
            logger.warning("Proxy enabled but parse failed; continuing without proxy")

        # Random UA
        browser_family, headers = get_random_sec_ch_headers(USER_AGENT)
        _headers = headers or {"user-agent": USER_AGENT}

        SEARCH_URL = (
            "https://www.hyatt.com/HyattSearch?location=Hyatt+Place+Montreal+-+Downtown"
            "&checkinDate=2025-11-12&checkoutDate=2025-11-14&rooms=1&adults=1&kids=0"
            "&spiritCode=yulzm&locale=en-US&rate=Standard&childAge1=&childAge2=&childAge3="
            "&childAge4=&offercode=&corp_id=&rateFilter=woh&accessibilityCheck=false&roomTypeCode="
        )
        WATCH_COOKIES = ["x-kpsdk-ct", "tkrm_alpekz_s1.3-ssn"]

        try:
            async with async_playwright() as p:
                launch_kwargs = {"headless": headless,
                                  "args": [
                                    '--no-first-run',
                                    '--disable-blink-features=AutomationControlled',
                                    '--disable-dev-shm-usage',
                                    '--no-sandbox',
                                    '--disable-setuid-sandbox'
                            ]}
                if proxy:
                    launch_kwargs["proxy"] = proxy

                browser = await p.chromium.launch(**launch_kwargs)
                try:
                    context = await browser.new_context(
                        user_agent=_headers.get("user-agent", USER_AGENT),
                        locale="en-US",
                        extra_http_headers={k: v for k, v in _headers.items() if k.lower() != "user-agent"}
                    )
                    page = await context.new_page()
                    page.set_default_timeout(120000)
                    await page.add_style_tag(content="*, *::before, *::after {transition:none!important;animation:none!important;}")

                    cookies_data = {}

                    # Listen to responses and collect cookies
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

                    for attempt in range(1, max_retries + 1):
                        try:
                            logger.info(f"Attempt {attempt} navigating to Hyatt home")
                            await page.goto("https://www.hyatt.com/loyalty/en-US", wait_until="load")
                            await human_delay(4, 8)
                            await asyncio.sleep(4)

                            logger.info(f"Navigating to SEARCH_URL to trigger cookies")
                            await page.goto(SEARCH_URL, wait_until="load")
                            await human_delay(3, 6)

                            cookies = await self.wait_for_cookies(context, WATCH_COOKIES, timeout_s=25)
                            status = False
                            for c in cookies:
                                if c.get("name") in WATCH_COOKIES:
                                    cookies_data[c["name"]] = c.get("value")
                                    await self.save_cookie_to_redis(c.get("value"))

                            cookie_header = self.cookies_to_header(cookies)
                            result = {"cookies": cookies_data, "cookie_header": cookie_header, "raw_cookies": cookies}
                            return self.build_response(True, result, 200)

                        except PlaywrightTimeoutError as pwex:
                            logger.warning(f"Attempt {attempt} timeout: {pwex}")
                            if attempt == max_retries:
                                return self.build_response(False, {"details": str(pwex)}, 103)
                        except Exception as inner_ex:
                            logger.exception(f"Attempt {attempt} error: {inner_ex}")
                            if attempt == max_retries:
                                return self.build_response(False, {"details": str(inner_ex)}, 103)

                finally:
                    await browser.close()
        except Exception as ex:
            logger.exception(f"Critical Error: {ex}")
            return self.build_response(False, {"details": str(ex)}, 100)


if __name__ == "__main__":
    fetcher = CookiesFetcher()
    resp = asyncio.run(fetcher.get_cookies(max_retries=3, headless=False, use_proxy=True, save_local_json=True))
    print(json.dumps(resp, indent=2))
