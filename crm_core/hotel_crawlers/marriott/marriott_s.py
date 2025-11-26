import random
import json
import time
import logging
from datetime import datetime
from seleniumbase import SB
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from mycdp.network import PrivateNetworkRequestPolicy

# Gracefully handle new Chrome value
try:
    PrivateNetworkRequestPolicy("PermissionBlock")
except ValueError:
    PrivateNetworkRequestPolicy._value2member_map_["PermissionBlock"] = list(PrivateNetworkRequestPolicy)[0]

import mycdp.util

_event_parsers = mycdp.util._event_parsers

def patched_parse_event(data):
    method = data.get("method")
    params = data.get("params", {})
    parser = _event_parsers.get(method)

    if parser is None:
        # ignore unknown CDP events
        return None

    return parser.from_json(params)

mycdp.util.parse_json_event = patched_parse_event

# --- SETUP LOGGING ---
# Configure the logger for the module
logger = logging.getLogger('MarriottScraper')
logger.setLevel(logging.DEBUG)
logger.propagate = False

# Create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# Create formatter and add it to the handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)

# Add the handler to the logger
if not logger.handlers:
    logger.addHandler(ch)

# --- CONFIGURATION (Global Constants) ---

USER_AGENT_POOL = [
    # "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    # "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 OPR/125.0.0.0",
    # "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 OPR/125.0.0.0",
    # "Mozilla/5.0 (Windows NT 10.0; WOW64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 OPR/125.0.0.0",
    # "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.7390.95 Safari/537.36 Edg/141.0.3537.57",
    # "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.7204.169 Safari/537.36 OPR/142.0.7204.169",
    # "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
    # "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    # "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    # "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    # "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:141.0) Gecko/20100101 Firefox/141.0",
    # "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:141.0) Gecko/20100101 Firefox/141.0",
    # "Mozilla/5.0 (X11; Linux x86_64; rv:141.0) Gecko/20100101 Firefox/141.0",
    # "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:141.0) Gecko/20100101 Firefox/141.0",
    # "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Safari/605.1.15",
    # "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0"
]
BASE_URL = "https://www.marriott.com/default.mi"

class ExtractMarriott:
    """
    Encapsulates all logic for scraping Hyatt room card data using SeleniumBase,
    with robust logging and exception handling.
    """

    def __init__(self):
        # Configuration
        self.check_in_date = None
        self.check_out_date = None
        self.location = None
        self.user_agent_pool = USER_AGENT_POOL
        self.selected_user_agent = random.choice(self.user_agent_pool)
        self.proxy_url = self._get_proxy()

        # State
        self.structured_room_data = []
        self.sb = None
        logger.info(f"Using User-Agent: {self.selected_user_agent}")
        # logger.info(f"Using Proxy: {self.proxy_url}")

    def build_response(self, success: bool, data: any, status_code: int, error_message: str = None):
        """Standardizes the response format for the client."""
        response = {
            "success": success,
            "data": data,
            "status_code": status_code
        }
        if error_message:
            response['error'] = error_message
        return response

    def _get_proxy(self):
        """Fetches the proxy URL from the ProxyManager utility."""
        try:
            # Assuming ProxyManager is available and working
            from .proxy_manager import ProxyManager
            return ProxyManager().fetch_proxy()

        except NameError:
            logger.error("No proxy available: 'ProxyManager' is not defined.")
            raise Exception("No proxy available: 'ProxyManager' is not defined.")


    def _parse_room_cards_html(self, html_content: str) -> list:
        """Parse Marriott room cards from provided HTML."""
        if not self.sb:
            logger.error("SeleniumBase instance missing")
            return []

        logger.info("Parsing room HTML content...")
        rooms = []

        try:
            self.sb.set_content(html_content)
            self.sb.sleep(0.9)

            # SELECT ALL ROOM CARDS
            room_cards = self.sb.find_elements("div[data-testid='RateCardV2']")
            logger.info(f"Found {len(room_cards)} room cards.")

            for card in room_cards:
                try:
                    logger.info(f"Parsing card '{card.text}'...")
                    room = {}

                    # Room Name
                    room["title"] = card.find_element(
                        By.CSS_SELECTOR, ".room-name"
                    ).text.strip()

                    # Room Details Link -> extract roomPoolCode
                    try:
                        details_link = card.find_element(
                            By.CSS_SELECTOR, ".room-desc a.room-detail-link"
                        ).get_attribute("href")
                        room_code = details_link.split("roomPoolCode=")[1].split("&")[0]
                        room["room_type_code"] = room_code
                    except Exception:
                        room["room_type_code"] = "N/A"

                    # Description (Marriott rarely shows description, may be blank)
                    try:
                        desc_el = card.find_element(
                            By.CSS_SELECTOR, ".rate-description"
                        )
                        room["description"] = desc_el.text.strip()
                    except:
                        room["description"] = "No description"

                    # Primary image
                    try:
                        img = card.find_element(
                            By.CSS_SELECTOR, ".image-container picture img"
                        ).get_attribute("src")
                        room["image_url"] = img
                    except:
                        room["image_url"] = "No Image Found"

                    # Points rate
                    try:
                        points = card.find_element(
                            By.CSS_SELECTOR, ".rate-details .points span"
                        ).text.strip()
                    except:
                        points = "N/A"

                    room["point_value"] = points

                    rooms.append(room)

                except Exception as e:
                    logger.warning(f"Failed to parse room card: {e}")
                    continue

        except Exception as e:
            logger.error(f"Parsing failed: {e}")

        self.sb.set_content("")
        return rooms

    def _safe_click(self, selector: str, description: str, sleep_time: float = 1.0):
        """Wrapper for sb.click with robust exception handling for timeouts."""
        try:
            self.sb.click(selector)
            logger.info(f"Successfully clicked: {description} ({selector})")
            self.sb.sleep(sleep_time)
            return True
        except TimeoutException:
            logger.error(f"Timeout clicking element: {description} ({selector}). Page state check needed.")
            return False
        except Exception as e:
            logger.error(f"General error clicking element: {description} ({selector}). Error: {e}")
            return False

    def _safe_type(self, selector: str, text: str, description: str,
                   min_delay: float = 0.01, max_delay: float = 0.3,
                   hesitation_chance: float = 0.04):

        """
        Types text into an input field using real human-like keystrokes.
        Works correctly with SeleniumBase + UC.
        """

        try:
            # Focus the element first (important!)
            self.sb.click(selector)

            # Clear old input safely
            self.sb.clear(selector)

            for char in text:
                # send_keys works perfectly for single characters
                self.sb.send_keys(selector, char)

                # random typing delay
                delay = random.uniform(min_delay, max_delay)
                time.sleep(delay)

                # occasional longer hesitation (human behavior)
                if random.random() < hesitation_chance:
                    time.sleep(random.uniform(0.1, 0.4))

            logger.info(f"Successfully typed '{text}' into: {description} ({selector})")
            return True

        except TimeoutException:
            logger.error(f"Timeout typing into: {description} ({selector})")
            return False

        except Exception as e:
            logger.error(f"Typing error on {description} ({selector}). Error: {e}")
            return False


    def _navigate_and_search(self):
        """Handles browser navigation, element interaction, and search execution."""

        # 1. Navigate and setup
        url = BASE_URL
        logger.info(f"Navigating to base URL: {url}")
        try:
            self.sb.open(url)
            self.sb.sleep(3.5)
        except WebDriverException as e:
            logger.critical(f"Failed to navigate or activate CDP mode. Error: {e}")
            return False

        # self.sb.focus("body")

        # 2. Set Location
        if not self._safe_click('input[id="downshift-1-input"]', "Destination Input"):
            return False
        self.sb.sleep(1)

        if not self._safe_type('input[id="downshift-1-input"]', self.location, "Destination Text"):
            return False

        self.sb.sleep(3)
        self.sb.wait_for_element_visible('[role="option"]', timeout=10)
        self.sb.click('[role="option"]')
        logger.info("Successfully clicked suggestion")
        self.sb.sleep(1)

        # ---- OPEN CALENDAR ----
        logger.info("Opening calendar...")

        self.sb.click("//body")
        self.sb.sleep(0.3)

        date_input = self.sb.find_element("//input[@aria-label='date-picker']")
        date_input.click()
        logger.info("Successfully open calendar")
        self.sb.sleep(0.5)

        def go_to_month(target_month_year: str):
            """
            Navigates the calendar forward until the target month/year is visible.
            The target_month_year should be in the format 'month year' (e.g., 'january 2026').
            """
            target = target_month_year.strip().lower()
            logger.info(f"Go to month: {target_month_year}")

            # Limit search to prevent infinite loop
            for _ in range(18):
                caps = self.sb.find_elements("//div[@class='DayPicker-Caption']/div")
                caps = [c for c in caps if c.text.strip()]

                if not caps:
                    self.sb.sleep(0.3)
                    continue

                visible = [c.text.strip().lower() for c in caps]
                first = visible[0]

                logger.info(f"Visible month caption: {visible}")

                # 2. Check if the target month is the first visible month
                if first == target:
                    logger.info(f"First visible month matched target: {first}")
                    # Wait for the day grid to be fully rendered
                    self.sb.wait_for_element_visible("//div[contains(@class,'DayPicker-Body')]", timeout=10)
                    return

                # 3. Click the next button and wait for the render
                next_button = self.sb.find_element("//span[contains(@class,'DayPicker-NavButton--next')]")
                next_button.click()

                self.sb.sleep(0.3)
                self.sb.wait_for_element_visible("//div[contains(@class,'DayPicker-Body')]", timeout=10)
                self.sb.sleep(0.3)

            raise Exception(f"Could not reach month: {target_month_year}")


        def select_check_in_check_out(check_in_date_label: str, check_out_date_label: str, check_in_month_year,
            check_out_month_year):

            target_month_year = check_in_month_year

            # --- STEP 1: Navigate to the correct month ---
            go_to_month(target_month_year)
            self.sb.sleep(9)

            # html = self.sb.get_page_source()
            # with open("quickbook_debug.html", "w", encoding="utf-8") as f:
            #     f.write(html)

            # --- STEP 2: Select Dates via JavaScript ---
            logger.info(f"Selecting dates: {check_in_date_label} to {check_out_date_label}")

            # --- STEP 2: Select Dates using direct Selenium Click ---
            CHECK_IN_XPATH = f'//div[@aria-label="{check_in_date_label}"]'
            CHECK_OUT_XPATH = f'//div[@aria-label="{check_out_date_label}"]'

            try:
                check_in_element = self.sb.find_element(CHECK_IN_XPATH)
                self.sb.sleep(0.5)
                check_in_element.click()
                logger.info(f"Clicked Check-in date: {check_in_date_label}")
                self.sb.sleep(1)

                check_out_element = self.sb.find_element(CHECK_OUT_XPATH)
                self.sb.sleep(0.8)
                check_out_element.click()
                logger.info(f"Clicked Check-out date: {check_out_date_label}")
                self.sb.sleep(0.9)


                done_button_xpath = "//button[@aria-label='Done']"
                self.sb.click(done_button_xpath)
                logger.info("Successfully clicked the 'Done' button.")
                self.sb.sleep(1)
            except Exception as e:
                logger.warning(f"Could not click the 'Done' button: {e}")

        def convert_date_format(
                date_string: str,
                input_format: str = "%Y-%m-%d",
                output_format: str = "%a %b %d %Y"
        ) -> str:
            """
            Converts a date string from one format to another.

            Args:
                date_string: The original date string (e.g., "2026-01-12").
                input_format: The format of the original date string (e.g., "%Y-%m-%d").
                output_format: The desired format for the output date string
                               (e.g., "%a %b %d %Y" for 'Mon Jan 12 2026').

            Returns:
                The date string in the new specified format.
            """
            try:
                # Parse the original string into a datetime object
                date_object = datetime.strptime(date_string, input_format)

                # Format the datetime object into the desired output string
                new_date_str = date_object.strftime(output_format)

                return new_date_str

            except ValueError as e:
                logger.info(f"Error converting date '{date_string}': {e}")
                return date_string

        check_in_date_label = convert_date_format(self.check_in_date)
        check_out_date_label = convert_date_format(self.check_out_date)

        check_in_month_year = convert_date_format(self.check_in_date, output_format="%B %Y")
        check_out_month_year = convert_date_format(self.check_out_date, output_format="%B %Y")

        select_check_in_check_out(
            check_in_date_label,
            check_out_date_label,
            check_in_month_year,
            check_out_month_year
        )

        logger.info("Date selection complete.")

        # Select 'Use Points'
        if not self._safe_click("//label[@for='usepoints-checkbox']", "usepoints-checkbox"):
            return False
        self.sb.sleep(3)

        # Click 'Find Hotels'
        if not self._safe_click("button.update-search-btn", "find hotel button"):
            return False

        self.sb.sleep(9)
        # self.sb.focus("body")
        self.sb.save_screenshot("list_page.png")

        view_rates_xpath = "//a[contains(@class, 'view-rates-button-container')]/button"
        self.sb.wait_for_element_visible(view_rates_xpath, timeout=240)
        self.sb.click(view_rates_xpath)
        self.sb.sleep(9)
        # self.sb.focus("body")

        logger.info("Clicked 'View Rates' successfully!")
        # self.sb.scroll_to_bottom()
        # copyright_selector = ".mt-copyright-component"
        #
        # logger.info(f"Starting slow scroll to element: {copyright_selector}...")
        #
        # # 3. Perform the smooth scroll
        # self.sb.scroll_to_element(copyright_selector)
        self.sb.scroll_to_bottom()
        self.sb.sleep(3)
        self.sb.scroll_to_top()
        # self.sb.scroll_to(
        #     selector=copyright_selector,
        #     duration=random.randint(1, 3),  # Scroll time (3 seconds for a noticeable, slow animation)
        #     offset="-100",  # Optional: Scrolls to 100 pixels above the element (useful for viewing)
        #     by_js=True  # Ensures the smooth JavaScript animation runs
        # )

        logger.info("Slow scroll finished. Element is now in view.")


        self.sb.sleep(5)

        self.sb.save_screenshot("room_page.png")
        return True


    def _extract_html_and_parse(self):
        """Extracts the entire room list HTML and calls the parser."""

        try:
            logger.info("Scrolling entire page to load room cards...")

            # Extract page HTML after scrolling
            html = self.sb.get_attribute("body", "outerHTML")
            logger.info(f"Extracted HTML length: {len(html)}")

            self.structured_room_data = self._parse_room_cards_html(html)

            logger.info(f"Parsed {len(self.structured_room_data)} rooms.")

        except Exception as e:
            logger.error(f"Critical HTML extraction error: {e}")
            self.structured_room_data = []


    def get_search_data(self, hotel_id, check_in_date, check_out_date, guest_count=1):
        """Main method to run the complete scraping process and return client response."""
        hotel_id_name = hotel_id
        parts = hotel_id_name.split("-", 1)
        hotel_id = parts[0].strip()
        logger.info(f"Hotel ID: {hotel_id}")
        location = parts[1].strip() if len(parts) > 1 else ""
        logger.info(f"Hotel Name: {location}")
        self.location = location
        self.check_in_date = check_in_date
        self.check_out_date = check_out_date
        final_response = self.build_response(success=False, data=[], status_code=500,
                                             error_message="Scraping process did not complete successfully.")

        try:
            with SB(
                    uc=True,
                    undetectable=True,
                    locale="en_US",
                    do_not_track=True,
                    incognito=True,
                    proxy=self.proxy_url,
                    # proxy_bypass_list="*",
                    agent=self.selected_user_agent,
                    ad_block=False,
                    disable_csp=False,
                    chromium_arg=[
                        # "--headless=new"    ### make uncomment for docker
                        "--disable-infobars",
                        "--no_sandbox",
                        "--disable_gpu",
                        "--disable-dev-shm-usage",
                        "--window-size=1280,800",
                        "--start-maximized"
                    ],
                    timeout_multiplier=2.0,
                    slow=True,
                    headless=False,
                    browser="chrome"
            ) as sb:

                sb.set_window_size(1280 + random.randint(-100, 100),
                                   720 + random.randint(-50, 50))
                sb.sleep(0.2)
                self.sb = sb

                # Navigate and Search
                if not self._navigate_and_search():
                    logger.error("Navigation or Search phase failed due to locator timeout.")
                    final_response = self.build_response(success=False, data=[], status_code=408,
                                                         error_message="Navigation or Search failed due to locator timeout or missing element.")
                    return final_response

                self._extract_html_and_parse()
                self.sb.sleep(3)

        except Exception as e:
            logger.critical(f"A fatal error occurred during the scraping process: {e}")
            final_response = self.build_response(success=False, data=[], status_code=500,
                                                 error_message=f"A fatal exception occurred: {type(e).__name__}")
            return final_response

        if self.structured_room_data:
            logger.info("Data extraction successful. Returning 200.")
            final_response = self.build_response(success=True, data=self.structured_room_data, status_code=200)
        else:
            logger.warning("Scraping completed, but no room data was extracted.")
            final_response = self.build_response(success=False, data=[], status_code=204,
                                                 error_message="Search successful, but no room data found for the criteria.")
        return final_response


if __name__ == '__main__':
    scraper = ExtractMarriott()

    data = scraper.get_search_data(hotel_id="snabp-courtyard-anaheim-buena-park", check_in_date="2026-01-12",
                                   check_out_date="2026-02-11" , guest_count=1)
    print(json.dumps(data, indent=4))