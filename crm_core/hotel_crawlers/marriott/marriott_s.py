import random
import json
import time
import logging
from datetime import datetime
from seleniumbase import SB
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from mycdp.network import PrivateNetworkRequestPolicy
from urllib.parse import urlparse

# Gracefully handle new Chrome value
try:
    PrivateNetworkRequestPolicy("PermissionBlock")
except ValueError:
    PrivateNetworkRequestPolicy._value2member_map_["PermissionBlock"] = list(PrivateNetworkRequestPolicy)[0]

# import mycdp.util

# _event_parsers = mycdp.util._event_parsers

# def patched_parse_event(data):
#     method = data.get("method")
#     params = data.get("params", {})
#     parser = _event_parsers.get(method)
#
#     if parser is None:
#         # ignore unknown CDP events
#         return None
#
#     return parser.from_json(params)
#
# mycdp.util.parse_json_event = patched_parse_event

import mycdp.util

loggger = logging.getLogger("cdp")

_event_parsers = mycdp.util._event_parsers

def patched_parse_event(data):
    method = data.get("method")
    params = data.get("params", {})

    parser = _event_parsers.get(method)

    if parser is None:
        loggger.debug(f"[CDP] Unknown event ignored: {method}")
        return None

    try:
        return parser.from_json(params)
    except Exception as e:
        loggger.error(f"[CDP] Failed to parse event {method}: {e}")
        return None

# monkey-patch
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

Linux_USER_AGENT_POOL = [
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chromium/142.0.7444.163 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 OPR/125.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.7390.125 Safari/537.36 OPR/125.0.5705.65"
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.7444.59 Safari/537.36",
    # "Mozilla/5.0 (X11; CrOS x86_64 14541.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    # "Mozilla/5.0 (Linux; Ubuntu 24.04) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    # "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    # "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
    # "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.3485.94 Safari/537.36 Edg/140.0.3485.94",
    # "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.4334.67 Safari/537.36 Edg/140.0.4334.67",
    # "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.3022.21 Safari/537.36 Edg/140.0.3022.21",
    # "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.4079.95 Safari/537.36 Edg/139.0.4079.95",
    # "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.2989.82 Safari/537.36 Edg/139.0.2989.82",
    # "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.4812.88 Safari/537.36 Edg/138.0.4812.88",
    # "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.3552.64 Safari/537.36 Edg/138.0.3552.64",
    # "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.2892.70 Safari/537.36 Edg/141.0.2892.70",
    # "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.3767.43 Safari/537.36 Edg/141.0.3767.43",
    # "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.1295.15 Safari/537.36 Edg/140.0.1295.15",
    # "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.3485.94 Safari/537.36 Edg/140.0.3485.94",
    # "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0",
    # "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0",
    # ####NW "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.s0.0.0 Safari/537.36 Edg/138.0.0.0",
    # "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0",
    # "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0",
    # ####NW "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/542.72 (KHTML, like Gecko) Brave/142.0.739.140 Safari/542.72",
    # ####NW "Mozilla/5.0 (X11; Fedora; Linux x86_64) AppleWebKit/542.43 (KHTML, like Gecko) Brave/141.0.4453.55 Safari/542.43",
    # ####NW "Mozilla/5.0 (X11; Ubuntu; Linux i686) AppleWebKit/542.07 (KHTML, like Gecko) Brave/137.0.7048.212 Safari/542.07",
    # ####NW "Mozilla/5.0 (X11; Fedora; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.4200.8293 Brave/111.0.2935.16 Safari/537.36",
    # ####NW "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.9765.9353 Brave/137.0.7740.642 Safari/537.36",
    # ####NW "Mozilla/5.0 (X11; Fedora; Linux x86_64) AppleWebKit/538.51 (KHTML, like Gecko) Brave/140.0.6992.144 Safari/538.51",
    # ####NW "Mozilla/5.0 (X11; Fedora; Linux x86_64) AppleWebKit/540.51 (KHTML, like Gecko) Brave/138.0.2093.219 Safari/540.51",
    # ####NW "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Brave Browser/114.0.5735.127 Safari/537.36",
    # ####SW "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0 Brave Browser/142.1.85.97 Safari/537.36",
    # ####SW "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Brave Browser/110.0.0.0 Safari/537.36",
    # ####NW "Mozilla/5.0 (X11; Ubuntu; Linux i686) AppleWebKit/542.12 (KHTML, like Gecko) Brave/138.0.891.272 Safari/542.12",
    # ####NW "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/542.15 (KHTML, like Gecko) Brave/138.0.165.170 Safari/542.15",
    # ####NW "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/540.02 (KHTML, like Gecko) Brave/138.0.1257.319 Safari/540.02",
    # ####NW "Mozilla/5.0 (X11; Ubuntu; Linux i686) AppleWebKit/542.47 (KHTML, like Gecko) Brave/140.0.1420.39 Safari/542.47",
    # "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
]
Widnows_USER_AGENT_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
#     "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/999.0.0.0 Safari/537.36",
#     "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.9765.9353 Brave/137.0.7740.642 Safari/537.36",
#     "Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Brave Browser/142.0.3595.53 Safari/537.36",
#     "Mozilla/5.0 (Windows NT 12.0; Win64; x64) AppleWebKit/543.24 (KHTML, like Gecko) Brave/137.0.5430.302 Safari/543.24",
#     "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6511.3 Safari/537.36 Brave/1.59.134",
#     "Mozilla/5.0 (Windows NT 12.0; Win64; x64) AppleWebKit/541.79 (KHTML, like Gecko) Brave/138.0.7722.25 Safari/541.79",
#     "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Brave Chrome/86.0.4240.111 Safari/537.36",
#     "Mozilla/5.0 (Windows NT 12.0; Win64; x64) AppleWebKit/542.24 (KHTML, like Gecko) Brave/136.0.2809.10 Safari/542.24",
#     "Mozilla/5.0 (Windows NT 12.0; Win64; x64) AppleWebKit/539.39 (KHTML, like Gecko) Brave/139.0.1483.30 Safari/539.39",
#     "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 OPR/125.0.0.0",
#     "Mozilla/5.0 (Windows NT 10.0; WOW64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 OPR/125.0.0.0",
#     "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.7390.95 Safari/537.36 Edg/141.0.3537.57",
#     "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.7204.169 Safari/537.36 OPR/142.0.7204.169",
#     "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
#     "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
#     "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0"
]

# BASE_URL = "https://www.marriott.com/default.mi"
BASE_URL = "https://www.marriott.com"

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
        self.hotel_id = None
        self.marsha_code = None
        self.user_agent_pool = None
        self.selected_user_agent = None
        self.proxy_url = self._get_proxy()

        # State
        self.structured_room_data = []
        self.sb = None

    def build_response(self, success: bool, data: any, status_code: int):
        return {
            "success": success,
            "data": data,
            "status_code": status_code
        }

    def _get_proxy(self):
        """Fetches the proxy URL from the ProxyManager utility."""
        try:
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
            # self.sb.sleep(0.9)

            def find_elements_with_retry(selector: str, max_retries: int = 1) -> list:
                """
                Attempts to find elements. If none are found, reloads the page
                and tries again up to max_retries times.

                Args:
                    sb: The SeleniumBase SB instance.
                    selector: The CSS selector for the elements (e.g., "div[data-testid='RateCardV2']").
                    max_retries: The number of times to reload and retry after the first failure.

                Returns:
                    A list of web elements found, or an empty list.
                """
                url = self.sb.get_current_url()

                for attempt in range(max_retries + 1):
                    try:
                        # Use sb.find_elements which should return an empty list if nothing is found
                        room_cards = self.sb.find_elements(selector)

                        if len(room_cards) > 0:
                            logger.info(f"Attempt {attempt + 1}: Found {len(room_cards)} room cards.")
                            return room_cards

                        logger.warning(f"Attempt {attempt + 1}: Found 0 room cards for selector '{selector}'.")

                    except TimeoutException:
                        # In some SeleniumBase versions, find_elements might still raise TimeoutException
                        # if the page is unstable. We treat this as a failure.
                        logger.warning(f"Attempt {attempt + 1}: Timeout while searching for elements.")

                    # If we didn't find cards and have retries left, reload the page
                    if attempt < max_retries:
                        logger.info(f"Attempt {attempt + 1} failed. Reloading page and retrying...")
                        self.sb.reload_page()
                        self.sb.wait_for_element_visible(selector, timeout=60)
                        self.sb.scroll_to_bottom()
                        self.sb.sleep(random.uniform(0.3, 0.9))
                        self.sb.scroll_to_top()


                # If all attempts fail, return an empty list
                logger.critical(f"Failed to find elements for selector '{selector}' after {max_retries + 1} attempts.")
                return []

            # SELECT ALL ROOM CARDS
            selector = "div[data-testid='RateCardV2']"
            room_cards = find_elements_with_retry(selector, max_retries=1)
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

    def _parse_room_cards_new_html(self, html_content: str) -> list:
        """Parse Marriott room cards from provided HTML."""
        if not self.sb:
            logger.error("SeleniumBase instance missing")
            return []

        logger.info("Parsing room HTML content...")
        rooms = []

        try:
            self.sb.set_content(html_content)
            # self.sb.sleep(0.9)

            selector = "div.rate-card-container"
            room_cards = self.sb.find_elements(selector)
            logger.info(f"Found {len(room_cards)} room cards.")

            for card in room_cards:
                try:
                    logger.info(f"Parsing card '{card.text}'...")
                    room = {}

                    # Room Name
                    room["title"] = card.find_element(By.CSS_SELECTOR, ".room-desc .room-name").text.strip()

                    # Room Details Link -> extract roomPoolCode
                    try:
                        details_link = card.find_element(By.CSS_SELECTOR, ".room-desc a").get_attribute("href")
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
                        img = card.find_element(By.CSS_SELECTOR, ".image-container picture img").get_attribute("src")
                        room["image_url"] = img
                    except:
                        room["image_url"] = "No Image Found"

                    # Points rate
                    try:
                        points = card.find_element(By.CSS_SELECTOR, ".rate-content .room-rate").text.strip()
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
                   min_delay: float = 0.03, max_delay: float = 0.8,
                   hesitation_chance: float = 0.05):

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
                    time.sleep(random.uniform(0.4, 0.8))

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

        # url = BASE_URL
        url = "https://books.toscrape.com/"
        logger.info(f"Navigating to base URL: {url}")
        try:
            # self.sb.open(url)
            self.sb.activate_cdp_mode(url)
            self.sb.sleep(random.uniform(2.1, 3.6))
        except WebDriverException as e:
            logger.critical(f"Failed to navigate or activate CDP mode. Error: {e}")
            return False

        # only for testing
        try:
            # self.sb.wait_for_element_visible('input[id="downshift-1-input"]', timeout=120)
            logger.info("home page loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Timed out waiting for home page to render after reload. Error: {e}")
            return False

        # try:
        #     self.sb.wait_for_element_visible('input[id="downshift-1-input"]', timeout=120)
        # except Exception as first_error:
        #     logger.info(f"Reloading homepage")
        #     self.sb.reload_page()
        #
        #     try:
        #         self.sb.wait_for_element_visible('input[id="downshift-1-input"]', timeout=120)
        #     except Exception as e:
        #         logger.error(f"Timed out waiting for home page to render after reload. Error: {e}")
        #         return False
        #
        # if not self._safe_click('input[id="downshift-1-input"]', "Destination Input"):
        #     return False
        # self.sb.sleep(random.uniform(0.8, 1.7))
        #
        # if not self._safe_type('input[id="downshift-1-input"]', self.location, "Destination Text"):
        #     return False
        #
        # self.sb.sleep(random.uniform(1.5, 2.9))
        # self.sb.wait_for_element_visible('[role="option"]', timeout=15)
        # self.sb.click('[role="option"]')
        # logger.info("Successfully clicked suggestion")
        # self.sb.sleep(random.uniform(0.8, 1.2))
        #
        # logger.info("Opening calendar...")
        #
        # # self.sb.click("//body")
        # self.sb.sleep(random.uniform(0.9, 1.5))
        #
        # date_input = self.sb.find_element("//input[@aria-label='date-picker']")
        # date_input.click()
        # logger.info("Successfully open calendar")
        # self.sb.sleep(random.uniform(0.9, 1.4))
        #
        # def go_to_month(target_month_year: str):
        #     """
        #     Navigates the calendar forward until the target month/year is visible.
        #     The target_month_year should be in the format 'month year' (e.g., 'january 2026').
        #     """
        #     target = target_month_year.strip().lower()
        #     logger.info(f"Go to month: {target_month_year}")
        #
        #     for _ in range(18):
        #         caps = self.sb.find_elements("//div[@class='DayPicker-Caption']/div")
        #         caps = [c for c in caps if c.text.strip()]
        #
        #         if not caps:
        #             self.sb.sleep(random.uniform(0.7, 0.9))
        #             continue
        #
        #         visible = [c.text.strip().lower() for c in caps]
        #         first = visible[0]
        #
        #         logger.info(f"Visible month caption: {visible}")
        #
        #         if first == target:
        #             logger.info(f"First visible month matched target: {first}")
        #             self.sb.sleep(random.uniform(0.5, 0.8))
        #             self.sb.wait_for_element_visible("//div[contains(@class,'DayPicker-Body')]", timeout=10)
        #             return
        #
        #         next_button = self.sb.find_element("//span[contains(@class,'DayPicker-NavButton--next')]")
        #         self.sb.sleep(random.uniform(0.6, 0.9))
        #         next_button.click()
        #
        #         self.sb.sleep(random.uniform(0.5, 0.8))
        #         self.sb.wait_for_element_visible("//div[contains(@class,'DayPicker-Body')]", timeout=10)
        #         self.sb.sleep(random.uniform(0.3, 0.6))
        #
        #     raise Exception(f"Could not reach month: {target_month_year}")
        #
        #
        # def select_check_in_check_out(check_in_date_label: str, check_out_date_label: str, check_in_month_year,
        #     check_out_month_year):
        #
        #     target_month_year = check_in_month_year
        #
        #     go_to_month(target_month_year)
        #     self.sb.sleep(random.uniform(3.5, 4.6))
        #
        #     # html = self.sb.get_page_source()
        #     # with open("quickbook_debug.html", "w", encoding="utf-8") as f:
        #     #     f.write(html)
        #
        #     logger.info(f"Selecting dates: {check_in_date_label} to {check_out_date_label}")
        #
        #     CHECK_IN_XPATH = f'//div[@aria-label="{check_in_date_label}"]'
        #     CHECK_OUT_XPATH = f'//div[@aria-label="{check_out_date_label}"]'
        #
        #     try:
        #         check_in_element = self.sb.find_element(CHECK_IN_XPATH)
        #         self.sb.sleep(random.uniform(0.7, 0.9))
        #         check_in_element.click()
        #         logger.info(f"Clicked Check-in date: {check_in_date_label}")
        #         self.sb.sleep(random.uniform(0.6, 0.8))
        #
        #         check_out_element = self.sb.find_element(CHECK_OUT_XPATH)
        #         self.sb.sleep(random.uniform(0.9, 1.3))
        #         check_out_element.click()
        #         logger.info(f"Clicked Check-out date: {check_out_date_label}")
        #         self.sb.sleep(random.uniform(0.9, 1.4))
        #
        #
        #         done_button_xpath = "//button[@aria-label='Done']"
        #         self.sb.click(done_button_xpath)
        #         logger.info("Successfully clicked the 'Done' button.")
        #         self.sb.sleep(random.uniform(1.2, 1.7))
        #     except Exception as e:
        #         logger.warning(f"Could not click the 'Done' button: {e}")
        #
        # def convert_date_format(
        #         date_string: str,
        #         input_format: str = "%Y-%m-%d",
        #         output_format: str = "%a %b %d %Y"
        # ) -> str:
        #     """
        #     Converts a date string from one format to another.
        #
        #     Args:
        #         date_string: The original date string (e.g., "2026-01-12").
        #         input_format: The format of the original date string (e.g., "%Y-%m-%d").
        #         output_format: The desired format for the output date string
        #                        (e.g., "%a %b %d %Y" for 'Mon Jan 12 2026').
        #
        #     Returns:
        #         The date string in the new specified format.
        #     """
        #     try:
        #         date_object = datetime.strptime(date_string, input_format)
        #
        #         new_date_str = date_object.strftime(output_format)
        #
        #         return new_date_str
        #
        #     except ValueError as e:
        #         logger.info(f"Error converting date '{date_string}': {e}")
        #         return date_string
        #
        # check_in_date_label = convert_date_format(self.check_in_date)
        # check_out_date_label = convert_date_format(self.check_out_date)
        #
        # check_in_month_year = convert_date_format(self.check_in_date, output_format="%B %Y")
        # check_out_month_year = convert_date_format(self.check_out_date, output_format="%B %Y")
        #
        # select_check_in_check_out(
        #     check_in_date_label,
        #     check_out_date_label,
        #     check_in_month_year,
        #     check_out_month_year
        # )
        #
        # logger.info("Date selection complete.")
        #
        # self.sb.sleep(random.uniform(0.9, 1.4))
        #
        # if not self._safe_click("//label[@for='usepoints-checkbox']", "usepoints-checkbox"):
        #     return False
        # self.sb.sleep(random.uniform(2.1, 3.3))
        #
        # if not self._safe_click("button.update-search-btn", "find hotel button"):
        #     return False
        #
        # self.sb.sleep(random.uniform(2.9, 4.8))
        #
        # self.sb.save_screenshot("list_page.png")
        #
        # PROPERTY_CARD_SELECTOR = 'div.property-card[data-marsha]'
        #
        # try:
        #     self.sb.wait_for_element_visible(PROPERTY_CARD_SELECTOR, timeout=120)
        # except Exception as first_error:
        #     logger.info(f"Reloading listPage")
        #     self.sb.reload_page()
        #
        #     try:
        #         self.sb.wait_for_element_visible(PROPERTY_CARD_SELECTOR, timeout=120)
        #     except Exception as e:
        #         logger.error(f"Timed out waiting for list page to render after reload. Error: {e}")
        #         return False
        #
        # cards = self.sb.find_elements(PROPERTY_CARD_SELECTOR)
        #
        # matched_card = None
        # available_codes = []
        #
        # for card in cards:
        #     code = card.get_attribute("data-marsha")
        #     if code:
        #         code_lower = code.lower()
        #         available_codes.append(code_lower)
        #
        #         if code_lower == self.hotel_id.lower():
        #             matched_card = card
        #
        # self.marsha_code = available_codes
        #
        # if not matched_card:
        #     logger.info(f"Input hotel {self.hotel_id.lower()} not available in listed hotel: {self.marsha_code}")
        #     message = {
        #         "details": f"Input hotel {self.hotel_id.lower()} not available in listed hotel: {self.marsha_code}",
        #     }
        #     return self.build_response(success=False, data=message, status_code=422)
        # else:
        #     logger.info(f"Input hotel {self.hotel_id.lower()} available in listed hotel: {self.marsha_code}")
        #     view_rates_xpath = f'//div[@data-marsha="{self.hotel_id.upper()}"]//a[contains(@class,"view-rates-button-container")]/button'
        #     try:
        #         self.sb.wait_for_element_visible(view_rates_xpath, timeout=120)
        #     except Exception as e:
        #         logger.error(f"Timed out waiting for view rates. Error: {e}")
        #         return False
        #
        #     if not self._safe_click(view_rates_xpath, "view_rates button"):
        #         return False
        #
        #     self.sb.sleep(random.uniform(2.5, 4.9))
        #
        #     ROOMS_LIST_CONTAINER = 'div[data-testid="RateCardV2"], div.rate-card-container'
        #
        #     self.sb.save_screenshot("room_page.png")
        #
        #     try:
        #         self.sb.wait_for_element_visible(ROOMS_LIST_CONTAINER, timeout=120)
        #     except Exception as first_error:
        #         logger.info(f"Reloading roomPage")
        #         self.sb.reload_page()
        #
        #         try:
        #             self.sb.wait_for_element_visible(ROOMS_LIST_CONTAINER, timeout=120)
        #         except Exception as e:
        #             logger.error(f"Timed out waiting for room rates to render after reload. Error: {e}")
        #             return False
        #
        #     logger.info("Clicked 'View Rates' successfully!")
        #     self.sb.sleep(random.uniform(2.1, 3.3))
        #
        #     def slow_scroll(sb, step=600, pause=0.3, max_attempts=900):
        #         """
        #         Improved scroll that goes near the true bottom before stopping.
        #         It waits for multiple scroll height checks to confirm no new content
        #         is loading before stopping.
        #         """
        #
        #         unchanged_height_count = 0
        #         last_height = sb.execute_script("return document.body.scrollHeight")
        #
        #         for _ in range(max_attempts):
        #             sb.execute_script(f"window.scrollBy(0, {step});")
        #             time.sleep(pause)
        #
        #             new_height = sb.execute_script("return document.body.scrollHeight")
        #
        #             if new_height == last_height:
        #                 unchanged_height_count += 1
        #             else:
        #                 unchanged_height_count = 0  # reset because page grew
        #
        #             if unchanged_height_count >= 5:
        #                 break
        #
        #             last_height = new_height
        #
        #     slow_scroll(self.sb)
        #
        #     logger.info("Slow scroll finished. Element is now in view.")
        #     # html = self.sb.get_page_source()
        #     # with open("quickbook_debug.html", "w", encoding="utf-8") as f:
        #     #     f.write(html)
        #
        #     return True

    # def _extract_html_and_parse(self):
    #     """Extracts the entire room list HTML and calls the parser."""
    #
    #     try:
    #         logger.info("Scrolling entire page to load room cards...")
    #
    #         html = self.sb.get_attribute("body", "outerHTML")
    #         logger.info(f"Extracted HTML length: {len(html)}")
    #         page_version = None
    #         if 'rate-card-container' in html:
    #             page_version = "new"
    #         elif 'RateCardV2' in html:
    #             page_version = "old"
    #         else:
    #             logger.error("No valid room layout detected!")
    #
    #         if page_version == "new":
    #             self.structured_room_data = self._parse_room_cards_new_html(html)
    #
    #         if page_version == "old":
    #             self.structured_room_data = self._parse_room_cards_html(html)
    #
    #         logger.info(f"Parsed {len(self.structured_room_data)} rooms.")
    #
    #     except Exception as e:
    #         logger.error(f"Critical HTML extraction error: {e}")
    #         self.structured_room_data = []


    def get_search_data(self, hotel_id, check_in_date, check_out_date, guest_count=1):
        """Main method to run the complete scraping process and return client response."""
        hotel_id_name = hotel_id
        parts = hotel_id_name.split("-", 1)
        hotel_id = parts[0].strip()
        self.hotel_id = hotel_id
        logger.info(f"Hotel ID: {hotel_id}")
        location = parts[1].strip() if len(parts) > 1 else ""
        logger.info(f"Hotel Name: {location}")
        self.location = location
        self.check_in_date = check_in_date
        self.check_out_date = check_out_date
        url = self.proxy_url
        if "://" not in url:
            url = "http://" + url  # add temporary scheme for parsing

        parsed = urlparse(url)
        if "smartproxy" in parsed.hostname:
            host = "smt"
        elif "oxylabs" in parsed.hostname:
            host = "aux"
        else:
            host = "pvt"
        logger.info(f"Using Proxy: {host}:{parsed.port}")
        self.user_agent_pool = Linux_USER_AGENT_POOL
        # self.user_agent_pool = Widnows_USER_AGENT_POOL
        self.selected_user_agent = random.choice(self.user_agent_pool)
        logger.info(f"Using User-Agent: {self.selected_user_agent}")
        message = {
            "details": "Scraping process did not complete successfully.",
        }
        final_response = self.build_response(success=False, data=message, status_code=500)

        try:
            with SB(
                uc=True,
                undetectable=True,
                locale="en_US",
                do_not_track=True,
                incognito=True,
                proxy=self.proxy_url,
                agent=self.selected_user_agent,
                ad_block=True,
                disable_csp=False,
                chromium_arg=[
                    "--headless=new"    ### make uncomment for docker
                    "--disable-infobars",
                    "--no_sandbox",
                    "--disable_gpu",
                    "--disable-dev-shm-usage",
                    "--window-size=1280,800",
                    "--start-maximized",
                    "--uc-cdp-events=false"
                ],
                timeout_multiplier=2.0,
                # slow=True,
                headless=True,
                # disable_cdp_logs=True,
                log_cdp=False,
                # browser="chrome",
                # page_load_strategy="eager"
            ) as sb:

                sb.set_window_size(1280 + random.randint(-100, 100),
                                   720 + random.randint(-50, 50))
                sb.sleep(random.uniform(0.1, 0.2))
                self.sb = sb

                # Navigate and Search
                navigation = self._navigate_and_search()

                if not navigation:
                    logger.error("Navigation or Search phase failed due to locator timeout.")
                    message = {
                        "details": "Navigation or Search failed due to locator timeout or missing element.",
                    }
                    return self.build_response(success=False, data=message, status_code=408)

                # if isinstance(navigation, dict) and not navigation.get("success", True):
                #     logger.error(f"Input hotel {self.hotel_id.lower()} not available in listed hotel: {self.marsha_code}")
                #     message = {
                #         "details": f"Input hotel {self.hotel_id.lower()} not available in listed hotel: {self.marsha_code}",
                #     }
                #     return self.build_response(success=True, data=message, status_code=200)

                logger.info("Navigation successful. Proceeding to extract HTML...")
                message = {
                        "details": "Home page found successfully.",
                    }
                return self.build_response(success=True, data=message, status_code=200)
                # self._extract_html_and_parse()
                # self.sb.sleep(random.uniform(0.5, 2.3))

        except Exception as e:
            logger.critical(f"A fatal error occurred during the scraping process: {e}")
            message = {
                "details": f"A fatal exception occurred: {type(e).__name__}",
            }
            return self.build_response(success=False, data=message, status_code=500)

        # if self.structured_room_data:
        #     logger.info("Data extraction successful. Returning 200.")
        #     return self.build_response(success=True, data=self.structured_room_data, status_code=200)
        # else:
        #     logger.warning("Scraping completed, but no room data was extracted.")
        #     message = {
        #         "details": "Search successful, but no room data found for the criteria.",
        #     }
        #     return self.build_response(success=True, data=message, status_code=200)


if __name__ == '__main__':
    scraper = ExtractMarriott()

    data = scraper.get_search_data(hotel_id="laxbp-courtyard-los-angeles-baldwin-park", check_in_date="2026-01-26",
                                   check_out_date="2026-01-28" , guest_count=1)
    print(json.dumps(data, indent=4))