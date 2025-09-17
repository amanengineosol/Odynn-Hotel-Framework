from .proxy_manager import ProxyManager
from datetime import datetime, timedelta
from .random_user_agent import get_random_sec_ch_headers, USER_AGENT
import requests
import json
import re
import logging
import time
from requests.exceptions import ProxyError, ConnectionError, Timeout, HTTPError
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def handle_response_status(response, context=""):
    status = response.status_code
    if 200 <= status < 300:
        logger.info(f"{context} - Success: HTTP {status}")
        return True
    if status == 400:
        logger.error(f"{context} - Bad Request (400)")
    elif status == 401:
        logger.error(f"{context} - Unauthorized (401)")
    elif status == 403:
        logger.error(f"{context} - Forbidden (403)")
    elif status == 404:
        logger.error(f"{context} - Not Found (404)")
    elif status == 429:
        logger.warning(f"{context} - Too Many Requests (429) - Rate limited")
    elif 500 <= status < 600:
        logger.error(f"{context} - Server Error ({status})")
    else:
        logger.warning(f"{context} - Unexpected HTTP status {status}")
    return False


class ExtractMarriott:
    def __init__(self):
        self._proxy_fetcher = ProxyManager()
        # self._headers_obj = get_random_sec_ch_headers(USER_AGENT)


    def build_response(self, success: bool, data, status_code: int):
        return {
            "Success": success,
            "data": data,
            "status_code": status_code
        }

    def get_search_data(self, hotel_id, check_in_date, check_out_date, guest_count,
                        max_retries=3, backoff_factor=2):
        hotel_name_original = hotel_id
        hotel_id = hotel_name_original.split('-')[0]

        # Validate inputs
        try:
            if not hotel_id:
                raise ValueError("Hotel ID is empty after parsing.")
            check_in = datetime.strptime(check_in_date, "%Y-%m-%d")
            check_out = datetime.strptime(check_out_date, "%Y-%m-%d")

            check_in_dd = check_in.strftime("%d")
            check_in_mm = check_in.strftime("%m")
            check_in_yyyy = check_in.strftime("%Y")

            check_out_dd = check_out.strftime("%d")
            check_out_mm = check_out.strftime("%m")
            check_out_yyyy = check_out.strftime("%Y")

            length_of_stay = (check_out - check_in).days
            if length_of_stay <= 0:
                raise ValueError("Check-out date must be after check-in date.")
            if guest_count <= 0:
                raise ValueError("Guest count must be positive.")
        except Exception as e:
            logger.error(f"Input validation error: {e}")
            return self.build_response(False, str(e), 400)

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Attempt {attempt}: Fetching proxy for session")
                proxy_url = self._proxy_fetcher.fetch_proxy()
                browser_family, headers = get_random_sec_ch_headers(USER_AGENT)
                while browser_family not in ("chromium", "firefox"):
                    browser_family, headers = get_random_sec_ch_headers(USER_AGENT)
                # self._headers = headers
                if not proxy_url:
                    raise Exception("Proxy url not retrieved from the server")

                proxies = {'http': proxy_url, 'https': proxy_url}
                session = requests.Session()
                session.proxies.update(proxies)
                session.headers.update(headers)
                print(session.headers)

                # 1. Homepage
                url_home = "https://www.marriott.com/default.mi"
                resp1 = session.get(url_home, timeout=10)
                print(resp1.status_code)
                if not handle_response_status(resp1, "1 - Home_Page"):
                    return self.build_response(False, f"Homepage request failed", resp1.status_code)

                # 2. JS Page
                ref_url = f"https://www.marriott.com/en-us/hotels/{hotel_name_original}/overview/"
                url_js = "https://www.marriott.com/etc.clientlibs/mcom-hws/clientlibs/clientlib-sitev2.min.25dfc6cf6a8b94135a28f9b03e6ed02d.js"
                headers_js = {
                    'accept': '*/*',
                    'sec-fetch-site': 'same-origin',
                    'sec-fetch-mode': 'no-cors',
                    'sec-fetch-dest': 'script',
                    'referer': ref_url,
                    'accept-language': 'en-US,en;q=0.9'
                }
                resp3 = session.get(url_js, headers=headers_js, timeout=10)
                print(resp3.status_code)
                if not handle_response_status(resp3, "3 - JS_Page"):
                    return self.build_response(False, f"JS page request failed", resp3.status_code)

                pattern_phoenix_hws = r':"([^"]+)","apollographql-client-version":"v1","apollographql-client-name":"phoenix_hws"'
                match = re.search(pattern_phoenix_hws, resp3.text)
                if not match:
                    raise Exception("Phoenix HWS signature not found in JS response.")
                phoenix_hws_signature = match.group(1)

                # 3. Standard Form (GraphQL)
                url_gql = "https://www.marriott.com/mi/query/phoenixHWSLAR"
                current_date = datetime.today().strftime("%Y-%m-%d")
                next_day_date = (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d")
                payload_gql = json.dumps({
                    "query": "...(your existing query here)...",
                    "variables": {
                        "search": {
                            "ids": [hotel_id.upper()],
                            "options": {
                                "startDate": current_date,
                                "endDate": next_day_date,
                                "includeTaxesAndFees": True,
                                "quantity": 1,
                                "numberInParty": guest_count,
                                "rateRequestTypes": [{"type": "STANDARD", "value": ""}],
                                "includeMandatoryFees": True
                            }
                        }
                    }
                })
                headers_gql = {
                    'x-request-id': '',
                    'accept-language': 'en-us',
                    'graphql-operation-signature': phoenix_hws_signature,
                    'apollographql-client-version': 'v1',
                    'content-type': 'application/json',
                    'apollographql-client-name': 'phoenix_hws',
                    'accept': '*/*',
                    'origin': 'https://www.marriott.com',
                    'sec-fetch-site': 'same-origin',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-dest': 'empty',
                    'referer': ref_url
                }
                resp4 = session.post(url_gql, headers=headers_gql, data=payload_gql, timeout=15)
                print(resp4.status_code)
                if not handle_response_status(resp4, "4 - Standard_Form_Page"):
                    return self.build_response(False, f"Standard form page request failed", resp4.status_code)

                if "Invalid Property Code" in resp4.text:
                    logger.error("Property Code is invalid.")
                    return self.build_response(False, "Property Code is invalid.", resp4.status_code)

                # 4. Submit Form Page
                url_submit_form = f"https://www.marriott.com/reservation/availabilitySearch.mi?destinationAddress.country=&lengthOfStay={length_of_stay}&fromDate={check_in_mm}%2F{check_in_dd}%2F{check_in_yyyy}&toDate={check_out_mm}%2F{check_out_dd}%2F{check_out_yyyy}&numberOfRooms=1&numberOfAdults={guest_count}&guestCountBox={guest_count}+Adults+Per+Room&childrenCountBox=0+Children+Per+Room&roomCountBox=1+Rooms&childrenCount=0&childrenAges=&clusterCode=none&corporateCode=&groupCode=&isHwsGroupSearch=true&propertyCode={hotel_id.upper()}&useRewardsPoints=true&flexibleDateSearch=false&t-start={check_in_mm}%2F{check_in_dd}%2F{check_in_yyyy}&t-end={check_out_mm}%2F{check_out_dd}%2F{check_out_yyyy}&fromDateDefaultFormat={check_in_mm}%2F{check_in_dd}%2F{check_in_yyyy}&toDateDefaultFormat={check_out_mm}%2F{check_out_dd}%2F{check_out_yyyy}&fromToDate_submit={check_out_mm}%2F{check_out_dd}%2F{check_out_yyyy}&fromToDate="
                print(url_submit_form)
                headers_submit = {
                    'upgrade-insecure-requests': '1',
                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'sec-fetch-site': 'same-origin',
                    'sec-fetch-mode': 'navigate',
                    'sec-fetch-user': '?1',
                    'sec-fetch-dest': 'document',
                    'referer': ref_url,
                    'accept-language': 'en-US,en;q=0.9'
                }
                resp5 = session.get(url_submit_form, headers=headers_submit, timeout=25)
                print(resp5.status_code)
                if resp5.status_code == 403:
                    logger.warning("Cookies failed at form submission page.")
                    if attempt + 1 < max_retries:
                        retry_result = self.get_search_data(hotel_id, check_in_date, check_out_date, guest_count)
                        attempt = attempt + 1
                        if retry_result['status_code'] == 200:
                            return retry_result
                        elif attempt + 1 < max_retries:
                            continue
                    else:
                        raise Exception("Failed after retries (form submission).")

                if not handle_response_status(resp5, "5 - Submit_Form_Page"):
                    return self.build_response(False, f"Submit form page request failed", resp5.status_code)

                # 5. Next JS Page
                url_next_js = "https://www.marriott.com/mi-assets/mi-static/mi-book-renderer/phx-rel-R25.8.2-12aug20259pmist/_next/static/chunks/2424-b7ef29505ec20836.js"
                headers_next_js = {
                    'accept': '*/*',
                    'sec-fetch-site': 'same-origin',
                    'sec-fetch-mode': 'no-cors',
                    'sec-fetch-dest': 'script',
                    'referer': 'https://www.marriott.com/reservation/rateListMenu.mi',
                    'accept-language': 'en-US,en;q=0.9'
                }
                resp7 = session.get(url_next_js, headers=headers_next_js, timeout=15)
                print(resp7.status_code)
                if not handle_response_status(resp7, "7 - Next_JS_Page"):
                    return self.build_response(False, f"Next JS page request failed", resp7.status_code)

                pattern_sig_search = r'"operationName":"PhoenixBookSearchProductsByProperty","signature":"([^"]+)"'
                match_sig_search = re.search(pattern_sig_search, resp7.text)
                signature_search = match_sig_search.group(1) if match_sig_search else None

                if not signature_search:
                    logger.error("Signature for PhoenixBookSearchProductsByProperty not found.")
                    return self.build_response(False, "Required operation signature not found in JS.", 500)

                # 6. Promotional Rate Page
                url_promotional = "https://www.marriott.com/mi/query/PhoenixBookSearchProductsByProperty"
                payload_promo = json.dumps({
                    "operationName": "PhoenixBookSearchProductsByProperty",
                    "variables": {
                        "search": {
                            "options": {
                                "startDate": check_in_date,
                                "endDate": check_out_date,
                                "quantity": 1,
                                "numberInParty": guest_count,
                                "childAges": [],
                                "productRoomType": ["ALL"],
                                "productStatusType": ["AVAILABLE"],
                                "rateRequestTypes": [
                                    {"value": "", "type": "STANDARD"},
                                    {"value": "", "type": "PREPAY"},
                                    {"value": "", "type": "PACKAGES"},
                                    {"value": "MRM", "type": "CLUSTER"},
                                    {"value": "", "type": "REDEMPTION"},
                                    {"value": "", "type": "REGULAR"}
                                ],
                                "isErsProperty": True,
                            },
                            "propertyId": hotel_id.upper(),
                        },
                        "offset": 0,
                        "limit": None
                    },
                    "query": """query PhoenixBookSearchProductsByProperty($search: ProductByPropertySearchInput, $offset: Int, $limit: Int) {
                                  searchProductsByProperty(search: $search, offset: $offset, limit: $limit) {
                                    edges {
                                      node {
                                        ... on HotelRoom {
                                          availabilityAttributes {
                                            rateCategory { type { code } value }
                                            isNearSellout
                                          }
                                          rates {
                                            name
                                            description
                                            rateAmounts {
                                              amount {
                                                origin { amount currency valueDecimalPoint }
                                              }
                                              points
                                              pointsSaved
                                              pointsToPurchase
                                            }
                                            localizedDescription { translatedText }
                                            localizedName { translatedText }
                                            rateAmountsByMode { averageNightlyRatePerUnit { amount { origin { value }}}}
                                          }
                                          basicInformation {
                                            type
                                            name
                                            localizedName { translatedText }
                                            description
                                            membersOnly
                                            oldRates
                                            representativeRoom
                                            housingProtected
                                            actualRoomsAvailable
                                            depositRequired
                                            roomsAvailable
                                            roomsRequested
                                            ratePlan { ratePlanType ratePlanCode }
                                            freeCancellationUntil
                                          }
                                          roomAttributes { attributes { id description groupID category { code description } accommodationCategory { code description }}}
                                          totalPricing { quantity rateAmountsByMode { grandTotal { amount { origin { value }}} subtotalPerQuantity { amount { origin { value }}} totalMandatoryFeesPerQuantity { amount { origin { value }}}}}
                                          id
                                        }
                                        id
                                      }
                                    }
                                    total
                                    status {
                                      ... on UserInputError {
                                        httpStatus
                                        messages { user { message field } }
                                      }
                                      ... on DateRangeTooLongError {
                                        httpStatus
                                        messages { user { message field } }
                                      }
                                    }
                                  }
                                }"""
                })
                headers_promo = {
                    'application-name': 'book',
                    'x-request-id': '',
                    'graphql-operation-name': 'PhoenixBookSearchProductsByProperty',
                    'graphql-force-safelisting': 'true',
                    'accept': '*/*',
                    'apollographql-client-version': '1',
                    'content-type': 'application/json',
                    'apollographql-client-name': 'phoenix_book',
                    'graphql-require-safelisting': 'true',
                    'accept-language': 'en-US',
                    'graphql-operation-signature': signature_search,
                    'origin': 'https://www.marriott.com',
                    'sec-fetch-site': 'same-origin',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-dest': 'empty',
                    'referer': 'https://www.marriott.com/reservation/rateListMenu.mi'
                }
                resp10 = session.post(url_promotional, headers=headers_promo, data=payload_promo, timeout=20)
                print(resp10.status_code)
                if resp10.status_code == 403:
                    logger.warning("Cookies failed at promo page.")
                    if attempt + 1 < max_retries:
                        retry_result  = self.get_search_data(hotel_id, check_in_date, check_out_date, guest_count)
                        attempt = attempt + 1
                        if retry_result['status_code'] == 200:
                            return retry_result
                        elif attempt + 1 < max_retries:
                            continue
                    else:
                        raise Exception("Failed after retries (promo API).")
                if not handle_response_status(resp10, "10 - Promotional_Rate_Page"):
                    return self.build_response(False, f"Promotional rate page request failed", resp10.status_code)

                if "\"Invalid Property Code\"" in resp10.text:
                    logger.error("Property Code is invalid.")
                    return self.build_response(False, "Property Code is invalid.", resp10.status_code)

                if '"code":"standard"' in resp10.text and '"code":"redemption"' not in resp10.text:
                    logger.error("No redemption rates available for selected dates.")
                    return self.build_response(False, "No redemption rates available for selected dates.",
                                               resp10.status_code)

                # Return final JSON response in generic format
                return self.build_response(True, resp10.json(), resp10.status_code)

            except (ProxyError, ConnectionError, Timeout) as e:
                logger.warning(f"Network/Proxy error on attempt {attempt}: {e}")
                if attempt < max_retries:
                    sleep_time = backoff_factor ** attempt
                    logger.info(f"Retrying after {sleep_time} seconds...")
                    time.sleep(sleep_time)
                else:
                    logger.error(f"Max retries reached. Last error: {e}")
                    return self.build_response(False, "Network or proxy error, unable to fetch data.", 503)
            except HTTPError as e:
                logger.error(f"HTTP error: {e.response.status_code} - {e.response.reason}")
                return self.build_response(False, f"HTTP error {e.response.status_code}", e.response.status_code)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                return self.build_response(False, "Failed to parse JSON response.", 500)
            except Exception as e:
                logger.error(f"Unexpected error: {e}", exc_info=True)
                return self.build_response(False, "Unexpected error occurred.", 500)
