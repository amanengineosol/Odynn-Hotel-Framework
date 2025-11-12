import requests

session = requests.Session()










url = "https://apis.ihg.com/graphql/v1/hotels"

payload = {}
headers = {
  'accept': '*/*',
  'access-control-request-method': 'POST',
  'access-control-request-headers': 'content-type,ihg-language,x-ihg-api-key',
  'origin': 'https://www.ihg.com',
  'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
  'sec-fetch-mode': 'cors',
  'sec-fetch-site': 'same-site',
  'sec-fetch-dest': 'empty',
  'referer': 'https://www.ihg.com/',
  'accept-encoding': 'gzip, deflate, br, zstd',
  'accept-language': 'en-US,en;q=0.9',
  'priority': 'u=1, i',
  'host': 'apis.ihg.com',
  # 'Cookie': '_abck=FDCFEA3853CEF8C3EFBFBBEE4C35DA40~-1~YAAQ5cIRYBbuDTKaAQAAizQicg7Xvi06L3rUBq5NLj/s3BSjTI+HmwvTmYyvl2XU+aPWQH3L4uecVgMUrHgPzHyPsHeDSJnRCpss9b/amlltg1LiCV5MLzYH7eEHzTNsASOwRUqu4X3afscdrj36JT+bJeK617/qmuYEzo8i1cNCFBSGNsJEF/TU46hHMyxO5lQUkqSmchJn94BPNyqMk8ecHCyMLBPF/+tSKLDwYw5WYjWPNH96JrwoYJaWbM8vVc1DjoiuIFbhjVCV8G3Bd3RiXLH5kKqNFZaOoTwH4+MVkM+vMb9VcPtOVk7z7eKDcabAGGJgacqQL4wP6/H20yooG1w//bar9RI3xwmK0GhK4rmhlO0yHuaeehhUOea2lcDaUHtjfGJ4ZowVueY1WsaANjW0lflMLZebYakry57dTpwz2Ac7hJK1PMvkfl5xqLa+oSx7LD9ql+559vCRVWo69pWaaM8tDYXmS4Eq/Nt77gE9686rTwUK5kVU5lCFydQTQCFI1BNrlFN5mVEOP4WSnBgyP7MsQ+v1HdREOBNHJBay69z1Ll0H7fXu+c6u2SUEYImusJZ19U6jo2RHcgc6rjIfq61pHFBJYBFY68wJYkTPNYHhMh46sJWru4lN+5QmfiHK0gb2WUdopY0a4QXJCT8AtQVMA/rjLy+mEZ3R15DfX5XJ~-1~-1~1762754432~AAQAAAAE%2f%2f%2f%2f%2fxUQEUMy1EwmPQGE3KsBxm8a+iMKgeiRu3omkNDUeUmBl89oML6rqJVfgOLCY1TuKz8RFg8BiSIN%2fj7JYgZvylBzs88mtCOZOXyC%2f7KQSVjtRSiV2lUYK17LNFMzDyFkeo8cAlU%3d~1762753115; ak_bmsc=3DF6CB814337FE48B694D9359CDC2A65~000000000000000000000000000000~YAAQ5cIRYBjuDTKaAQAAizQich07ZBeI3F5BCAILz5po/n94u1Bz6ytuN2Lmj+6gFojXpPtUnYrVCJHJEPlMQZJ10DF4r/x5NAyr1Fn9dJQZ150LfeLXYEapnJgyZJHzWcKKNb62rxAwTMNJNB7Q39KO3aQkdDiqHffrNmg96l4Thcq/ylyPwitaXlqaONTBXEWG22ByPDJVZ3ws+AtBTb3T/duf4g15Z7kLs2hwzili90s4pzS9maNXcv7YnL03CW3aYxdthxXuytC+Qkhr0oWBt+3YWlELmV1lmyiB2xbPEP+jvD5+RhZ0HZt1eawLnJkyvDNocRuBTEsZh4mSuG/OqEyZnpJzqKaj6TY7kIyNo1g7bOW5w70oVQRC; bm_sz=42F36A5EF79E9B092FAE4EC9A73345A7~YAAQ5cIRYBruDTKaAQAAizQich0wDc32LOYcSj0vyw4JR7sNIpcqeqNWVv1+2N1h9ZfXZ6t3BsnoKF5zZj5MEbbsRfYzTxd4tsRpKzTuYjkk2WoT8i2zC78R7PLnkOsIGsRCTaMU7xDuM+Cb3yi5OiBoqKxH3AuYLJJ4GnlYrB5bqKW0ZnS1u321fNs4dcfiR+17y4BsSsH85FnnN1DOCQCukdjcl4MBJq4Z0ifD5FBeR3+BhO/ZMg4lipsQtARty3K7dnJAsQDrQbDD9gSuCfPVcEZ8qX36HkHg82g21c6+LEfPiAZLHUOuri233Yw0KOU6WhGN+G2BZ5b1zNnJJimy6Us+BTEtJCJX~3555652~3421492'
}

response = session.options(url, headers=headers, data=payload)

print(response.text[:500])


url = "https://apis.ihg.com/graphql/v1/hotels"

payload = "{\r\n    \"operationName\": \"GetHotelDetails\",\r\n    \"variables\": {\r\n        \"detailsInput\": {\r\n            \"geoLocation\": {\r\n                \"lat\": 40.757996,\r\n                \"lon\": -73.985626,\r\n                \"radius\": 30\r\n            },\r\n            \"geoLocationDistance\": {\r\n                \"distanceType\": \"STRAIGHT_LINE\",\r\n                \"distanceUnit\": \"MI\"\r\n            },\r\n            \"size\": 120,\r\n            \"fallbackSearch\": {\r\n                \"minHotels\": 1,\r\n                \"maxRadius\": 100,\r\n                \"incrementRadiusBy\": 70\r\n            },\r\n            \"sortBy\": \"DISTANCE\"\r\n        },\r\n        \"mediaArgs\": {\r\n            \"formats\": [\r\n                {\r\n                    \"aspectHeight\": \"3\",\r\n                    \"aspectWidth\": \"4\"\r\n                },\r\n                {\r\n                    \"aspectHeight\": \"5\",\r\n                    \"aspectWidth\": \"16\"\r\n                }\r\n            ]\r\n        }\r\n    },\r\n    \"query\": \"query GetHotelDetails($detailsInput:HotelArgs$mediaArgs:MediaArgs){getHotels(input:$detailsInput){hotelInfo{hotelCode address{street1 street2 street3 city zip state{code name}country{name code}}location{boardTypes{boardType}}distanceFrom{kilometers miles}marketing{optOutDateWeb optInDateWeb marketingText{welcomeMessage}}brandInfo{SPBrandName brandCode brandName chainCode futureBrandInfo{rebrandingDate hotelName chainCode brandName brandCode}spTransitionalBrandIdentifier}greenEngage{certificationPrograms{certifiedByGloballyRecognizedSustainableProgram environmentalCertificationProgram{listItem}}lowCarbon{lowCarbonHotelDescription isLowCarbonHotel}lowCarbonReady{lowCarbonReadyHotelDescription isLowCarbonReadyHotel}}room{hotelHighlights{hotelDisclaimer}}badges{name id}facilities{name id}parking{complimentaryDailySelfParking parkingDescription carParkingAvailable valetParkingAvailable}policies{pet{petsAllowed guideDogsOrServiceAnimalsAllowed description}}stripes{id name}renovationAlertsList{alertType flagEndDate flagStartDate other}profile{name webNonBrandedHotelLogo{url}seoCity nonIhgCrsUrl hotelLogo{originalUrl}averageReview tpiLevel2Violator primaryImageUrl{originalUrl}latLong{lon lat}hotelStatus preSellDate dateOpened totalReviews vatIncluded}media(input:$mediaArgs){primaryPhotos{allPhotos{type primary caption originalUrl formats{url aspectHeight aspectWidth}}}}foodAndBeverage{complimentaryBreakfastDetails{complimentaryGrabAndGoBreakfast}}restaurant{onSiteRestaurantsCount}tax{taxAndFeeDetail serviceCharge{startAndEndDate{startDate endDate}description}}}}}\"\r\n}"
headers = {
  'content-length': '2002',
  'sec-ch-ua-platform': '"Windows"',
  'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
  'ihg-language': 'en-US',
  'sec-ch-ua-mobile': '?0',
  'x-ihg-api-key': 'se9ym5iAzaW8pxfBjkmgbuGjJcr3Pj6Y',
  'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
  'accept': 'application/json, text/plain, */*',
  'content-type': 'application/json; charset=UTF-8',
  'origin': 'https://www.ihg.com',
  'sec-fetch-site': 'same-site',
  'sec-fetch-mode': 'cors',
  'sec-fetch-dest': 'empty',
  'referer': 'https://www.ihg.com/',
  'accept-encoding': 'gzip, deflate, br, zstd',
  'accept-language': 'en-US,en;q=0.9',
  'priority': 'u=1, i',
  'host': 'apis.ihg.com',
  # 'Cookie': '_abck=FDCFEA3853CEF8C3EFBFBBEE4C35DA40~-1~YAAQ5cIRYBbuDTKaAQAAizQicg7Xvi06L3rUBq5NLj/s3BSjTI+HmwvTmYyvl2XU+aPWQH3L4uecVgMUrHgPzHyPsHeDSJnRCpss9b/amlltg1LiCV5MLzYH7eEHzTNsASOwRUqu4X3afscdrj36JT+bJeK617/qmuYEzo8i1cNCFBSGNsJEF/TU46hHMyxO5lQUkqSmchJn94BPNyqMk8ecHCyMLBPF/+tSKLDwYw5WYjWPNH96JrwoYJaWbM8vVc1DjoiuIFbhjVCV8G3Bd3RiXLH5kKqNFZaOoTwH4+MVkM+vMb9VcPtOVk7z7eKDcabAGGJgacqQL4wP6/H20yooG1w//bar9RI3xwmK0GhK4rmhlO0yHuaeehhUOea2lcDaUHtjfGJ4ZowVueY1WsaANjW0lflMLZebYakry57dTpwz2Ac7hJK1PMvkfl5xqLa+oSx7LD9ql+559vCRVWo69pWaaM8tDYXmS4Eq/Nt77gE9686rTwUK5kVU5lCFydQTQCFI1BNrlFN5mVEOP4WSnBgyP7MsQ+v1HdREOBNHJBay69z1Ll0H7fXu+c6u2SUEYImusJZ19U6jo2RHcgc6rjIfq61pHFBJYBFY68wJYkTPNYHhMh46sJWru4lN+5QmfiHK0gb2WUdopY0a4QXJCT8AtQVMA/rjLy+mEZ3R15DfX5XJ~-1~-1~1762754432~AAQAAAAE%2f%2f%2f%2f%2fxUQEUMy1EwmPQGE3KsBxm8a+iMKgeiRu3omkNDUeUmBl89oML6rqJVfgOLCY1TuKz8RFg8BiSIN%2fj7JYgZvylBzs88mtCOZOXyC%2f7KQSVjtRSiV2lUYK17LNFMzDyFkeo8cAlU%3d~1762753115; ak_bmsc=3DF6CB814337FE48B694D9359CDC2A65~000000000000000000000000000000~YAAQ5cIRYBjuDTKaAQAAizQich07ZBeI3F5BCAILz5po/n94u1Bz6ytuN2Lmj+6gFojXpPtUnYrVCJHJEPlMQZJ10DF4r/x5NAyr1Fn9dJQZ150LfeLXYEapnJgyZJHzWcKKNb62rxAwTMNJNB7Q39KO3aQkdDiqHffrNmg96l4Thcq/ylyPwitaXlqaONTBXEWG22ByPDJVZ3ws+AtBTb3T/duf4g15Z7kLs2hwzili90s4pzS9maNXcv7YnL03CW3aYxdthxXuytC+Qkhr0oWBt+3YWlELmV1lmyiB2xbPEP+jvD5+RhZ0HZt1eawLnJkyvDNocRuBTEsZh4mSuG/OqEyZnpJzqKaj6TY7kIyNo1g7bOW5w70oVQRC; bm_sv=9B0F4D1649CF70AA1EA7404BE8A4AB3A~YAAQ5sIRYAjPDTOaAQAAWFojch3Fk9MGmaG7NNsjESmRrroozwF+JclA9BpELIhAoq/nQ5ga5hXEjb6AGkMMQ1VG2IgvK7IcI8a4NuRo6+yjC4030U6ujtEwcFvP69ZX3ih3X5J4l9G9yfufGG4Xl3eI1w2q4i/bIdzltQSG0dahJ5Pv1NE+HvutSKqZ8MMCevPLXiwPd5w5KjytrEdstyPSkICoICaxynmm+Dj+FiUBGmtnCfKlqe5wzsik~1; bm_sz=42F36A5EF79E9B092FAE4EC9A73345A7~YAAQ5cIRYBruDTKaAQAAizQich0wDc32LOYcSj0vyw4JR7sNIpcqeqNWVv1+2N1h9ZfXZ6t3BsnoKF5zZj5MEbbsRfYzTxd4tsRpKzTuYjkk2WoT8i2zC78R7PLnkOsIGsRCTaMU7xDuM+Cb3yi5OiBoqKxH3AuYLJJ4GnlYrB5bqKW0ZnS1u321fNs4dcfiR+17y4BsSsH85FnnN1DOCQCukdjcl4MBJq4Z0ifD5FBeR3+BhO/ZMg4lipsQtARty3K7dnJAsQDrQbDD9gSuCfPVcEZ8qX36HkHg82g21c6+LEfPiAZLHUOuri233Yw0KOU6WhGN+G2BZ5b1zNnJJimy6Us+BTEtJCJX~3555652~3421492'
}

response = session.post( url, headers=headers, data=payload)

print(response.text[:500])



# import requests
#
# url = "https://apis.ihg.com/availability/v3/hotels/offers?fieldset=rateDetails,rateDetails.policies,rateDetails.bonusRates,rateDetails.upsells,alternatePayments"
#
# payload = "{\"startDate\":\"2025-12-25\",\"endDate\":\"2025-12-31\",\"hotelMnemonics\":[\"NYCBA\"],\"rates\":{\"ratePlanCodes\":[{\"internal\":\"IVAN1\"},{\"internal\":\"IVAN3\"},{\"internal\":\"IVAN5\"},{\"internal\":\"IVAN6\"},{\"internal\":\"IVAN7\"},{\"internal\":\"IVANI\"}]},\"products\":[{\"productCode\":\"SR\",\"startDate\":\"2025-12-25\",\"endDate\":\"2025-12-31\",\"quantity\":1,\"guestCounts\":[{\"otaCode\":\"AQC10\",\"count\":1}]}],\"options\":{\"disabilityMode\":\"ACCESSIBLE_AND_NON_ACCESSIBLE\",\"returnAdditionalRatePlanDescriptions\":true,\"rateDetails\":{\"includePackageDetails\":true}}}"
# headers = {
#   'host': 'apis.ihg.com',
#   'content-length': '521',
#   'sec-ch-ua-platform': '"Windows"',
#   'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
#   'ihg-language': 'en-US',
#   'sec-ch-ua-mobile': '?0',
#   # 'ihg-sessionid': '1f1bdf73-00f4-410d-9da5-269d1f9fa36b',
#   'x-ihg-api-key': 'se9ym5iAzaW8pxfBjkmgbuGjJcr3Pj6Y',
#   'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
#   'accept': 'application/json, text/plain, */*',
#   'content-type': 'application/json; charset=UTF-8',
#   'origin': 'https://www.ihg.com',
#   'sec-fetch-site': 'same-site',
#   'sec-fetch-mode': 'cors',
#   'sec-fetch-dest': 'empty',
#   'referer': 'https://www.ihg.com/',
#   'accept-encoding': 'gzip, deflate, br, zstd',
#   'accept-language': 'en-US,en;q=0.9',
#   'priority': 'u=1, i',
#   # 'cookie': 'ak_bmsc=51F896459395FE86AABCEB48595DE067~000000000000000000000000000000~YAAQbW/ZF+0QhFyaAQAA1hAjbB0UKVtzGvxFkGF26BdF/LJFW+DC4NAsRRlKrld1s1Yh5CF+aqUZ7OXDa2KBWex5qd41/ZHwwUKJw9GqXTuabEdDobspnzLWzDBYwEDFpGreFJR6GopoLGF9x5y7LJXOeee//UwU8SKovXJzdqdxSWonZJGVYxdJuwPWG9V+KZnw9w4PAhzasGWKcwjXrfuYSkzPp5RGzN4qsnTCjqwqBoxC+izwiBYveSnILg2BzEVETVGyOdASUoqzxAVrUgWhdsei2n4k9IPghXzL0yXSsvqE2xyZucM881E/rsYPx9aNNSSkw508mNsXi3xY5LYQiMy+JQSc5/LAp3Z3g4JWlnseOX9XrnuGAkr7VNHyxdSqrBCuKZDo9A==; AMCV_8EAD67C25245B1870A490D4C%40AdobeOrg=179643557%7CMCIDTS%7C20403%7CMCMID%7C43292804243917805648644415823109086636%7CvVersion%7C5.5.0; at_check=true; notice_behavior=implied,us; s_inv=0; s_vnc365=1794286832553%26vn%3D1; s_ivc=true; s_ev37=PDSEA-_-G_F-IMEA_FS-SWA_H-IMEA_HS-SWA_6C_BSF_EXM_CORE-IHG_EN; s_ev38=PDSEA-_-G_F-IMEA_FS-SWA_H-IMEA_HS-SWA_6C_BSF_EXM_CORE-IHG_EN; s_ev66=PDSEA-_-G_F-IMEA_FS-SWA_H-IMEA_HS-SWA_6C_BSF_EXM_CORE-IHG_EN; s_cc=true; gig_bootstrap_4_jpzahMO4CBnl9Elopzfr0A=identity_ver4; _fbp=fb.1.1762750834277.605601524406015478; _gcl_au=1.1.1660376761.1762750834; _gcl_aw=GCL.1762750833883.EAIaIQobChMIje6DwebmkAMVTZxQBh2Czi4DEAAYASAAEgL2S_D_BwE; _pin_unauth=dWlkPU9HWmhNV0U0TlRjdE1HVmxZUzAwT1RjM0xUazRaakV0WlRBNFpEWXpOamRtTlRkaw; bm_sz=D85C268C59DF4D8F86533EFE95F37B5A~YAAQbW/ZF0YVhFyaAQAA58MkbB0w6SxJcYHRT6PG2tEjk35wC43JB6QlUEdO9LaWmiOk+4rggLv5tQ8EJh+XQJZZDhKSI3EweMeR3inIBDCUC+C0mJTAVAYptZWdPDOEELyHKOXQs/Cin4CaRUjq3FvS8ypYvC3KSqBnv7yUjXfa39bNzAWSOZbHf50h55wjC36aAYFKH7LBfdhzPRujz0IBdrH3ICF7x0sDgkbqqiI0jo/RKHBVXYFG6fS0xOenhIMtRKkSdrtXSbrYkoJsJsJC71dtR/87HoLlLyGcHrd2FlfRufnnvTvGztR8YWtKb9aym/gdxqRbkN3D4JFbHZBaiUkQltWAddr9qr1FdJUIfqe6EhPCR0tnukgO4qUS4Vu/3r/JqvVuf6WwkK8pEWBq3F5xN16fkVHG8HzmHM65vhw=~3422008~4535873; prevPageName=6C%3A%20SEARCH%20RESULTS; ADRUM=s~1762752404205&r~aHR0cHMlM0ElMkYlMkZ3d3cuaWhnLmNvbSUyRmhvdGVscyUyRmdiJTJGZW4lMkZmaW5kLWhvdGVscyUyRmhvdGVsLXNlYXJjaCUzRmhhc2glM0QtMjEyNjgyMTU1MA==; forterToken=42187ca64a9e4d2a8fd2cbf01460b9db_1762752405605__UDF43-m4_15ck_; _uetsid=30c31410bdf211f0ab88b3ae2cf25f94; _uetvid=30c34660bdf211f0a954e9e1e024fd17; mbox=session#b5573fee81154905979cef7a0ddf8e3b#1762754271|PC#b5573fee81154905979cef7a0ddf8e3b.41_0#1825997210; s_tslv=1762752411616; notice_preferences=3:; TAconsentID=9ae656be-fac1-4ce9-b602-e6a6eb0b507e; notice_gdpr_prefs=0,1,2,3:; notice_poptime=1720533300000; cmapi_gtm_bl=; cmapi_cookie_privacy=permit 1,2,3,4; bm_sv=6C651A9D58CD71A5F45583F9F3047513~YAAQ5cIRYBpjpTGaAQAAUBg8bB3yz/+GkM9BvtEXzk/c9JSRMV281Ul+6FnNKFKvIKu9cDHFV5IRtqMe4b4yiM4bePHRyWUMF6We9NIuHrMGr8SrdimclfUPXnaxsr44h23pBFogNVZSlyROGfa14o/drUTrjnDlU5I8M4jQqas3vhGyKjwhHuNYCG5nxQ4LYn9aTaNHEbARM6vaOGn8hDZNMeifQmDJimWfVvGD+2h1+vGyyH4UXp8bl9lRVQ==~1; s_sq=ihgusglobal%3D%2526c.%2526a.%2526activitymap.%2526page%253D6C%25253A%252520SEARCH%252520RESULTS%2526link%253DSelect%252520Hotel%2526region%253DNYCBA%2526pageIDType%253D1%2526.activitymap%2526.a%2526.c%2526pid%253D6C%25253A%252520SEARCH%252520RESULTS%2526pidt%253D1%2526oid%253DSelect%252520Hotel%2526oidt%253D3%2526ot%253DSUBMIT; _abck=FDCFEA3853CEF8C3EFBFBBEE4C35DA40~-1~YAAQbW/ZF0FZhFyaAQAAfQtFbA7kgQkX4Vxqd0SRL/YzQF8FBiliDxdv0+Wej0egbHw+gex7PCYShQPjzADZQBRJ3mvrNqkEw564ECUf+TXkG6pm1mz/nB95nPpX0oKmYUbLJQ16Zij3cCmYoIyeYxKvI3JH/wi0sNcvWEEoASOOnDRCnW0d7MF5aSu5USHO2OKQDzHEDMiJRhsI8ycMVwIMWCBHlcaAK2KFwqpsyt4rKFYq0yK/Oy9dO1HaX3Wdslad+HbZoaMFFyCylHcM0wGRvsTq8LlNDSnW+E5NuXOGidfk6aaaS6iMWsIKsVEnOOGOB15gKF1DfsmysJSIM7e8olLWNHtW6fsZoF/xcGrcSNZpbadz3ItsHrVgyLGRG1pUlLGTIKD5Xh2kMQG0dNZTyFXs8N7VZqx1qKaXR/Bk7Vh+Cx8olJaedhqkrRKktL7/Qui17EMtU2hyro0o1jx2+wYpDw10Ic/Qz7CIr/WS+1RMhI4yLE0GURrmpD3sK6hzY0Lyd5o2I5Nu6T6Tiq5mEs6MAjoiVeFj0a9iRL9Noo/bDXxo5OJU08GXxXy8CHk1abpbTxRTZbKP/DTGhhXJahfBVexa4SgkQO0ZN+twz5cy8Ae9Bp7cZGhXKchscHZdR8VPz2K1XHaNPlWVswf7HCWVdJD6HWzWbuBCFKeHI2NEtuw=~-1~-1~1762754432~AAQAAAAE%2f%2f%2f%2f%2fxUQEUMy1EwmPQGE3KsBxm8a+iMKgeiRu3omkNDUeUmBl89oML6rqJVfgOLCY1TuKz8RFg8BiSIN%2fj7JYgZvylBzs88mtCOZOXyC%2f7KQSVjtRSiV2lUYK17LNFMzDyFkeo8cAlU%3d~1762753115; _abck=FDCFEA3853CEF8C3EFBFBBEE4C35DA40~-1~YAAQ5sIRYHtnwjKaAQAA/JZYbA7TeJBTayt4+C4+Sa01WvasP3uSUOj1mNwZzQbBAo05HLZYBJvFS2w/LSD2NXYBJpw7y1w62yHETSCpQm6h/VmpSWnlBmBfi0d0PTnleNJ4AQnCW9B3x0RaNrv+ITv87d6scHtqh2Z5u/mKQmkQniqq2HvJxjiJgg0OVBclrCS14TWcmqibajPV4Hxndo0ULABf1cbbfwZaq+Tm9KqxcSBuFeRUICD2ZDa1t4rX0UC5ndKIDJYcX7TATlki9K+zmGfMN30eAQ/DlNoJig39HdaJZ40m7SGYl3pDu3jO9wUIcr7MDbM1VaZGBt+7s6vfqzLw+zGKvz55378hfI2dW4X1h9qSMQ5l+bEanGk6ABnm2Lg12GoWe126r1oCjdh8KX20LaYKGo3hmnFZP5E4GO/nbY4XepqlcQupboiwRO85z3AgbdznsaWWpf30m78OQM/yDbbl+3E/AHokVlyLEzs5Y4hug58uZC10ObY5V2FbuFkeDDMWVT1Xq3nL8xFX45Ye6ornpD9ZaLn0n6MC74qlt0dd+GhkoywLwcASFEbxk5lgoQWSxQ+mjtJUPbTXxgPZbbJUM9L58I9LfBwUEbsLASGX+3/fkCDVWaC9KZhWAQb2SeNJEHMxdI1U1jSoLaHvly1paD2X+AdU/xcC83ASOKM=~0~-1~1762754432~AAQAAAAE%2f%2f%2f%2f%2fxUQEUMy1EwmPQGE3KsBxm8a+iMKgeiRu3omkNDUeUmBl89oML6rqJVfgOLCY1TuKz8RFg8BiSIN%2fj7JYgZvylBzs88mtCOZOXyC%2f7KQSVjtRSiV2lUYK17LNFMzDyFkeo8cAlU%3d~1762753115; bm_sv=6C651A9D58CD71A5F45583F9F3047513~YAAQ5sIRYHxnwjKaAQAA/JZYbB1pFY3TFigZ7XGm9CCWqrDp8jZ5R2ozh2j0K5FyiGmtq2pUhkMo/0DeBFqBQbDVZ335JOcK22E6yZFU2biF7l/t0wMaqCx44siMNZMlTda/BBQuuEgYi6rCxb3alFTa46+EWA86a4JGAvaLWkrVW+4gumGRndGIMOwcFkp/W+pEOROsWz5w7hU4hRu4z3Y+OSe3JbFmLZ+9FCnKY4lEDKeDhS16KQgK2T/vuQ==~1; ADRUM_BT1=R:20|i:460240|e:301|t:1762754335270; ADRUM_BTa=R:20|g:9400e072-7dac-41c1-8331-1bb8a5717c05|n:ihg-prod_b3f2c515-18e4-4179-bf89-bc1bae74cb38'
# }
#
# response = requests.request("POST", url, headers=headers, data=payload)
#
# print(response.text)
