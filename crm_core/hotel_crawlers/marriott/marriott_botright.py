import asyncio
import json
import logging
import random
import time
from datetime import datetime
from urllib.parse import urlparse, quote
from .proxy_manager import ProxyManager
from .random_user_agent import get_random_sec_ch_headers, USER_AGENT

# from playwright.async_api import async_playwright
from patchright.async_api import async_playwright

# ---------------- Log configuration ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("marriott_playwright.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


def human_delay(a, b):
    time.sleep(random.uniform(a, b))


class ExtractMarriottPlaywright:
    def __init__(self):
        self._proxy_fetcher = ProxyManager()

    async def linux_format_marriott_date(self, dt_str):
        dt = datetime.strptime(dt_str, "%Y-%m-%d")
        # Format like: Tue, Nov 4
        return dt.strftime("%a %b %d %Y")  # linux

    async def windows_format_marriott_date(self, dt_str):
        dt = datetime.strptime(dt_str, "%Y-%m-%d")
        # Format like: Tue, Nov 4
        return dt.strftime("%a %b %d %Y")  # On Windows use

    async def format_marriott_date(self, dt_str):
        dt = datetime.strptime(dt_str, "%Y-%m-%d")
        return dt.strftime("%a %b %d %Y")

    def build_response(self, success: bool, data: any, status_code: int):
        return {"success": success, "data": data, "status_code": status_code}

    async def get_search_data(self, hotel_id, check_in_date, check_out_date, guest_count):
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

        # Validate inputs
        check_in = datetime.strptime(check_in_date, "%Y-%m-%d")
        check_out = datetime.strptime(check_out_date, "%Y-%m-%d")
        length_of_stay = (check_out - check_in).days
        if not hotel_id or length_of_stay <= 0 or guest_count <= 0:
            raise ValueError("hotel_id/no_of_stays/guest must have valid values.")

        hotel_parts = hotel_id.split("-", 1)
        hotel_code = hotel_parts[0].strip()
        hotel_name = hotel_parts[1].strip() if len(hotel_parts) > 1 else ""
        encoded_hotel_name = quote(hotel_name, safe="")

        async with async_playwright() as p:
            # browser = await p.chromium.launch(headless=True)
            browser = await p.chromium.launch(
                headless=False,
                # proxy=proxy,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                    "--ignore-certificate-errors"
                    # "--disable-blink-features=AutomationControlled",
                    # "--start-maximized",
                    # "--disable-dev-shm-usage",
                    # "--no-sandbox",
                    # "--disable-gpu",
                    # "--disable-infobars",
                    # "--ignore-certificate-errors",
                    # "--enable-features=NetworkService,NetworkServiceInProcess"
                ],
                slow_mo=600
            )
            # context = await browser.new_context()
            context = await browser.new_context(
                viewport=None,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
                locale="en-US",
                permissions=["geolocation"],
                # user_agent=_headers["user-agent"],
                # locale="en-US",
                # extra_http_headers=extra_headers
            )

            # Capture API and search responses correctly in Playwright
            api_responses = {}
            search_responses = {}

            # async def handle_response(response):
            #     try:
            #         url = response.url
            #         if 'PhoenixBookSearchProductsByProperty' in url:
            #             body = await response.body()
            #             try:
            #                 data = json.loads(body)
            #                 api_responses[url] = data
            #                 logger.info(f"Captured Marriott API response: {url}")
            #             except json.JSONDecodeError:
            #                 api_responses[url] = body.decode('utf-8', errors='ignore')
            #                 logger.info(f"Captured Marriott non-JSON response: {url}")
            #         elif '/default.mi' in url or 'search/submitSearch.mi' in url or 'search/findHotels.mi' in url:
            #             body = await response.body()
            #             search_responses[url] = body.decode('utf-8', errors='ignore')
            #             logger.info(f"Captured Marriott Search response: {url}")
            #     except Exception as e:
            #         logger.error(f"Error capturing response from {response.url}: {e}")
            #
            # # Register the event handler before navigation
            # page.on("response", lambda response: asyncio.create_task(handle_response(response)))

            page = await context.new_page()
            try:
                logger.info("Navigating to Marriott home page...")
                await page.goto("https://www.marriott.com/")
                human_delay(5, 10)

                # Search input
                await page.fill('input[id="downshift-1-input"]', hotel_name)
                human_delay(1, 2)
                await page.keyboard.press("ArrowDown")
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(2000)

                # # Select first dropdown suggestion
                # human_delay(1, 1.8)
                # suggest_hotelcheck = await page.wait_for_selector ("//*[@role='option']")
                # # await suggest_hotelcheck.wait_until(is_visible=True, timeout=5000)
                # suggest_hotel = await page.wait_for_selector("//*[@role='option']", find_all=True)
                # if not suggest_hotel:
                #     raise Exception("No hotel suggestions found in dropdown!")
                # await suggest_hotel[0].click()
                # human_delay(1.2, 2.5)

                # --- Open calendar ---
                date_input = page.locator("//input[@aria-label='date-picker']")
                await date_input.wait_for(state="visible", timeout=120_000)
                await date_input.click()
                human_delay(1, 2)

                # --- Format check-in and check-out labels ---
                if _headers["sec-ch-ua-platform"] == '"Linux"':
                    check_in_label = await self.linux_format_marriott_date(check_in_date)
                    check_out_label = await self.linux_format_marriott_date(check_out_date)
                    date_range_str = f"{check_in_label} - {check_out_label}"
                else:
                    check_in_label = await self.windows_format_marriott_date(check_in_date)
                    check_out_label = await self.windows_format_marriott_date(check_out_date)
                    date_range_str = f"{check_in_label} - {check_out_label}"

                # --- Define helper: go_to_month() ---
                async def go_to_month(page, target_month_year: str):
                    """
                    target_month_year should be like 'October 2025'.
                    """
                    while True:
                        # Get all currently visible month captions
                        captions = page.locator(
                            "//*[contains(@class, 'DayPicker-Caption')]//div[@data-scroll-date-marker]"
                        )
                        month_count = await captions.count()
                        months = []
                        for i in range(month_count):
                            text = (await captions.nth(i).inner_text()).strip()
                            months.append(text)

                        if target_month_year in months:
                            break  # target month is visible, stop clicking

                        # Re-query and click next button
                        next_button = page.locator("//*[contains(@class, 'DayPicker-NavButton--next')]")
                        if await next_button.is_visible():
                            await next_button.click()
                            await asyncio.sleep(random.uniform(1, 2))  # async sleep
                        else:
                            raise Exception(f"Could not find month {target_month_year}")

                # --- Format month-year for navigation ---
                human_delay(1, 2)
                checkin_month_year = datetime.strptime(check_in_date, "%Y-%m-%d").strftime("%B %Y")
                logger.info(f"Checkin month year: {checkin_month_year}")
                checkout_month_year = datetime.strptime(check_out_date, "%Y-%m-%d").strftime("%B %Y")
                logger.info(f"Checkout month year: {checkout_month_year}")
                logger.info(f"check_in_label: {check_in_label}")
                logger.info(f"check_out_label: {check_out_label}")

                # --- Navigate to check-in month and select date ---
                await go_to_month(page, checkin_month_year)
                check_in_button = page.locator(
                    f"//div[contains(@class, 'DayPicker-Day') and @aria-label='{check_in_label}']"
                )
                await check_in_button.wait_for(state="visible", timeout=120_000)
                await check_in_button.click()
                human_delay(1.7, 2.8)

                # --- Navigate to check-out month and select date ---
                await go_to_month(page, checkout_month_year)
                check_out_button = page.locator(
                    f"//div[contains(@class, 'DayPicker-Day') and @aria-label='{check_out_label}']"
                )
                await check_out_button.wait_for(state="visible", timeout=120_000)
                await check_out_button.click()
                # await page.mouse.move(random.randint(0, 2), random.randint(3, 8))
                # await page.mouse.down()
                human_delay(1.3, 2.6)
                done_button = page.locator("//button[@aria-label='Done']")
                await done_button.wait_for(state="visible", timeout=120_000)
                await done_button.click()
                human_delay(1, 2)

                # Use points checkbox
                await page.click("//label[@for='usepoints-checkbox']")
                human_delay(1, 2)

                # Click Find Hotels
                await page.click("//button[contains(@class, 'update-search-btn') and contains(text(), 'Find Hotels')]")
                await page.wait_for_timeout(100000)  # Wait for API responses

                # Capture API responses
                if api_responses:
                    logger.info("Captured Marriott API responses:")
                    for url, resp in api_responses.items():
                        edges = resp.get("data", {}).get("searchProductsByProperty", {}).get("edges", [])
                        has_standard = any(
                            edge["node"]["availabilityAttributes"]["rateCategory"]["type"]["code"] == "standard" for
                            edge in edges)
                        has_redemption = any(
                            edge["node"]["availabilityAttributes"]["rateCategory"]["type"]["code"] == "redemption" for
                            edge in edges)

                        if '"Invalid Property Code"' in str(resp):
                            message = {"details": "Property Code is invalid."}
                            return self.build_response(success=True, data=message, status_code=200)
                        elif has_standard and has_redemption:
                            return self.build_response(success=True, data=resp, status_code=200)
                        elif has_standard and not has_redemption:
                            message = {"details": "Hotel is not available at selected date."}
                            return self.build_response(success=True, data=message, status_code=200)
                else:
                    return self.build_response(success=False, data={"details": "Roomrate API failed"}, status_code=429)

            except Exception as ex:
                logger.exception(f"Exception during scraping: {ex}")
                return self.build_response(success=False, data={"details": str(ex)}, status_code=103)
            finally:
                await page.close()
                await browser.close()


if __name__ == "__main__":
    async def main():
        crawler = ExtractMarriottPlaywright()
        data = await crawler.get_search_data(
            hotel_id="swfhr-inn at bellefield hyde park",
            check_in_date="2026-01-06",
            check_out_date="2026-01-08",
            guest_count=1
        )
        print(data)


    asyncio.run(main())
