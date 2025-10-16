'''
Background scheduler that checks Redis DB size every minute.
If the size is less than 5, it calls `get_tokens(count)` from tokenManager.py.
'''
import asyncio
import logging
from cache_processor import CrawlerRedisClient
from cookies_fetcher import CookiesFetcher


class BotScheduler:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cookie_fetcher = CookiesFetcher()
        self.redis_client = CrawlerRedisClient(1)

    async def generate_cookies(self):
        try:
            db_size = self.redis_client.redis_db_count()
            self.logger.info(f"Redis DB size: {db_size}")

            if db_size < 15:
                await self.cookie_fetcher.get_cookies()
            else:
                self.logger.info("DB size is >= 15, no action taken.")
        except Exception as e:
            self.logger.error(f"Error checking Redis: {e}")

    async def run_scheduler(self, interval=60):
        while True:
            await self.generate_cookies()
            await asyncio.sleep(interval)


if __name__ == "__main__":
    asyncio.run(BotScheduler().run_scheduler())