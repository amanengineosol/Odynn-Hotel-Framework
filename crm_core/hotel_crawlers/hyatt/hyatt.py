import random
import json
import time
import logging

import sbase.steps
from seleniumbase import SB
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# --- SETUP LOGGING ---
# Configure the logger for the module
logger = logging.getLogger('HyattScraper')
logger.setLevel(logging.DEBUG)

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
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
]
# USER_AGENT_POOL = [
#     "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
# ]
# DEFAULT_CHECK_IN_DATE = '2025-11-11'
# DEFAULT_CHECK_OUT_DATE = '2025-11-14'
BASE_URL = "https://www.hyatt.com/loyalty/en-US"


# Note: ProxyManager import is assumed to be working locally:
# from proxy_manager import ProxyManager

class HyattScraper:
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
        logger.debug(f"Using User-Agent: {self.selected_user_agent}")
        logger.debug(f"Using Proxy: {self.proxy_url}")

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
        """Parses the raw room card HTML content into structured data."""
        if not self.sb:
            logger.error("SeleniumBase instance is not initialized for parsing.")
            return []

        logger.info("Starting HTML content parsing...")
        structured_data = []

        try:
            self.sb.set_content(html_content)
            self.sb.sleep(0.5)

            room_cards = self.sb.find_elements(".room-rate-card-wrapper")
            logger.info(f"Found {len(room_cards)} room cards for parsing.")

            for card in room_cards:
                room = {}
                try:
                    # 1. Room Type Code
                    room['room_type_code'] = card.get_attribute("data-room-type-code") or 'N/A'
                    # 2. Room Title
                    room['title'] = card.find_element(By.CSS_SELECTOR, ".room-title").text
                    # 3. Description
                    room['description'] = card.find_element(By.CSS_SELECTOR, ".truncate-text.room_description").text
                    # 4. Image URL
                    try:
                        room['image_url'] = card.find_element(By.CSS_SELECTOR,".room-card-carousel-wrapper img").get_attribute("src")
                    except NoSuchElementException:
                        room['image_url'] = 'No Image Found'
                        logger.debug(f"No image found for room code: {room['room_type_code']}")
                    # 5. Rate Type
                    room['rate_type'] = card.find_element(By.CSS_SELECTOR,".room-rate-content.points-rate span.b-col-7").text
                    # 6. Rate Value
                    room['point_value'] = card.find_element(By.CSS_SELECTOR,".room-rate-content.points-rate > span:last-child").text

                    structured_data.append(room)
                except Exception as e:
                    logger.warning(f"Failed to parse a room card. Skipping. Error: {e}")
                    continue

        except Exception as e:
            logger.error(f"Critical error during HTML parsing setup: {e}")
            structured_data = []

        self.sb.set_content("")  # Clear temporary content
        logger.info("HTML parsing complete.")
        return structured_data

    def _safe_click(self, selector: str, description: str, sleep_time: float = 1.0):
        """Wrapper for sb.click with robust exception handling for timeouts."""
        try:
            self.sb.click(selector)
            logger.debug(f"Successfully clicked: {description} ({selector})")
            self.sb.sleep(sleep_time)
            return True
        except TimeoutException:
            logger.error(f"Timeout clicking element: {description} ({selector}). Page state check needed.")
            return False
        except Exception as e:
            logger.error(f"General error clicking element: {description} ({selector}). Error: {e}")
            return False

    def _safe_type(self, selector: str, text: str, description: str, sleep_time: float = 1.0):
        """Wrapper for sb.type with robust exception handling for timeouts."""
        try:
            self.sb.type(selector, text)
            logger.debug(f"Successfully typed '{text}' into: {description} ({selector})")
            self.sb.sleep(sleep_time)
            return True
        except TimeoutException:
            logger.error(f"Timeout typing into element: {description} ({selector}).")
            return False
        except Exception as e:
            logger.error(f"General error typing into element: {description} ({selector}). Error: {e}")
            return False

    def _navigate_and_search(self):
        """Handles browser navigation, element interaction, and search execution."""

        # 1. Navigate and setup
        url = BASE_URL
        logger.info(f"Navigating to base URL: {url}")
        try:
            self.sb.activate_cdp_mode(url)
            self.sb.sleep(3.5)
        except WebDriverException as e:
            logger.critical(f"Failed to navigate or activate CDP mode. Check network/proxy. Error: {e}")
            return self.build_response(success=False, data=None,status_code= 503, error_message="Navigation failed. Check browser setup or network.")

        # 2. Handle popups and cookies
        self.sb.save_screenshot("initial_page_load.png")
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
        logger.info("Clicking 'Find Hotels' button...")
        if not self._safe_click("button.be-button-shop", "Find Hotels Button", sleep_time=6): return False

        # 7. Ensure all rooms are loaded by scrolling
        logger.info("Scrolling to ensure dynamic content loads...")
        self.sb.scroll_to_bottom()
        self.sb.sleep(5)
        return True

    def _extract_html_and_parse(self):
        """Extracts the target HTML and calls the parser method."""
        SCROLL_TARGET_ID = "#room-cards-section-panel"
        HTML_EXTRACTION_SELECTOR = "#room-cards-section-panel .room-cards"
        room_cards_html = None

        try:
            logger.info(f"Attempting to scroll to final target: {SCROLL_TARGET_ID}")
            # Use slow scroll to ensure the element is loaded/visible
            self.sb.slow_scroll_to(SCROLL_TARGET_ID)
            logger.info("Successfully scrolled to the room cards section.")
            self.sb.sleep(3)

            # Get the HTML content of the target element
            room_cards_html = self.sb.get_attribute(HTML_EXTRACTION_SELECTOR, "outerHTML")
            logger.info(f"Successfully retrieved HTML. Length: {len(room_cards_html)} characters.")

            # PARSING STEP
            if room_cards_html:
                self.structured_room_data = self._parse_room_cards_html(room_cards_html)
                logger.info(f"Parsed {len(self.structured_room_data)} structured room entries.")

        except (TimeoutException, NoSuchElementException) as e:
            logger.error(f"HTML extraction failed. Element '{SCROLL_TARGET_ID}' not found after scroll. Error: {e}")
            # Do not re-raise, allow flow to continue to return empty data

        except Exception as e:
            logger.critical(f"Critical error during HTML extraction: {e}")
            # Do not re-raise, allow flow to continue to return empty data

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
        final_response = self.build_response(success=False, data=[], status_code=500, error_message="Scraping process did not complete successfully.")

        try:
            # Initialize SeleniumBase
            with SB(
                    uc=True,
                    test=True,
                    locale="en",
                    ad_block=True,
                    incognito=True,
                    proxy = self.proxy_url,
                    agent=self.selected_user_agent,
                    headless=True,
            ) as sb:
                self.sb = sb

                # Navigate and Search
                if not self._navigate_and_search():
                    logger.info(f"Using {self.proxy_url} to navigate")
                    logger.error("Navigation or Search phase failed due to locator timeout.")
                    final_response = self.build_response(success=False, data=[], status_code=408, error_message="Navigation or Search failed due to locator timeout or missing element.")
                    return final_response

                # Extract and Parse
                self._extract_html_and_parse()

                # Final sleep before closing the browser
                self.sb.sleep(3)

        except Exception as e:
            # Catches exceptions during SB initialization or in the `with` block
            logger.critical(f"A fatal error occurred during the scraping process: {e}")
            final_response = self.build_response(success=False, data=[], status_code=500, error_message=f"A fatal exception occurred: {type(e).__name__}")
            return final_response

        # Build Final Successful/Unsuccessful Response
        if self.structured_room_data:
            logger.info("Data extraction successful. Returning 200.")
            final_response = self.build_response(success=True, data= self.structured_room_data, status_code=200)
        else:
            logger.warning("Scraping completed, but no room data was extracted.")
            final_response = self.build_response(success=False, data=[], status_code=204, error_message="Search successful, but no room data found for the criteria.")

        return final_response


# --- EXECUTION ---

if __name__ == '__main__':
    scraper = HyattScraper()

    data = scraper.get_search_data(hotel_id="ancza-Hyatt Place Edmonton-West", check_in_date="2025-11-12", check_out_date="2025-11-14")
    print("\n--- FINAL CLIENT RESPONSE ---")
    print(json.dumps(data, indent=4))
    