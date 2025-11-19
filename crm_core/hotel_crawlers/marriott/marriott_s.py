import base64
import requests
import json
import re
import logging
from .proxy_manager import ProxyManager
from datetime import datetime, timedelta
from .random_user_agent import get_random_sec_ch_headers, USER_AGENT
import quote

# ---------------- Log configuration ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("marriott.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
logger.info("Starting application...")


class ExtractMarriott:
    def __init__(self):
        self._proxy_fetcher = ProxyManager()
        browser_family, headers = get_random_sec_ch_headers(USER_AGENT)
        while browser_family not in ("chromium", "firefox"):
            browser_family, headers = get_random_sec_ch_headers(USER_AGENT)
        self._headers = headers


    def build_response(self, success: bool, data: any, status_code: int):
        return {
            "success": success,
            "data": data,
            "status_code": status_code
        }

    def get_search_data(self, hotel_id, check_in_date, check_out_date, guest_count, max_retries=3):
        logger.info("Getting proxy IP for current session")
        _proxy_url = self._proxy_fetcher.fetch_proxy()
        if not _proxy_url:
            message = "Proxy url not retrieved from the server"
            return self.build_response(success=False, data=message, status_code=101)

        proxies = {
            'http': _proxy_url,
            'https': _proxy_url
        }

        logger.info("Proxy url dict created for request")
        logger.info("Setting up crawler to extract data")

        session = requests.Session()
        session.proxies.update(proxies)
        session.headers.update(self._headers)

        # Validate inputs
        current_date = datetime.today().strftime("%Y-%m-%d")
        next_day_date = (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        check_in = datetime.strptime(check_in_date, "%Y-%m-%d")
        check_out = datetime.strptime(check_out_date, "%Y-%m-%d")
        check_in_dd = check_in.strftime("%d")
        check_in_mm = check_in.strftime("%m")
        check_in_yyyy = check_in.strftime("%Y")

        check_out_dd = check_out.strftime("%d")
        check_out_mm = check_out.strftime("%m")
        check_out_yyyy = check_out.strftime("%Y")
        length_of_stay = (check_out - check_in).days
        if not hotel_id or length_of_stay <= 0 or guest_count <= 0:
            raise ValueError("hotel_id/no_of_stays/guest must have valid values.")

        hotel_id_name = hotel_id
        parts = hotel_id_name.split("-", 1)
        hotel_id = parts[0].strip()
        logger.info(f"Hotel ID: {hotel_id}")
        hotel_name = parts[1].strip() if len(parts) > 1 else ""
        logger.info(f"Hotel Name: {hotel_name}")

        # ---- Retry mechanism ----
        int_count = 1
        for icount in range(3):
            is_all_requests_passed = True

            try:

                # ---------- 1: Marriott Homepage ----------
                url = "https://www.marriott.com/"
                session.headers.update({
                    'upgrade-insecure-requests': '1',
                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'sec-fetch-site': 'same-origin',
                    'sec-fetch-mode': 'navigate',
                    'sec-fetch-user': '?1',
                    'sec-fetch-dest': 'document',
                    'accept-language': 'en-US,en;q=0.9'
                })
                resp1 = session.get(url)
                logger.info(f"1 - Home_Page: {resp1.status_code}")

                # ---------- 2: Hotel page ----------
                ref_url = f"https://www.marriott.com/en-us/hotels/{hotel_id_name}/overview/"

                # ---------- 3: JS page ----------
                url = "https://www.marriott.com/etc.clientlibs/mcom-hws/clientlibs/clientlib-sitev2.min.6ad258637c239cff460e0f2a987c0e8d.js"
                headers = {
                    'accept': '*/*',
                    'sec-fetch-site': 'same-origin',
                    'sec-fetch-mode': 'no-cors',
                    'sec-fetch-dest': 'script',
                    'referer': ref_url,
                    'accept-language': 'en-US,en;q=0.9'
                }
                resp3 = session.get(url, headers=headers)
                logger.info(f"3 - JS_Page: {resp3.status_code}")

                pattern_phoenix_hws = r':"([^"]+)","apollographql-client-version":"v1","apollographql-client-name":"phoenix_hws"'
                match_phoenix_hws = re.search(pattern_phoenix_hws, resp3.text)

                if match_phoenix_hws:
                    phoenix_hws_signature = match_phoenix_hws.group(1)
                    logger.info(f"phoenix_hws_signature: {phoenix_hws_signature}")

                    # ---------- 4: Standard hotel form page ----------
                url = "https://www.marriott.com/mi/query/phoenixHWSLAR"
                payload = json.dumps({
                    "query": "\n    query phoenixHWSLAR($search: LowestAvailableRatesPropertyIdsSearchInput) {\n        searchLowestAvailableRatesByPropertyIds(search: $search) {\n            edges {\n                node {\n                    property {\n                        id\n                        basicInformation {\n                            name\n                            __typename\n                        }\n                        __typename\n                    }\n                    rates {\n                        rateAmounts {\n                            amount {\n                                origin {\n                                    currency\n                                    value\n                                    valueDecimalPoint\n                                    __typename\n                                }\n                                locale {\n                                    currency\n                                    value\n                                    valueDecimalPoint\n                                    __typename\n                                }\n                                __typename\n                            }\n                            points\n                            mandatoryFees {\n                                origin {\n                                    valueDecimalPoint\n                                    value\n                                    currency\n                                    __typename\n                                }\n                                locale {\n                                    currency\n                                    value\n                                    valueDecimalPoint\n                                    __typename\n                                }\n                                __typename\n                            }\n                            amountPlusMandatoryFees {\n                                locale {\n                                    currency\n                                    value\n                                    valueDecimalPoint\n                                    __typename\n                                }\n                                origin {\n                                    currency\n                                    value\n                                    valueDecimalPoint\n                                    __typename\n                                }\n                                __typename\n                            }\n                            totalAmount {\n                                origin {\n                                    currency\n                                    value\n                                    valueDecimalPoint\n                                    __typename\n                                }\n                                locale {\n                                    currency\n                                    value\n                                    valueDecimalPoint\n                                    __typename\n                                }\n                                __typename\n                            }\n                            rateMode {\n                                code\n                                label\n                                description\n                                __typename\n                            }\n                            __typename\n                        }\n                        rateCategory {\n                            type {\n                                code\n                                label\n                                description\n                                __typename\n                            }\n                            value\n                            __typename\n                        }\n                        status {\n                            code\n                            description\n                            __typename\n                        }\n                        __typename\n                    }\n                    __typename\n                }\n                __typename\n            }\n            __typename\n        }\n    }\n",
                    "variables": {
                        "search": {
                            "ids": [
                                hotel_id.upper()
                            ],
                            "options": {
                                "startDate": current_date,
                                "endDate": next_day_date,
                                "includeTaxesAndFees": True,
                                "quantity": 1,
                                "numberInParty": guest_count,
                                "rateRequestTypes": [
                                    {
                                        "type": "STANDARD",
                                        "value": ""
                                    }
                                ],
                                "includeMandatoryFees": True
                            }
                        }
                    }
                })
                headers = {
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
                resp4 = session.post(url, headers=headers, data=payload)
                logger.info(f"4 - Standard_Form_Page: {resp4.status_code}")
                if "Invalid Property Code" in resp4.text:
                    logging.error("Property Code is invalid.")
                    return ("Property Code is invalid.")

                # # ---------- 5: Submit form page ----------
                # url = f"https://www.marriott.com/reservation/availabilitySearch.mi?destinationAddress.country=&lengthOfStay={length_of_stay}&fromDate={check_in_mm}%2F{check_in_dd}%2F{check_in_yyyy}&toDate={check_out_mm}%2F{check_out_dd}%2F{check_out_yyyy}&numberOfRooms=1&numberOfAdults={guest_count}&guestCountBox={guest_count}+Adults+Per+Room&childrenCountBox=0+Children+Per+Room&roomCountBox=1+Rooms&childrenCount=0&childrenAges=&clusterCode=none&corporateCode=&groupCode=&isHwsGroupSearch=true&propertyCode={hotel_id.upper()}&useRewardsPoints=true&flexibleDateSearch=false&t-start={check_in_mm}%2F{check_in_dd}%2F{check_in_yyyy}&t-end={check_out_mm}%2F{check_out_dd}%2F{check_out_yyyy}&fromDateDefaultFormat={check_in_mm}%2F{check_in_dd}%2F{check_in_yyyy}&toDateDefaultFormat={check_out_mm}%2F{check_out_dd}%2F{check_out_yyyy}&fromToDate_submit={check_out_mm}%2F{check_out_dd}%2F{check_out_yyyy}&fromToDate="
                # headers = {
                #     'upgrade-insecure-requests': '1',
                #     'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                #     'sec-fetch-site': 'same-origin',
                #     'sec-fetch-mode': 'navigate',
                #     'sec-fetch-user': '?1',
                #     'sec-fetch-dest': 'document',
                #     'referer': ref_url,
                #     'accept-language': 'en-US,en;q=0.9'
                # }
                # resp5 = session.get(url, headers=headers)
                # logger.info(f"5 - Submit_Form_Page: {resp5.status_code}")
                # if ">0 Results" in resp5.text:
                #     logging.error("There are no redemption rates available for the dates you selected.")
                #     return ("There are no redemption rates available for the dates you selected.")
                # print(resp5.text)

                # ---------- 7: Next JS Page ----------
                url = "https://www.marriott.com/mi-assets/mi-static/mi-book-renderer/phx-rel-r25.9.4-21sep20259amist/_next/static/chunks/52211-9cb7f5ca7f77ffba.js"
                headers = {
                    'accept': '*/*',
                    'sec-fetch-site': 'same-origin',
                    'sec-fetch-mode': 'no-cors',
                    'sec-fetch-dest': 'script',
                    'referer': 'https://www.marriott.com/reservation/rateListMenu.mi',
                    'accept-language': 'en-US,en;q=0.9'
                }
                resp7 = session.get(url, headers=headers)
                logger.info(f"7 - Next_JS_Page: {resp7.status_code}")

                pattern_PhoenixBookProperty = r'"operationName":"PhoenixBookProperty","signature":"([^"]+)"'
                match_PhoenixBookProperty = re.search(pattern_PhoenixBookProperty, resp7.text)

                if match_PhoenixBookProperty:
                    signature_PhoenixBookProperty = match_PhoenixBookProperty.group(1)

                pattern_PhoenixBookSearchProductsByProperty = r'"operationName":"PhoenixBookSearchProductsByProperty","signature":"([^"]+)"'
                match_PhoenixBookSearchProductsByProperty = re.search(pattern_PhoenixBookSearchProductsByProperty,
                                                                      resp7.text)

                if match_PhoenixBookSearchProductsByProperty:
                    signature_PhoenixBookSearchProductsByProperty = match_PhoenixBookSearchProductsByProperty.group(1)
                    logger.info(f"signature_PhoenixBookProperty: {signature_PhoenixBookProperty}")
                    logger.info(
                        f"signature_PhoenixBookSearchProductsByProperty: {signature_PhoenixBookSearchProductsByProperty}")

                # ---------- 8: Book Property Page ----------
                url = "https://www.marriott.com/mi/query/PhoenixBookProperty"
                payload = json.dumps({
                    "operationName": "PhoenixBookProperty",
                    "variables": {
                        "propertyId": hotel_id.upper()
                    },
                    "query": "query PhoenixBookProperty($propertyId: ID!) {\n  property(id: $propertyId) {\n    ... on Hotel {\n      basicInformation {\n        ... on HotelBasicInformation {\n          descriptions {\n            type {\n              code\n              __typename\n            }\n            text\n            __typename\n          }\n          isAdultsOnly\n          resort\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n"
                })
                headers = {
                    'application-name': 'book',
                    'x-request-id': '',
                    'graphql-operation-name': 'PhoenixBookProperty',
                    'graphql-force-safelisting': 'true',
                    'accept': '*/*',
                    'apollographql-client-version': '1',
                    'content-type': 'application/json',
                    'apollographql-client-name': 'phoenix_book',
                    'graphql-require-safelisting': 'true',
                    'accept-language': 'en-US',
                    'graphql-operation-signature': signature_PhoenixBookProperty,
                    'origin': 'https://www.marriott.com',
                    'sec-fetch-site': 'same-origin',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-dest': 'empty',
                    # 'referer': 'https://www.marriott.com/reservation/rateListMenu.mi',
                    # 'cookie': 'bm_ss=ab8e18ef4e; _abck=4157EAFF3C3F9AA92FECB5944DE214B5~-1~YAAQDWnDFyfL/aCZAQAAt40n3Q7IBiX+VX9+pgEbF345nlhFLN5OVExMs8FahvIqCNt/Ybw4Jo4qvFvrlltA7H4kxEWkdQl9b0LVHCZfkghwq+8ieyUUxTfnlgZ8Jw4fRlCQw4YwDnrzUdnZnMQ3e/gQ1p2UgDsOo5x5wbeTrFjBebzq5xWBWQTbepbfZPXibc4bHzmzdEovqUO+nXIedr+/mLX/ccQUryVRSLS+1GK64e/ilaAM6PXzxClxuH19YvFb53Zkm8oZWbRKMuyPD4iDLo278g/4LCdWwbDS7349Npv6SfqLfABelhr00zlLQePAEdOfdGrLpnoZWgA5BmvlcyrkLYB8F5HCKpU1oFcDKpcBrwnrfKIKzStjg/CeYBh8VogYwmGIMqJgShBEHWz0H/fqcKSqXx+BNXzs1VhxwHev5V+frgMr753o3cQYXfj6Jg2HcrAQmg==~-1~-1~-1~-1~-1; ak_bmsc=968B4082DCE4B42C75B5ADD3C42ED3C3~000000000000000000000000000000~YAAQDWnDFyjL/aCZAQAAt40n3R0DBiU6sAx2sevENCZJMPSoK4eneuh6lUuihzRz/uVB7LF2JGHTdonLD26dpd6xBqKtq7EG5doJ7/u6jQUAQSkdE25Q8MSg2gja2va9JMsEjgxn/JRaTVSsBnNa6Nnuorv3+Jml4KqC38pR6GvYzX/wMnhi3WDZsSaJH+EZGI5/QozylMuaSo7IcTw4WEH3WPGqbaBDE4FEBP4pLSU9CoWR1/elbTM4UaPvlK2TbsbrSdEHxuJDCSn08BPOHKRnlOjLZXNVtHT+xOE3DSE7mbltaEWa6y3/L7jKT8BHD/C+wDYo7wrVCHoKMJLpfy1GMnnQuUr36aL2u2BexNrl8d7wegO9Ft9cSGJDRStXIvlVErU=; bm_so=93F5450046D761DB5004EACCEC05879B64567AF08E810CE1C595C34ABE43FB08~YAAQDWnDFyvL/aCZAQAAt40n3QXvp8d5PoE8xYmPFGqOkw36T4GIkIwRFQfbQ+vYswGlpq0LxnvKswjbD481jstS9nNt1SeBELmmu+okLCn+WWim92jjcOri4RKN6ehlcj2VpEtzTQJkLllxmBhtiuI7S/yUpKG7ijmiF2htd9tFR5P+f4502hY5saleSoGfxvQIAh47Y3vzVwlORvmzlGr92G/iupmlQUwGrskX1W9ulItW0XB+yZc9ECo47DjXLontyealBi3h9VwqWG5YCgzySGOXNHuFZqRuc5+VPR1jy6hdoNBQBUzCYBh666eAOe5ibhQYoh1V98y7pgkBmqmVTYumh7WzpSWSr47FN/5yiZIFowrf8pFVglPYGCuP+9nIXS/HOXq9yX0h2r/IoXvaHoHSdGrr54CEGPs0mRHfe6fH1qpdXAdSIt5GsjY8W1eFO57pVz8C5nWXVWwCYOI=; bm_sz=B8BBA0EF9E3EFA5E31BFFC83502A3151~YAAQDWnDFyzL/aCZAQAAt40n3R118AVA6wvHKcF2g6f2zwdBuTWqErI8dTF3xFVw7nWw63gUYH+ap81C2jdnzfUvbQNXOIbfGiy2onyhxF/wGlBrI6Axh8F8nb7jhsY5T5mF20HjXe7nZxH6LHYEQbK6eCuvmaCx5oCsJqsoJxdz95JEKh9j1fgzXqSUz2Ehft4QBvVk6XjeH5KZDgcDuzgYHgG+1xkTKd+jF+HkrsnIfJiufCp2iakjQUGQPR/ovfI4vbsPpkj/0Rz1sTQnpbsAMbTTE9bW4MDtvzGtiGfyH2HgiDMRoMxCZ9kSaf7fVvW7ztz48TIyzzWOE2yhk7NHIyGlWagjdKEul7C15AeYLvhG9Pn1Xg==~3162418~3616833; device-characteristics=brand_name=Chrome&model_name=140&marketing_name=Chrome+140&device_os=Windows+NT&device_os_version=10.0&mobile_browser=Chrome&mobile_browser_version=140&is_mobile=false&is_tablet=false; bm_lso=93F5450046D761DB5004EACCEC05879B64567AF08E810CE1C595C34ABE43FB08~YAAQDWnDFyvL/aCZAQAAt40n3QXvp8d5PoE8xYmPFGqOkw36T4GIkIwRFQfbQ+vYswGlpq0LxnvKswjbD481jstS9nNt1SeBELmmu+okLCn+WWim92jjcOri4RKN6ehlcj2VpEtzTQJkLllxmBhtiuI7S/yUpKG7ijmiF2htd9tFR5P+f4502hY5saleSoGfxvQIAh47Y3vzVwlORvmzlGr92G/iupmlQUwGrskX1W9ulItW0XB+yZc9ECo47DjXLontyealBi3h9VwqWG5YCgzySGOXNHuFZqRuc5+VPR1jy6hdoNBQBUzCYBh666eAOe5ibhQYoh1V98y7pgkBmqmVTYumh7WzpSWSr47FN/5yiZIFowrf8pFVglPYGCuP+9nIXS/HOXq9yX0h2r/IoXvaHoHSdGrr54CEGPs0mRHfe6fH1qpdXAdSIt5GsjY8W1eFO57pVz8C5nWXVWwCYOI=^1760351981042; MarriottOrigin=B; bm_s=YAAQDWnDF3rL/aCZAQAAr5cn3QT1T8/X+JG0Nc6dwxz97EsTL2JRnwymZxUDGZLpm8bNkzKeQTN9oVI9qTdhzTYEpFqzQ/DenD5WjRFAeax/cL4eO4ZzItQueLTRy4JTmikn2pIBPfGe30H6KRY/5lWGf7jtCwxK52zrvaYkA5vUYc+JG+q1tLPZAK4txmLh5X9ZyOrLWjNx1kxAhgg4ATG6ZheP2CZ9BYsA8GE84i1MGI35oBOryILCNqG0wq8glFVo/mrmQhgpL8jBMDxPBu7+YkCkISkV9PxNSXInXYxh4C3Nd0I5XJSa+uLdJqYpHwDbYs9Xy/6Yo+9RkCzcoR6uKWTCerU2K0MzJPmOnY6UP7xRHpWgZwBdBpaJ1bHwT6qhsTIvBPhrWU4LYjuV4yCQZq/LfL2eAPhfF1wGWmV3JjKGNyMtXSp9bwcVTfUfDEw4cFK/P8ZztzZLr0sCEQK9zf1TLn3Ub2HTpokxCXxSm7lvj59FidDPIvFrWaFuwZQQT7m2hvT9q3lE69MWPA2r9QZTbdnN3ihObDaQIK5J0UsPgWYf/4h0ajhBMDYF+nf6cDaBwPvGFQ==; bm_sc=2~1~838362831~YAAQDWnDF3vL/aCZAQAAr5cn3QV8/UoyXfVEXCE3LnFOUiPV6rehJlxiDstOyo2CuK3Asw+gGHqsLUSAgKk2Xa+0rQKngw4yTPRH/OZ/hSeUHFi31OnOK3PDWQQsr5aRSueayNnwujnOV7d2VGIin9VjZGpDC4zK+uEB6kDZaAwy+dqmuZ7x6P3J7H1EFhZoukqrXy9gOyLBXh4hlcRnBeBwfw5zknMutYwlRiQ+pL+QJaTC9cOFoDo24TebGKKto/wPu5rJJpIL2BK7zysGfHIUa+zLkfy8FNSQHbHfb5mkVuH1nJIn43hWYnOcOC/38Lqhr0APkuf+Ajh9F6wN0l9JTM3X1IVpD+of/7A5iTtR0riQAMWVYmksKwhGJMQhMs21OW79WR3hnVKaxwTxljIgGsVpI5MMCRx9BB5vGCdpMK6Sqf+9W0K2VOzz/ZT4mAs/n+J8n21LjtuuLW3ymoyHh/dKznH+gdW2PblS2VY='
                }
                resp8 = session.post(url, headers=headers, data=payload)
                logger.info(f"8 - Book_Property_Page: {resp8.status_code}")

                # ---------- 10: Promotional Rate Page ----------
                url = "https://www.marriott.com/mi/query/PhoenixBookSearchProductsByProperty"

                payload = json.dumps({
                    "operationName": "PhoenixBookSearchProductsByProperty",
                    "variables": {
                        "search": {
                            "options": {
                                "startDate": f"{check_in_date}",
                                "endDate": f"{check_out_date}",
                                "quantity": 1,
                                "numberInParty": 1,
                                "childAges": [],
                                "productRoomType": [
                                    "ALL"
                                ],
                                "productStatusType": [
                                    "AVAILABLE"
                                ],
                                "rateRequestTypes": [
                                    {
                                        "value": "",
                                        "type": "STANDARD"
                                    },
                                    {
                                        "value": "",
                                        "type": "PREPAY"
                                    },
                                    {
                                        "value": "",
                                        "type": "PACKAGES"
                                    },
                                    {
                                        "value": "MRM",
                                        "type": "CLUSTER"
                                    },
                                    {
                                        "value": "",
                                        "type": "REDEMPTION"
                                    }
                                ],
                                "isErsProperty": False
                            },
                            "propertyId": f"{hotel_id.upper()}"
                        },
                        "offset": 0,
                        "limit": 150
                    },
                    "query": "query PhoenixBookSearchProductsByProperty($search: ProductByPropertySearchInput, $offset: Int, $limit: Int) {\n  searchProductsByProperty(search: $search, offset: $offset, limit: $limit) {\n    edges {\n      node {\n        ... on HotelRoom {\n          availabilityAttributes {\n            rateCategory {\n              type {\n                code\n                __typename\n              }\n              value\n              __typename\n            }\n            isNearSellout\n            __typename\n          }\n          rates {\n            name\n            description\n            rateAmounts {\n              amount {\n                origin {\n                  amount\n                  currency\n                  valueDecimalPoint\n                  __typename\n                }\n                __typename\n              }\n              points\n              pointsSaved\n              pointsToPurchase\n              __typename\n            }\n            localizedDescription {\n              translatedText\n              sourceText\n              __typename\n            }\n            localizedName {\n              translatedText\n              sourceText\n              __typename\n            }\n            rateAmountsByMode {\n              averageNightlyRatePerUnit {\n                amount {\n                  origin {\n                    amount\n                    currency\n                    valueDecimalPoint\n                    __typename\n                  }\n                  __typename\n                }\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          basicInformation {\n            type\n            name\n            localizedName {\n              translatedText\n              __typename\n            }\n            description\n            localizedDescription {\n              translatedText\n              __typename\n            }\n            membersOnly\n            oldRates\n            representativeRoom\n            housingProtected\n            actualRoomsAvailable\n            depositRequired\n            roomsAvailable\n            roomsRequested\n            ratePlan {\n              ratePlanType\n              ratePlanCode\n              marketCode\n              __typename\n            }\n            freeCancellationUntil\n            __typename\n          }\n          roomAttributes {\n            attributes {\n              id\n              description\n              groupID\n              category {\n                code\n                description\n                __typename\n              }\n              accommodationCategory {\n                code\n                description\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          totalPricing {\n            quantity\n            rateAmountsByMode {\n              grandTotal {\n                amount {\n                  origin {\n                    value: amount\n                    valueDecimalPoint\n                    __typename\n                  }\n                  __typename\n                }\n                __typename\n              }\n              subtotalPerQuantity {\n                amount {\n                  origin {\n                    currency\n                    value: amount\n                    valueDecimalPoint\n                    __typename\n                  }\n                  __typename\n                }\n                __typename\n              }\n              totalMandatoryFeesPerQuantity {\n                amount {\n                  origin {\n                    currency\n                    value: amount\n                    valueDecimalPoint\n                    __typename\n                  }\n                  __typename\n                }\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          id\n          __typename\n        }\n        id\n        __typename\n      }\n      __typename\n    }\n    total\n    status {\n      ... on UserInputError {\n        httpStatus\n        messages {\n          user {\n            message\n            field\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      ... on DateRangeTooLongError {\n        httpStatus\n        messages {\n          user {\n            message\n            field\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n"
                })
                headers = {
                    'host': 'www.marriott.com',
                    'content-length': '5190',
                    'application-name': 'book',
                    'x-request-id': '',
                    'sec-ch-ua-platform': '"Windows"',
                    'graphql-operation-name': 'PhoenixBookSearchProductsByProperty',
                    'x-dtpc': '6$36758541_438h5vKJPTIVKBRMCMUMUDFVHJRKICCHCKJPFR-0e0',
                    'traceparent': '00-916AE5B5A7E6DCA1E754F9FBE6A00D55-87A64169B3E0C2ED-01',
                    'sec-ch-ua': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
                    'sec-ch-ua-mobile': '?0',
                    'graphql-force-safelisting': 'true',
                    'accept': '*/*',
                    'apollographql-client-version': '1',
                    'content-type': 'application/json',
                    'apollographql-client-name': 'phoenix_book',
                    'graphql-require-safelisting': 'true',
                    'accept-language': 'en-US',
                    'graphql-operation-signature': 'a1079a703a2d21d82c0c65e4337271c3029c69028c6189830f30882170075756',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
                    'origin': 'https://www.marriott.com',
                    'sec-fetch-site': 'same-origin',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-dest': 'empty',
                    'referer': 'https://www.marriott.com/reservation/rateListMenu.mi',
                    'accept-encoding': 'gzip, deflate, br, zstd',
                    'priority': 'u=1, i',
                    # 'cookie': 'useRequestedLanguage=true; device-characteristics=brand_name=Chrome&model_name=141&marketing_name=Chrome+141&device_os=Windows+NT&device_os_version=10.0&mobile_browser=Chrome&mobile_browser_version=141&is_mobile=false&is_tablet=false; AKA_A2=A; akacd_phoenix=3939614826~rv=38~id=9a875ff8ca0b7ffbbf95ec19ff88f855; bm_ss=ab8e18ef4e; MarriottOrigin=B; rxVisitor=1762162027894RJHEKBE6GBGBSQFI7NFA4J44A8C6JC9Q; dtSa=-; PIM-SESSION-ID=txfFAVoatZhuvcwD; dtPC=-29510$562027889_620h6vUTKONPHOPHJBWFVPFSFNAFGNQFUAKORP-0e0; sessionID=283B489B-C0F1-5E96-9987-3282FBDFD1B8; MI_SITE=prod17; dtCookie=v_4_srv_6_sn_EIJ4M148EU4188LSGNRCO076DGEAG8LK_perc_100000_ol_0_mul_1_app-3A220110cf75551a30_0_rcs-3Acss_0; rxvt=1762163828931|1762162027894; authStateToken=; ak_bmsc=9B016CB8BE425D8B79A1E5960F85A8F6~000000000000000000000000000000~YAAQDWnDF8AgsjCaAQAAULMKSR3LEY8GAJm5MHl4qWrgsKxPUw0jklDEjY74TOmlTW29IlZ3fDkVmb72CGGg3VzZQwskrrc/poZuaNAYFMFRVvL7twTLoGOvkX2tZo1eup85JQARXsxPrePijm1mjSxElRUzTieEClFQ+dRTM6FHkYT+6+PNDtfuQwdjLoQn3Vx0FJph99Qt15nFeWQOeQu5MtbcooR94lj8wTwKrOJIhIJMme2M/IfLccINtXg37diw0L/Zz8U7Lsvlez50gUT/hJaNzXM6/NzuCpSItC9ExhyUPX4rncbqOUUgklZMB9kDEO0sfWFPJrS05A0pO8baE6Np2c47IKG6KAhMdHCs6MQHxgQzWLq9cXdGgL2XxLfKZDkqBtz3IdFrezI=; s_loginState=unauthenticated; _cls_v=b2850aa1-4f9f-46a9-bc62-403aa7eb4676; _cls_s=f84882fc-901a-4246-9b59-7c6db0d2c23c:0; kndctr_664516D751E565010A490D4C_AdobeOrg_identity=CiYyNTMyNzQwNzk3NDU2MTQwMjU1MzI5MjUyNjQxNDU3Mzc4ODk1NVITCPv1qsikMxABGAEqBElORDEwAPAB%2D%5FWqyKQz; kndctr_664516D751E565010A490D4C_AdobeOrg_cluster=ind1; mboxEdgeCluster=41; _fwb=53Askl5RBzhnuQqFAPIRlf.1762162031468; rto=default; _yjsu_yjad=1762162032.4f3c0803-16cb-404f-9006-f654d7a30f8d; _fbp=fb.1.1762162032936.972361057892895196; kampyle_userid=0e08-3c12-351c-ed4b-af07-ff0b-1cf2-04b1; kampyleUserSession=1762162033079; kampyleUserSessionsCount=1; kampyleUserPercentile=74.58942712717389; __lt__cid=6fbc0ce3-00b0-4323-bb39-b6fba8e3a778; __lt__sid=5319f3b9-9efebfa8; _scid=tZBAzBk-bihtbWD82qODhbylDE5vdnWQ; jvxsync=v1tGjmsv6gOv; _ScCbts=%5B%5D; _ga=GA1.1.1883530285.1762162035; _yoid=d0e82a52-1d7f-47b3-a8ce-48205d0e5321; _yosid=a3065403-a25e-4e4b-b606-87871ad54c96; JVMID=mi-interceptor-app-blue; akacd_phoenix-dtt=3939614835~rv=24~id=f0ecde6165dd2ce5175ce0f7ad9df522; bm_sc=4~1~830552331~YAAQDWnDFwYhsjCaAQAAH9EKSQXIMOJn0EhLccFig/qWhfuTPCoJuCn9gQGejxn6qTr2gofZ4RL0GlzzsWTWUg/Mn0OYkaOcIXmT/kF/TRQiDIA4ZgWHjffsch2uWxXuxtutDxV+cWKRN4FCs0FS95xq7czuFqsM1DQb+z+C8hTyJmLRBc5jqrhHeaZcKY5crGUzE2Uz/GzxjEH7lEoPOIBqQz/ns7HhhU11gDeZCWuzPKMdukXRLMWBp1z28ZaVldQIL4p/SOhVVpD48/9zgxM1bE5ng6pegNWFrKpmuwPrXIl4cCteEf2t18nUwo/6UqqgTLIig2Jnv5nEXvTORt239OHkJN4pPV/qWGZD7xEwHlyIiXSfbtxLCqd6zebUvNqwJkXFydpM0KlH9+OhOxekaytU9EET+3El82EqUE+aeI31KHCPSG32+Lno74zX7cmIe2DCqjmuuMLTuRnFVgqEa5pzj9i+3ja6TDxbwdXKdt4tUEf+BBAv2wT0KyjRCda5e9QvR/SAu51w8PpBXTxzyKkZLHVjtXtgqXOzsScYrIPpPrDSSt5mEFHgG67aTLb8lclXAnlPD88um29ThEPlWEQ/vDRNZc2hYtkn0CHDUTVVWnaEMsMlyBOJhsMW7qxixkKDADyQiruBfCV16lnZSMLaovoIvhQAw1X7yteQzz9cGAyXgYT1Pb+Wsvec6jaUfkB5XR11cjVVJ3KDNpWLU0BKgoibp40U2A7XpMx7tcS3I7gt7/dQXicg9D+qHj46gct1pKdAy+FvqLzmz6HXEUB4q39lVJzIKiTWTR+Sl2/LG3+uwB2p4PmBicOVTFoE6UjC2srXFQ3IE3MopzmjRkvC+fXWrNQem5smr6GvKGV+BPBVeMQOs/BKNptyOnKbiubDkQCcY6xycFL2q6yNT/KtKv4Az+JgquXTq3r5jP8BUxrFTLaHuDRRy9jZv8XnFfq0UoCcEbLPrYvPtSQR71zFs5YZXDNO7GFLJ9vR67CUwTrvudNBZF4fti00d51NMHumkKrJj57N2ZMPSSP+7Vnf3SUNvEj/plHTPmar0PzC5FgnUgDuEISn5RcADQEt7vN0Gs8n1BLZeIsxtLVhR/MEcFRI0AnEPOxVfMMcNa4yefLawWOQ4zX8jb4mBau3F1n8tbjoLZ+WbJPCxJHv8M4HUvhRCIsK4lOa93rx3C2GO9YU//L6udNlCz5ME/1txdJNk73OVWLhOJ392FhmudZVZjQOzmMZyPZJ+oIp0XoqvGr9E8tDspz01Sx7BqquVoVkueSNL3R+C3plX0vCBMi6V8L8wTAZ9YYk4nk44hGzAinKE7U9bTgCrmc4JkXMma/TBnSnpxanlqHyY3/R4JMp6cGr0FyO6nZcDq24LhDRPHMswrDBqT8+gHH/5BVX2ExefQqGYrJEgmYl/DF3tCbPyUinOulUi4+IJ3NanbbzqWkrZ4DdsrWcEJ/3RxjCTkNeyjW6s7gmA6V72z28y9xXIRoJP70mQEIgDiALIbiFw/fMkFb4Jtd0AJpMn3Q4FIQw9aqWz/d3LASJc4jwgbKiEQ6mqYk39uv6KWGL6Hys30AhZ+L9RBHI4u/YyIqb2ghTrxG4saI7lokHbzYDcC7au8C8FdDEewkvuZMDXlVOwyc8mFfFH88onJrAEBkY9L9153JtlPUqUORMTBmflam4vqbX51h/177bmdOW8dBKY0G1nur0YDBtggtbUlj6XRygInj4yc/FXBJiLB3qyG8=; at_check=true; _gcl_au=1.1.1842475900.1762162040; _pin_unauth=dWlkPU5UbGlaRFV4TmpBdFpqYzFNUzAwT1RNNExXRm1NV1V0TkdZeU1qUTNNak5qTmpVNA; _sctr=1%7C1762108200000; AMCVS_664516D751E565010A490D4C%40AdobeOrg=1; AMCV_664516D751E565010A490D4C%40AdobeOrg=-1124106680%7CMCMID%7C25327407974561402553292526414573788955%7CMCAAMLH-1762766846%7C12%7CMCAAMB-1762766846%7Cj8Odv6LonN4r3an7LhD3WZrU1bUpAkFkkiY1ncBR96t2PTI%7CMCOPTOUT-1762169246s%7CNONE%7CvVersion%7C5.2.0; s_tbm=true; s_cc=true; aam_uuid=25401780980238278943303385412163178866; demdex=25401780980238278943303385412163178866; x_page_trace_id=/search/findHotels.mi~X~4CE6864C-DB00-5889-96D7-E9C3B5EC2C34; bm_so=A8979BD7A17BB8989C228F936B9E00A809212E53FA4281BE7A0EFD1734B2B58F~YAAQDWnDF/8hsjCaAQAAsXELSQWq3LTBygYuB1eDgA6vhMJhNlgTh/ahqPw4lrNC3eTlKLxMvsse38ZfnxRZ4JwXBr7UDZojJK2CVFnPRxcKN/H06VPq7UpAK6fZyiBCPj5m6lBuWxXuan+jmnOs7Ff4cmyxStktikEpg0HZBRWiccANHTRLoeKQSXf3aVXdh+mw0GLr4Rz9QQIOQsfAWsOvHYLiqd/YDHDoxHYl9WMZIvA6pNORyBxEBPeuJpX8xxIW1Iz62l3foxYjP8HplohFHZFlJk8Mx0QIzkjMClFbnlcwB7syhDQm1kWyhu8UanXeoBHUvsycNtboLpuwH4GDKKIr7XQBc0taLLmppkMkfjJWycN6gCV0Dr9oZ1d9B+uiMFppcxCotlPsCw7LajT6gZHpjaxOvCr8C7qjSsgRMLgY2onVH8SsmHbe1KSwhHatW1f5/BVb7K1ZRgDxvkA=; x-mi-tag=NA; kampyleSessionPageCounter=3; _uetsid=4bd95c10b89711f0951c05517e4a0c1b; _uetvid=4bd987f0b89711f0b5aa75dbf3a347e1; bm_lso=A8979BD7A17BB8989C228F936B9E00A809212E53FA4281BE7A0EFD1734B2B58F~YAAQDWnDF/8hsjCaAQAAsXELSQWq3LTBygYuB1eDgA6vhMJhNlgTh/ahqPw4lrNC3eTlKLxMvsse38ZfnxRZ4JwXBr7UDZojJK2CVFnPRxcKN/H06VPq7UpAK6fZyiBCPj5m6lBuWxXuan+jmnOs7Ff4cmyxStktikEpg0HZBRWiccANHTRLoeKQSXf3aVXdh+mw0GLr4Rz9QQIOQsfAWsOvHYLiqd/YDHDoxHYl9WMZIvA6pNORyBxEBPeuJpX8xxIW1Iz62l3foxYjP8HplohFHZFlJk8Mx0QIzkjMClFbnlcwB7syhDQm1kWyhu8UanXeoBHUvsycNtboLpuwH4GDKKIr7XQBc0taLLmppkMkfjJWycN6gCV0Dr9oZ1d9B+uiMFppcxCotlPsCw7LajT6gZHpjaxOvCr8C7qjSsgRMLgY2onVH8SsmHbe1KSwhHatW1f5/BVb7K1ZRgDxvkA=^1762162080575; _scid_r=zxBAzBk-bihtbWD82qODhbylDE5vdnWQlZuQxQ; wcs_bt=s_199db929d7ed:1762162081; OptanonConsent=isGpcEnabled=0&datestamp=Mon+Nov+03+2025+14%3A58%3A01+GMT%2B0530+(India+Standard+Time)&version=202411.2.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=e4f0388c-c649-451a-b65e-9bb7af749550&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=1%3A1%2C3%3A1%2C4%3A1%2C6%3A1&AwaitingReconsent=false; merchViewed=hpHero-undefined|hpBanner-|advSearchBanner-MER_GLB0005L9X_GLE000D16M_GLF000T3RY|serpBannerhvmb010124|; s_sq=%5B%5BB%5D%5D; _abck=AB3EE59BA38D71D22E516DE5984072E1~0~YAAQDWnDF3wisjCaAQAAGbILSQ4/Ehcs9pZiG04ty1mi6I02xuPbbiKH9Q9cpTIuIu50jqgqgGO1ByBg5Ou22gbvxjwNyXqGENU60sBLmAMex9lBVvW1t3PTmr7M9EWc7Ug4CYeG8oa8Q515Xe/nQITzhX1tzlb6+Nj3g2t4SjC1+N4scFOSAx5pOy3uDIB3qvbfBulRYIXPRNxZCs4i68vvBwoGKLS/y4tLyy55SSAzcys43/moKoKEZvniKMduy+DIstsU2cFfmBp8z4M+Y5ig2H15Mw6ePgCbRLZ7PBHllmT65hVforNfIW6S1TYVYZyFV4t60Jirygkpkp1FCjunij2lkIUOyosAfoPiomyUAmMWUldOIFNJEIhrVwp8UdBxdWfkWPcKjf5JkFssQ0r3U5qb/urmdPVZcfStgDkWtNIWLw9U1anjJNvExBAjWY0akqLWIVqTQv60xnO6R8LYCfnCDWzg/EFfuPMnpPSLz21SLb+Sb+Pvs35ketBvYh++2BVXV8EMp8AQ2OoGsD54177laSZmzPEBho18L1pDI07uDRNZ1dGZXgjfR8rk/1AWDo/VPR9FHuu2r5aqlQUeD4gC4FpOtYNK1KXbYi9SmTdIeGcYOt1YWrg9TiJ0+tcodj9ci3ZclxyQwJ8rLMFQOd5/P8tfWtXvNTuVIIvW3LZMnoCA7aZe+sTKdUuMuwFso/kDa3ANwQ7sg78weUjR8cqvkdTSgWGVXlxCrP4OmS3nh67PpNj4Tn7vtkOMWjl3n+k4ki2J2VrfqHVEcutAgEhP7c/3LPe6qf+3LG2N4J7HSycP5IuxVSgcnUHgY/aThbE2JM6xHmIRYL67a64gMrpa+yd410DqAOMoW6KG+Kybqo7G+QJUTg==~-1~-1~1762165675~AAQAAAAE%2f%2f%2f%2f%2f34b4M0zOelFMIq3haxzVoIjSRuZzWreXK2o+mGD%2f2gkWLpo2DPweINpB95GftmWuHC30eRgUiZjPhKOT1FaqbsVLvvBtiel1ZjY~-1; bm_s=YAAQDWnDF30isjCaAQAAGbILSQS4e+fhF5NjpLA6yvqcKu0FG36oKEhc53V/Loyu550yZWSY7tnia3tv1Pw9xcvdtr1TvJygisGHO3XMDAh8xjOcvFQVTif1+cl0qegpSBaFs6PygmbK4EjNBGht7/34QLclD7LuqswMLBOl2XHBHYxMBxYuRTHmvaDjFSOw6oonlsXkKXpanBjNBZJRQs4mrMiNlRaGIUN5jfYhFeeiR2OyoYfW6wrvITVBg9Bwdo6ELC8rhfjS++VEARy35lq0WxDLsqDxzXhTOBdBrNEF7ln5rxdWrGyO94urYXSo/bBiCTPgXcxwqvc3YiV3fg18da7z7j8fhcezc7/d1yC8p6ml0Rj+Np6Rd9Jx8BzWDz2YRdnVtFhbUL7AjqJ9A+xCZD+XnNxdC3DLa0kX2F77kKHKFOH+tmG0gF0Ee/Ii04WNK50VCrxGUT8wfTPt0Uz3i3q1xoVfBf5PvXQmA8ZmR2gJrqmg0xDcCgXqPMfIhGEeMs5lDoMBMMXBEID6LJJkNAYmOH09z929UjMPfNFyJl+Pz+DNB18HAvGfcmzPPQ/JQXpEblyO+A==; bm_sz=AF266690FE46EAED160FC659BC8314E1~YAAQDWnDF34isjCaAQAAGbILSR0S7QE4UL/DHUXTVZUpp8TfO/Sz5yS8Cemk0Y6rxDr2jv1HsfjrNdCtLfyCcdXVaNr6wK1ccbxe/BcDsRyAj5g5O/cMJ7rQwaT2gahWNDVe7a6FLBlYg/dKOflJbIVdCzWOo94sFAVyVfsk7mGGqsqS3bwoJHWT4aBCYrYpBk9luyPwK8im+YYt29nLlcX1uFE0z6a3GvFKHWx79WLDKAcfCKC37i2aNFUKiXqVJW56CTuzkibfrnVlfP27Fu1vs/ReiUgtCoehjxF4yjv3W2i2wKK2AFKtv0yU0jv5/kz8XNqF1d0GMkyFBYjONB+nBb24A+Ejt8Bs0iJxLwUqsZKSMWqoZVasRDnQHhpNBLHv9A1EgAGEWm7sZ+1wDT7NHmsmS8/k1PSZWoTygnLTXl7RTImlyBCPZdYYIm42/4+eBlj9Z6UZ44xl3LzcRQ==~4536116~4536133; _ga_1LXTBF5X2V=GS2.1.s1762162034$o1$g1$t1762162094$j60$l0$h0; Ddup=06fa8593-7cbe-4ca3-9708-8377c53fddb0; mbox=session#25327407974561402553292526414573788955-XNXjBN#1762163956|PC#25327407974561402553292526414573788955-XNXjBN.41_0#1825406886; _abck=27073CA09FFBD04249C03138C9D83786~-1~YAAQDWnDF/HEEOiZAQAAH+N08Q7LzdBqNxvu0yhLwJMQwA1TxakR1H7uRkAYgYs/Lc+aAy6tc+f0XJyoJzl7DaHjYJL0rKQLalMEpork56BdVM1Qv4wk06oudnM+QVBjjAyWpLvBdhPdb7aYnInrxrEkPBM+k1zejSl/csqr6GT5tY6xv7IY6w9aD2D8sR8CjnVU0CMvZ5GKT1K4+WWviVwY4qV8HwYuoMrjPQ/ti+MKEwBtE3PilJSEwOE16TrtmKSGiH7UB2QsuDeHsGMbMN8ZdOoObBJa2lix2NbPdF3ubv3s3f7ZQ+LMtF3htDTfKffM0UIwFEyzHMD4feMk8CC+XoAt1oKbggXw7DkNy7uRP1VVtMAsZPWqhXXJADPJSrSGMIlApZe2cnmnq9bSNsVaRsA6G8SzUtL5WPY15tNyUR8kyqLzKlyBeVoQVM8H7VOBl9gxUiUt5fdNM27cNE5jE5jbFTSk037WxmahOtjzYLKkoY6dPt20aUWTZ+iKcbecpg7DvrYcnOIwsYFj48St5/Z/hYQelN0HvneT/dLTuMgh4/bemgAoLvQIgVtlFKjsO+woHan5vZ/7l0dvRc3fj5Yb9Cd4h+/BXrdKtoib8PRoPZaxg2Z/IvzxQP6dnGWF~0~-1~1760688859~AAQAAAAE%2f%2f%2f%2f%2f%2f+XwhtCu8g3JZ09tSBSv7qKr2LntrNtwZfKYBwSbeNP80PRiCW7ejY%2fLuuhDt6m2RBrnf6oSXJx0xbOZiUpP1rxanT9qpbNrEok~-1; bm_s=YAAQDWnDFxTmEOiZAQAABD998QQvAYiLIHztpBxob724mzMV0q0sH/7VzWWLqXaR1RHsxddWAMWRTHh213xeEfuGtROCLYtK0LgB1MVcQjTa8DrnALH88R31K9df14ebRYnYKhHVbb0YHZh9L4CnOwu4mgCUSFcldSWqZlqiCMcqYuk7HSc8fwi6y/P1RxUie0q3UyTabk4jGJZF2tADE0UqQclqcfBA3T1uusNYwco5F9xpNZ3RC85uKjyMan0LVo/eUNCeLAXXR1xlZ9fCHu99VQ2JWT2g9lR6XVoIsv281JPkYTrIqLxeaJHRGscuFCH+RpK0W3E1Ogdzj2zwW3ULZMICUUvBxtBnFNSD4bgLwm24iBrIP7T5NFel8h/Oj4zoDRv+3szfAaoqLrbx931L0C0ykw8a9Qz5LoIcmVQlKoA=; JVMID=mi-interceptor-app-green; MI_SITE=prod17; MI_Visitor=3AF17CDC-A9AC-52B9-96EE-E90A3EF5710E; device-characteristics=brand_name=Chrome&model_name=141&marketing_name=Chrome+141&device_os=Windows+NT&device_os_version=10.0&mobile_browser=Chrome&mobile_browser_version=141&is_mobile=false&is_tablet=false; x-mi-tag=NA'
                }

                resp10 = session.post(url, headers=headers, data=payload)

                # resp10 = session.post(url, headers=headers, data=payload)
                logger.info(f"10 - Promotional_Rate_Page: {resp10.status_code}")
                logger.info(f"10 - Promotional_Rate_Page: {resp10.text[:1000]}")
                if "\"Invalid Property Code\"" in resp10.text:
                    logging.error("Property Code is invalid.")
                    return ("Property Code is invalid.")
                if '"code":"standard"' in resp10.text and '"code":"redemption"' not in resp10.text:
                    logging.error("There are no redemption rates available for the dates you selected.")
                    return ("There are no redemption rates available for the dates you selected.")

                text_resp = resp10.text
                file_path = f"marriott_{hotel_id}_{check_in_date}_{check_out_date}_response.json"

                logger.info(f"Saving API Response at Path:- {file_path}")

                try:
                    json_data = json.loads(text_resp)
                except json.JSONDecodeError:
                    logger.info("Response is not valid JSON")
                    json_data = {"raw_response": text_resp}

                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(json_data, f, indent=4, ensure_ascii=False)

                int_count += 1

            except Exception as ex:
                logging.error(f"Exception occurred: {ex}")
                is_all_requests_passed = False
            finally:
                logger.info("Closing application...")

            if is_all_requests_passed:
                break

        return json_data

if __name__ == "__main__":
    crawl = ExtractMarriott()
    data = crawl.get_search_data(
        hotel_id="swfhr-inn at bellefield hyde park",
        check_in_date="2025-11-21",
        check_out_date="2025-11-29",
        guest_count=1,
    )
    if data:
        print("API data fetched successfully")
    else:
        print("API data could not be fetched with current cookies")