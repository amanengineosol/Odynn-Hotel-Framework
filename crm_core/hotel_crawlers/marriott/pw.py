import requests
import json

url = "https://www.marriott.com/mi/query/PhoenixBookSearchProductsByProperty"

headers = {
    "host": "www.marriott.com",
    "application-name": "book",
    "sec-ch-ua-platform": "\"Windows\"",
    "graphql-operation-name": "PhoenixBookSearchProductsByProperty",
    "x-dtpc": "10$552354512_401h5vDANFWRBPCSQTETAEOSRKRMFMKELHHQOH-0e0",
    "sec-ch-ua": "\"Chromium\";v=\"140\", \"Not=A?Brand\";v=\"24\", \"Google Chrome\";v=\"140\"",
    "sec-ch-ua-mobile": "?0",
    "graphql-force-safelisting": "true",
    "accept": "*/*",
    "apollographql-client-version": "1",
    "content-type": "application/json",
    "apollographql-client-name": "phoenix_book",
    "graphql-require-safelisting": "true",
    "accept-language": "en-US",
    "graphql-operation-signature": "a1079a703a2d21d82c0c65e4337271c3029c69028c6189830f30882170075756",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    "origin": "https://www.marriott.com",
    "sec-fetch-site": "same-origin",
    "sec-fetch-mode": "cors",
    "sec-fetch-dest": "empty",
    "referer": "https://www.marriott.com/reservation/rateListMenu.mi",
    "accept-encoding": "gzip, deflate, br, zstd",
    "priority": "u=1, i",
    "cookie": "sessionID=C03B9195-8EE5-55D1-895D-3EF0F38BDA07; Affiliate=pId=intbppc; JVMID=mi-interceptor-app-blue; MI_SITE=prod17; ..."  # <-- put your full cookie string here
}

payload = {
    "operationName": "PhoenixBookSearchProductsByProperty",
    "variables": {
        "search": {
            "options": {
                "startDate": "2025-11-04",
                "endDate": "2025-11-08",
                "quantity": 1,
                "numberInParty": 1,
                "childAges": [],
                "productRoomType": ["ALL"],
                "productStatusType": ["AVAILABLE"],
                "rateRequestTypes": [
                    {"value": "", "type": "STANDARD"},
                    {"value": "", "type": "PREPAY"},
                    {"value": "", "type": "PACKAGES"},
                    {"value": "MRM", "type": "CLUSTER"},
                    {"value": "", "type": "REDEMPTION"}
                ],
                "isErsProperty": False
            },
            "propertyId": "SNABP"
        },
        "offset": 0,
        "limit": 150
    },
    "query": """query PhoenixBookSearchProductsByProperty($search: ProductByPropertySearchInput, $offset: Int, $limit: Int) {
      searchProductsByProperty(search: $search, offset: $offset, limit: $limit) {
        edges {
          node {
            ... on HotelRoom {
              basicInformation { name description }
              rates { name rateAmountsByMode { averageNightlyRatePerUnit { amount { origin { amount currency }}}}}
            }
          }
        }
        total
      }
    }"""
}

response = requests.post(url, headers=headers, data=json.dumps(payload))

print(f"Status code: {response.status_code}")
print("Response headers:", response.headers.get("content-type"))
print("Response text (first 500 chars):\n", response.text[:500])
