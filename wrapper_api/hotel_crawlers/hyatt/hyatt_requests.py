from urllib.parse import quote

import aiohttp
import asyncio
from random_user_agent import get_random_sec_ch_headers, USER_AGENT
from random_cookie_getter import CrawlerRedisClient

class HyattExtractor:
    def __init__(self):
        self.session = None  # Will initialize later
        self.base_url = 'https://www.hyatt.com/shop/service/rooms/roomrates/'

    async def get_search_data(self, check_in_date, check_out_date, hotel_id, hotel_name):
        if not self.session:
            self.session = aiohttp.ClientSession()
        redis_client= CrawlerRedisClient(db=1)
        token = await redis_client.get_cookie()
        browser_family, headers = get_random_sec_ch_headers(USER_AGENT)
        encoded_hotel_name = quote(hotel_name, safe="")

        params = (
            f"?spiritCode={hotel_id}&rooms=1&adults=1&location={encoded_hotel_name}"
            f"&checkinDate={check_in_date}&checkoutDate={check_out_date}"
            "&kids=0&rate=Standard&suiteUpgrade=true"
        )

        url = self.base_url + hotel_id + params
        print(f"Requesting: {url}")

        req_headers = {
            'User-Agent': headers.get('user-agent') or headers.get('User-Agent'),
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Priority': 'u=1, i',
            'Referer': f'https://www.hyatt.com/shop/rooms/{hotel_id}?location={hotel_name}&checkinDate={check_in_date}&checkoutDate={check_out_date}&rooms=1&adults=1&kids=0&rate=Standard&rateFilter=woh',
            'sec-ch-ua': headers['sec-ch-ua'],
            'sec-ch-ua-platform': headers['sec-ch-ua-platform'],
            'sec-ch-ua-mobile': '?0',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Cookie': f'tkrm_alpekz_s1.3-ssn={token}; tkrm_alpekz_s1.3={token}; rate_filter=woh;',
        }

        async with self.session.get(url, headers=req_headers) as response:
            print(f"Status: {response.status}")
            data = await response.json(content_type=None)  # Hyatt might send `text/json` or no header
            print(data)
            return data

    async def close(self):
        if self.session:
            await self.session.close()


# --------------- Run Example -----------------
async def main():
    hyatt = HyattExtractor()
    await hyatt.get_search_data(
        check_in_date="2026-01-10",
        check_out_date="2026-01-12",
        hotel_id="yvrrv",
        hotel_name="Hyatt Regency Vancouver"
    )
    await hyatt.close()

if __name__ == "__main__":
    asyncio.run(main())
