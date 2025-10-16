from urllib.parse import quote
import aiohttp
import asyncio
from datetime import datetime
from .random_user_agent import get_random_sec_ch_headers, USER_AGENT
from .random_cookie_getter import CrawlerRedisClient
from .proxy_manager import ProxyManager

class HyattExtractor:
    def __init__(self):
        self.session = None  # Will initialize later
        self.base_url = 'https://www.hyatt.com/shop/service/rooms/roomrates/'
        self.proxy_manager = ProxyManager()

    async def build_response(self, success: bool, data: any, status_code: int):
        return {
            "success": success,
            "data": data,
            "status_code": status_code
        }

    async def get_search_data(self, hotel_id, check_in_date, check_out_date, guest_count, max_retries=3):
        if not self.session:
            self.session = aiohttp.ClientSession()
        proxy_url = self.proxy_manager.fetch_proxy()
        proxies = {
            "http": proxy_url,
            "https": proxy_url
        }
        redis_client= CrawlerRedisClient(db=1)
        token = await redis_client.get_cookie()
        print(token)
        print(type(token))
        browser_family, headers = get_random_sec_ch_headers(USER_AGENT)
        print("browser_family", browser_family)
        print("Headers", headers)

        # Validate inputs
        check_in = datetime.strptime(check_in_date, "%Y-%m-%d")
        check_out = datetime.strptime(check_out_date, "%Y-%m-%d")
        length_of_stay = (check_out - check_in).days
        if not hotel_id or length_of_stay <= 0 or guest_count <= 0:
            raise ValueError("hotel_id/no_of_stays/guest must have valid values.")

        hotel_id_name = hotel_id
        parts = hotel_id_name.split("-", 1)
        hotel_id = parts[0].strip()
        hotel_name = parts[1].strip() if len(parts) > 1 else ""
        encoded_hotel_name = hotel_name.replace(" ","%20")

        params = (
            f"?spiritCode={hotel_id}&rooms=1&adults=1&location={encoded_hotel_name}"
            f"&checkinDate={check_in_date}&checkoutDate={check_out_date}"
            "&kids=0&rate=Standard&suiteUpgrade=true"
        )

        url = self.base_url + hotel_id + params
        print(f"Requesting: {url}")

        req_headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            'accept-language': 'en-US,en;q=0.9',
            "accept-encoding": "gzip, deflate, br",
            'pragma': 'no-cache',
            'referer': f'https://www.hyatt.com/shop/rooms/{hotel_id}?location={hotel_name}&checkinDate={check_in_date}&checkoutDate={check_out_date}&rooms=1&adults=1&kids=0&rate=Standard&rateFilter=woh',
            'sec-ch-ua': f'{headers.get("sec-ch-ua")};',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': f'{headers.get("sec-ch-ua-platform")}',
            # 'sec-ch-ua-full-version-list': f'{headers.get("sec-ch-ua-full-version-list")}',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            "connection": "keep-alive",
            'user-agent': headers.get('user-agent'),
            'Cookie': f'tkrm_alpekz_s1.3-ssn={token}; tkrm_alpekz_s1.3={token}; rate_filter=woh',
        }
        print("using.........",headers.get('user-agent'))

        async with self.session.get(url, headers=req_headers, proxy=proxy_url) as response:
            print(f"Status: {response.status}")
            print(response.request_info)
            if response.status == 200:
                data = await response.json()
                return await self.build_response(success=True, data=data, status_code=response.status)
            elif response.status == 404:
                return await self.build_response(success=False, data=await response.text(), status_code=404)
            elif response.status == 429:
                return await self.build_response(success=False, data=await response.text(), status_code=429)
            elif response.status == 500:
                return await self.build_response(success=False, data=await response.text(), status_code=500)
            else:
                return await self.build_response(success=False, data=await response.text(), status_code=response.status)


    async def close(self):
        if self.session:
            await self.session.close()


# --------------- Run Example -----------------
async def main():
    hyatt = HyattExtractor()
    await hyatt.get_search_data(
        check_in_date="2026-01-10",
        check_out_date="2026-01-12",
        hotel_id="yvrrv-Hyatt Regency Vancouver",
        guest_count=1
    )
    await hyatt.close()

if __name__ == "__main__":
    asyncio.run(main())
