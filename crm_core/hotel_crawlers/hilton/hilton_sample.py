import json
import logging
import random
import time
from urllib.parse import quote
import requests
from datetime import datetime
from .proxy_manager import ProxyManager
from .random_user_agent import get_random_sec_ch_headers, USER_AGENT

# ---------------- Log configuration ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("ihg.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def human_delay(a, b):
    time.sleep(random.uniform(a, b))

class ExtractIhg:

    def __init__(self):
        self._proxy_fetcher = ProxyManager()
        browser_family, headers = get_random_sec_ch_headers(USER_AGENT)
        self._headers = headers
        self.sec_headers_flag = False
        if browser_family not in ("firefox", "webkit"):
            self.sec_headers_flag = True

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

        # ---------- Session Setup ----------
        session = requests.Session()
        session.proxies.update(proxies)
        session.headers.update(self._headers)
        logger.info("Setting up crawler to extract data")

        # Validate inputs
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
        encoded_hotel_name = quote(hotel_id_name, safe="")

        # ---- Retry mechanism ----
        int_count = 1
        for icount in range(3):
            try:
                ############ New Req 1 ##################
                logger.info("Home page requested....")
                homeUrl = "https://www.ihg.com/hotels/us/en/reservation"
                session.headers.update({
                    'upgrade-insecure-requests': '1',
                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'sec-fetch-site': 'none',
                    'sec-fetch-mode': 'navigate',
                    'sec-fetch-user': '?1',
                    'sec-fetch-dest': 'document',
                    'accept-language': 'en-US,en;q=0.9',
                    'priority': 'u=0, i',
                    'host': 'www.ihg.com',
                })
                homeResponse = session.get(homeUrl)
                if homeResponse.status_code != 200:
                    message = {
                        "details": "Home page request failed",
                    }
                    return self.build_response(success=False, data=message, status_code=homeResponse.status_code)
                else:
                    logger.info(f"Home page request succeeded with status code: {homeResponse.status_code}")

                ############ New Req 2 ##################
                logger.info("Pre location search Requested....")
                preLocationUrl = f"https://apis.ihg.com/locations/v1/destinations?destination={encoded_hotel_name}&ihg-language=en-US&chainCode=6c"
                session.headers.pop('upgrade-insecure-requests')
                session.headers.pop('sec-fetch-user')
                if self.sec_headers_flag:
                    session.headers.pop('sec-ch-ua')
                    session.headers.pop('sec-ch-ua-mobile')
                    session.headers.pop('sec-ch-ua-platform')
                session.headers.update({
                    'accept': '*/*',
                    'access-control-request-method': 'GET',
                    'access-control-request-headers': 'content-type,ihg-language,ihg-sessionid,x-ihg-api-key',
                    'origin': 'https://www.ihg.com',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-site',
                    'sec-fetch-dest': 'empty',
                    'referer': 'https://www.ihg.com/',
                    'priority': 'u=1, i',
                    'host': 'apis.ihg.com',
                })
                preLocationResponse = session.options(preLocationUrl)
                if preLocationResponse.status_code != 200:
                    message = {
                        "details": "Pre location search failed",
                    }
                    return self.build_response(success=False, data=message, status_code=preLocationResponse.status_code)
                else:
                    logger.info(f"Pre location search succeeded with status code: {preLocationResponse.status_code}")

                ############ New Req 3 ##################
                logger.info("Location search Requested....")
                locationUrl = preLocationUrl
                session.headers.pop('access-control-request-method')
                session.headers.pop('access-control-request-headers')
                if self.sec_headers_flag:
                    session.headers.update({
                        'sec-ch-ua-platform': self._headers['sec-ch-ua-platform'],
                        'sec-ch-ua': self._headers['sec-ch-ua'],
                        'sec-ch-ua-mobile': self._headers['sec-ch-ua-mobile'],
                    })
                session.headers.update({
                    'ihg-language': 'en-US',
                    'ihg-sessionid': '85cff00e-d07d-4c40-9cd1-15f5ed6fcdfb',
                    'x-ihg-api-key': 'se9ym5iAzaW8pxfBjkmgbuGjJcr3Pj6Y',
                    'accept': 'application/json, text/plain, */*',
                    'content-type': 'application/json; charset=UTF-8'
                })
                locationResponse = session.get(locationUrl)
                if locationResponse.status_code != 200:
                    message = {
                        "details": "Location search failed",
                    }
                    return self.build_response(success=False, data=message, status_code=locationResponse.status_code)
                else:
                    logger.info(f"Location search succeeded with status code: {locationResponse.status_code}")
                    if '"No destination found"' in locationResponse.text:
                        message = {
                            "details": f"No destination found at input location {hotel_name}",
                        }
                        return self.build_response(success=True, data=message, status_code=locationResponse.status_code)
                    latitude = locationResponse.json()[0]['latitude']
                    longitude = locationResponse.json()[0]['longitude']
                    clarifiedLocation = locationResponse.json()[0]['clarifiedLocation']
                    locationType = locationResponse.json()[0]['type']

                ############ New Req 4 ##################
                logger.info("Pre hotel search Requested....")
                preHotelUrl = "https://apis.ihg.com/graphql/v1/hotels"
                if self.sec_headers_flag:
                    session.headers.pop('sec-ch-ua')
                    session.headers.pop('sec-ch-ua-mobile')
                    session.headers.pop('sec-ch-ua-platform')
                session.headers.pop('ihg-language')
                session.headers.pop('ihg-sessionid')
                session.headers.pop('x-ihg-api-key')
                session.headers.pop('content-type')
                session.headers.update({
                    'accept': '*/*',
                    'access-control-request-method': 'POST',
                    'access-control-request-headers': 'content-type,ihg-language,x-ihg-api-key',
                })
                preHotelResponse = session.options(preHotelUrl)
                if preHotelResponse.status_code != 200:
                    message = {
                        "details": "Pre hotel search failed",
                    }
                    return self.build_response(success=False, data=message, status_code=preHotelResponse.status_code)
                else:
                    logger.info(f"Pre hotel search succeeded with status code: {preHotelResponse.status_code}")

                ############ New Req 5 ##################
                logger.info("Hotel search Requested....")
                hotelUrl = preHotelUrl
                # hotelpayloadSample = "{\r\n    \"operationName\": \"GetHotelDetails\",\r\n    \"variables\": {\r\n        \"detailsInput\": {\r\n            \"geoLocation\": {\r\n                \"lat\": 40.757996,\r\n                \"lon\": -73.985626,\r\n                \"radius\": 30\r\n            },\r\n            \"geoLocationDistance\": {\r\n                \"distanceType\": \"STRAIGHT_LINE\",\r\n                \"distanceUnit\": \"MI\"\r\n            },\r\n            \"size\": 120,\r\n            \"fallbackSearch\": {\r\n                \"minHotels\": 1,\r\n                \"maxRadius\": 100,\r\n                \"incrementRadiusBy\": 70\r\n            },\r\n            \"sortBy\": \"DISTANCE\"\r\n        },\r\n        \"mediaArgs\": {\r\n            \"formats\": [\r\n                {\r\n                    \"aspectHeight\": \"3\",\r\n                    \"aspectWidth\": \"4\"\r\n                },\r\n                {\r\n                    \"aspectHeight\": \"5\",\r\n                    \"aspectWidth\": \"16\"\r\n                }\r\n            ]\r\n        }\r\n    },\r\n    \"query\": \"query GetHotelDetails($detailsInput:HotelArgs$mediaArgs:MediaArgs){getHotels(input:$detailsInput){hotelInfo{hotelCode address{street1 street2 street3 city zip state{code name}country{name code}}location{boardTypes{boardType}}distanceFrom{kilometers miles}marketing{optOutDateWeb optInDateWeb marketingText{welcomeMessage}}brandInfo{SPBrandName brandCode brandName chainCode futureBrandInfo{rebrandingDate hotelName chainCode brandName brandCode}spTransitionalBrandIdentifier}greenEngage{certificationPrograms{certifiedByGloballyRecognizedSustainableProgram environmentalCertificationProgram{listItem}}lowCarbon{lowCarbonHotelDescription isLowCarbonHotel}lowCarbonReady{lowCarbonReadyHotelDescription isLowCarbonReadyHotel}}room{hotelHighlights{hotelDisclaimer}}badges{name id}facilities{name id}parking{complimentaryDailySelfParking parkingDescription carParkingAvailable valetParkingAvailable}policies{pet{petsAllowed guideDogsOrServiceAnimalsAllowed description}}stripes{id name}renovationAlertsList{alertType flagEndDate flagStartDate other}profile{name webNonBrandedHotelLogo{url}seoCity nonIhgCrsUrl hotelLogo{originalUrl}averageReview tpiLevel2Violator primaryImageUrl{originalUrl}latLong{lon lat}hotelStatus preSellDate dateOpened totalReviews vatIncluded}media(input:$mediaArgs){primaryPhotos{allPhotos{type primary caption originalUrl formats{url aspectHeight aspectWidth}}}}foodAndBeverage{complimentaryBreakfastDetails{complimentaryGrabAndGoBreakfast}}restaurant{onSiteRestaurantsCount}tax{taxAndFeeDetail serviceCharge{startAndEndDate{startDate endDate}description}}}}}\"\r\n}"
                hotelpayload_dict = {
                    "operationName": "GetHotelDetails",
                    "variables": {
                        "detailsInput": {
                            "geoLocation": {
                                "lat": latitude,
                                "lon": longitude,
                                "radius": 30
                            },
                            "geoLocationDistance": {
                                "distanceType": "STRAIGHT_LINE",
                                "distanceUnit": "MI"
                            },
                            "size": 120,
                            "fallbackSearch": {
                                "minHotels": 1,
                                "maxRadius": 100,
                                "incrementRadiusBy": 70
                            },
                            "sortBy": "DISTANCE"
                        },
                        "mediaArgs": {
                            "formats": [
                                {"aspectHeight": "3", "aspectWidth": "4"},
                                {"aspectHeight": "5", "aspectWidth": "16"}
                            ]
                        }
                    },
                    "query": (
                        "query GetHotelDetails($detailsInput:HotelArgs$mediaArgs:MediaArgs)"
                        "{getHotels(input:$detailsInput){hotelInfo{hotelCode address{street1 street2 "
                        "street3 city zip state{code name}country{name code}}location{boardTypes{boardType}}"
                        "distanceFrom{kilometers miles}marketing{optOutDateWeb optInDateWeb marketingText{welcomeMessage}}"
                        "brandInfo{SPBrandName brandCode brandName chainCode futureBrandInfo{rebrandingDate hotelName "
                        "chainCode brandName brandCode}spTransitionalBrandIdentifier}greenEngage{certificationPrograms"
                        "{certifiedByGloballyRecognizedSustainableProgram environmentalCertificationProgram{listItem}}"
                        "lowCarbon{lowCarbonHotelDescription isLowCarbonHotel}lowCarbonReady{lowCarbonReadyHotelDescription "
                        "isLowCarbonReadyHotel}}room{hotelHighlights{hotelDisclaimer}}badges{name id}facilities{name id}"
                        "parking{complimentaryDailySelfParking parkingDescription carParkingAvailable valetParkingAvailable}"
                        "policies{pet{petsAllowed guideDogsOrServiceAnimalsAllowed description}}stripes{id name}"
                        "renovationAlertsList{alertType flagEndDate flagStartDate other}profile{name webNonBrandedHotelLogo{url}"
                        "seoCity nonIhgCrsUrl hotelLogo{originalUrl}averageReview tpiLevel2Violator primaryImageUrl{originalUrl}"
                        "latLong{lon lat}hotelStatus preSellDate dateOpened totalReviews vatIncluded}media(input:$mediaArgs)"
                        "{primaryPhotos{allPhotos{type primary caption originalUrl formats{url aspectHeight aspectWidth}}}}"
                        "foodAndBeverage{complimentaryBreakfastDetails{complimentaryGrabAndGoBreakfast}}restaurant"
                        "{onSiteRestaurantsCount}tax{taxAndFeeDetail serviceCharge{startAndEndDate{startDate endDate}description}}}}}"
                    )
                }
                hotelpayload = json.dumps(hotelpayload_dict)
                session.headers.pop('access-control-request-method')
                session.headers.pop('access-control-request-headers')
                if self.sec_headers_flag:
                    session.headers.update({
                        'sec-ch-ua-platform': self._headers['sec-ch-ua-platform'],
                        'sec-ch-ua': self._headers['sec-ch-ua'],
                        'sec-ch-ua-mobile': self._headers['sec-ch-ua-mobile'],
                    })
                session.headers.update({
                    'ihg-language': 'en-US',
                    'x-ihg-api-key': 'se9ym5iAzaW8pxfBjkmgbuGjJcr3Pj6Y',
                    'accept': 'application/json, text/plain, */*',
                    'content-type': 'application/json; charset=UTF-8',
                })
                hotelResponse = session.post(hotelUrl, data=hotelpayload)
                if hotelResponse.status_code != 200:
                    message = {
                        "details": "Hotel search failed",
                    }
                    return self.build_response(success=False, data=message, status_code=hotelResponse.status_code)
                else:
                    logger.info(f"Hotel search succeeded with status code: {hotelResponse.status_code}")
                    if '"hotelCode"' not in hotelResponse.text:
                        message = {
                            "details": f"Hotel not found at input location {hotel_name}",
                        }
                        return self.build_response(success=True, data=message, status_code=hotelResponse.status_code)


                ############ New Req 6 ##################
                logger.info("Pre list data search Requested....")
                preListDataUrl = "https://apis.ihg.com/availability/v3/hotels/offers?fieldset=summary,summary.rateRanges"
                if self.sec_headers_flag:
                    session.headers.pop('sec-ch-ua')
                    session.headers.pop('sec-ch-ua-mobile')
                    session.headers.pop('sec-ch-ua-platform')
                session.headers.pop('ihg-language')
                session.headers.pop('x-ihg-api-key')
                session.headers.pop('content-type')
                session.headers.update({
                    'accept': '*/*',
                    'access-control-request-method': 'POST',
                    'access-control-request-headers': 'content-type,ihg-language,ihg-sessionid,x-ihg-api-key'
                })
                preListDataResponse = session.options(preListDataUrl)
                if preListDataResponse.status_code != 200:
                    message = {
                        "details": "Pre list data search failed",
                    }
                    return self.build_response(success=False, data=message, status_code=preListDataResponse.status_code)
                else:
                    logger.info(f"Pre list data search succeeded with status code: {preListDataResponse.status_code}")

                ############ New Req 7 ##################
                logger.info("List data search Requested....")
                listDataUrl = preListDataUrl
                listDatapayload = "{\r\n    \"hotelMnemonics\": [\r\n        \"NYCXV\",\r\n        \"NYCHC\",\r\n        \"NYCEA\",\r\n        \"NYCDD\",\r\n        \"NYCAT\",\r\n        \"NYCMA\",\r\n        \"NYCCW\",\r\n        \"NYCWS\",\r\n        \"NYCPC\",\r\n        \"NYCVM\",\r\n        \"NYCTS\",\r\n        \"NYCTT\",\r\n        \"NYCHK\",\r\n        \"NYCPK\",\r\n        \"NYCHA\",\r\n        \"NYCAA\",\r\n        \"NYCNY\",\r\n        \"NYCEV\",\r\n        \"NYCVC\",\r\n        \"NYCVO\",\r\n        \"NYCIS\",\r\n        \"NYCOS\",\r\n        \"NYCES\",\r\n        \"NYCEX\",\r\n        \"JERCY\",\r\n        \"NYCAS\",\r\n        \"NYCMP\",\r\n        \"NYCMF\",\r\n        \"EWRCJ\",\r\n        \"NYCWL\",\r\n        \"NYCGO\",\r\n        \"NYCSF\",\r\n        \"NYCNJ\",\r\n        \"NYCWD\",\r\n        \"MPENY\",\r\n        \"LGABR\",\r\n        \"BXYEV\",\r\n        \"NYCFL\",\r\n        \"CSTNJ\",\r\n        \"BXYSP\",\r\n        \"NYCLF\",\r\n        \"NYCFQ\",\r\n        \"NYCBA\",\r\n        \"HASNJ\",\r\n        \"ENGNJ\",\r\n        \"NYCBK\",\r\n        \"NYCAV\",\r\n        \"EWRHL\",\r\n        \"NYCJC\",\r\n        \"MFHAM\",\r\n        \"SADNJ\",\r\n        \"EWRZB\",\r\n        \"EWRSP\",\r\n        \"HPNNR\",\r\n        \"LDJNJ\",\r\n        \"CLKNJ\",\r\n        \"NYCWB\",\r\n        \"EWRWB\",\r\n        \"PASNJ\",\r\n        \"RAMNJ\",\r\n        \"HSKNJ\",\r\n        \"HPNHY\",\r\n        \"NYCMW\",\r\n        \"HZTNJ\",\r\n        \"SUFNY\",\r\n        \"EDSCP\",\r\n        \"NYCPV\",\r\n        \"PNFNJ\",\r\n        \"EBKNJ\"\r\n    ],\r\n    \"radius\": null,\r\n    \"maxRadius\": null,\r\n    \"minHotels\": 1,\r\n    \"incrementRadiusBy\": null,\r\n    \"distanceUnit\": \"MI\",\r\n    \"distanceType\": \"STRAIGHT_LINE\",\r\n    \"startDate\": \"2025-12-25\",\r\n    \"endDate\": \"2025-12-28\",\r\n    \"geoLocation\": null,\r\n    \"products\": [\r\n        {\r\n            \"productCode\": \"SR\",\r\n            \"startDate\": \"2025-12-25\",\r\n            \"endDate\": \"2025-12-28\",\r\n            \"quantity\": 1,\r\n            \"guestCounts\": [\r\n                {\r\n                    \"otaCode\": \"AQC10\",\r\n                    \"count\": 1\r\n                }\r\n            ]\r\n        }\r\n    ],\r\n    \"rates\": {\r\n        \"ratePlanCodes\": [\r\n            {\r\n                \"internal\": \"IVAN1\"\r\n            },\r\n            {\r\n                \"internal\": \"IVAN3\"\r\n            },\r\n            {\r\n                \"internal\": \"IVAN5\"\r\n            },\r\n            {\r\n                \"internal\": \"IVAN6\"\r\n            },\r\n            {\r\n                \"internal\": \"IVAN7\"\r\n            },\r\n            {\r\n                \"internal\": \"IVANI\"\r\n            }\r\n        ]\r\n    }\r\n}"
                session.headers.pop('access-control-request-method')
                session.headers.pop('access-control-request-headers')
                if self.sec_headers_flag:
                    session.headers.update({
                        'sec-ch-ua-platform': self._headers['sec-ch-ua-platform'],
                        'sec-ch-ua': self._headers['sec-ch-ua'],
                        'sec-ch-ua-mobile': self._headers['sec-ch-ua-mobile'],
                    })
                session.headers.update({
                    'ihg-language': 'en-US',
                    'ihg-sessionid': '85cff00e-d07d-4c40-9cd1-15f5ed6fcdfb',
                    'x-ihg-api-key': 'se9ym5iAzaW8pxfBjkmgbuGjJcr3Pj6Y',
                    'accept': 'application/json, text/plain, */*',
                    'content-type': 'application/json; charset=UTF-8'
                })
                listDataResponse = session.post(listDataUrl, data=listDatapayload)
                if listDataResponse.status_code != 200:
                    message = {
                        "details": "List data search failed",
                    }
                    return self.build_response(success=False, data=message, status_code=listDataResponse.status_code)
                else:
                    logger.info(f"List data search succeeded with status code: {listDataResponse.status_code}")

                ############ New Req 8 ##################
                logger.info("Pre hotel detail search Requested....")
                preHotelDetailUrl = "https://apis.ihg.com/availability/v3/hotels/offers?fieldset=rateDetails,rateDetails.policies,rateDetails.bonusRates,rateDetails.upsells,alternatePayments"
                if self.sec_headers_flag:
                    session.headers.pop('sec-ch-ua')
                    session.headers.pop('sec-ch-ua-mobile')
                    session.headers.pop('sec-ch-ua-platform')
                session.headers.pop('ihg-language')
                session.headers.pop('ihg-sessionid')
                session.headers.pop('x-ihg-api-key')
                session.headers.pop('content-type')
                session.headers.update({
                    'accept': '*/*',
                    'access-control-request-method': 'POST',
                    'access-control-request-headers': 'content-type,ihg-language,ihg-sessionid,x-ihg-api-key',
                })
                preHotelDetailResponse = session.options(preHotelDetailUrl)
                if preHotelDetailResponse.status_code != 200:
                    message = {
                        "details": "Pre hotel detail search failed",
                    }
                    return self.build_response(success=False, data=message, status_code=preHotelDetailResponse.status_code)
                else:
                    logger.info(f"Pre hotel detail search succeeded with status code: {preHotelDetailResponse.status_code}")

                ############ New Req 9 ##################
                logger.info("Hotel detail search Requested....")
                hotelDetailUrl = preHotelDetailUrl
                hotelDetailpayload = "{\r\n    \"startDate\": \"2025-12-25\",\r\n    \"endDate\": \"2025-12-28\",\r\n    \"hotelMnemonics\": [\r\n        \"NYCHC\"\r\n    ],\r\n    \"rates\": {\r\n        \"ratePlanCodes\": [\r\n            {\r\n                \"internal\": \"IVAN1\"\r\n            },\r\n            {\r\n                \"internal\": \"IVAN3\"\r\n            },\r\n            {\r\n                \"internal\": \"IVAN5\"\r\n            },\r\n            {\r\n                \"internal\": \"IVAN6\"\r\n            },\r\n            {\r\n                \"internal\": \"IVAN7\"\r\n            },\r\n            {\r\n                \"internal\": \"IVANI\"\r\n            }\r\n        ]\r\n    },\r\n    \"products\": [\r\n        {\r\n            \"productCode\": \"SR\",\r\n            \"startDate\": \"2025-12-25\",\r\n            \"endDate\": \"2025-12-28\",\r\n            \"quantity\": 1,\r\n            \"guestCounts\": [\r\n                {\r\n                    \"otaCode\": \"AQC10\",\r\n                    \"count\": 1\r\n                }\r\n            ]\r\n        }\r\n    ],\r\n    \"options\": {\r\n        \"disabilityMode\": \"ACCESSIBLE_AND_NON_ACCESSIBLE\",\r\n        \"returnAdditionalRatePlanDescriptions\": true,\r\n        \"rateDetails\": {\r\n            \"includePackageDetails\": true\r\n        }\r\n    }\r\n}"
                session.headers.pop('access-control-request-method')
                session.headers.pop('access-control-request-headers')
                if self.sec_headers_flag:
                    session.headers.update({
                        'sec-ch-ua-platform': self._headers['sec-ch-ua-platform'],
                        'sec-ch-ua': self._headers['sec-ch-ua'],
                        'sec-ch-ua-mobile': self._headers['sec-ch-ua-mobile'],
                    })
                session.headers.update({
                    'ihg-language': 'en-US',
                    'ihg-sessionid': '85cff00e-d07d-4c40-9cd1-15f5ed6fcdfb',
                    'x-ihg-api-key': 'se9ym5iAzaW8pxfBjkmgbuGjJcr3Pj6Y',
                    'accept': 'application/json, text/plain, */*',
                    'content-type': 'application/json; charset=UTF-8'
                })
                hotelDetailResponse = session.post(hotelDetailUrl, data=hotelDetailpayload)
                if hotelDetailResponse.status_code != 200:
                    message = {
                        "details": "Hotel detail search failed",
                    }
                    return self.build_response(success=False, data=message, status_code=hotelDetailResponse.status_code)
                else:
                    logger.info(f"Hotel detail search succeeded with status code: {hotelDetailResponse.status_code}")
                    try:
                        data_json = {
                            "listpage":hotelResponse.json(),
                            "listpage_summary":listDataResponse.json(),
                            "finalpage":hotelDetailResponse.json()
                        }
                        return self.build_response(success=True, data=data_json, status_code=hotelDetailResponse.status_code)
                    except Exception as e:
                        message = {
                            "details": f"Response Json not available {e}"
                        }
                        return self.build_response(success=False, data=message, status_code=hotelDetailResponse.status_code)

            except Exception as ex:
                logging.error(f"Critical Error occurred: {ex}")
                message = {
                        "details": f"Critical Error: {ex}"
                    }
                return self.build_response(success=False, data=message, status_code=100)
            finally:
                logger.info("Closing application...")

        int_count += 1

# ---------------- Runner ----------------
if __name__ == "__main__":
    crawl = ExtractIhg()
    data = crawl.get_search_data(
        hotel_id="new york",
        check_in_date="2026-01-28",
        check_out_date="2026-01-29",
        guest_count=1
    )
    if data:
        print("API data fetched successfully")
    else:
        print("API data could not be fetched.")