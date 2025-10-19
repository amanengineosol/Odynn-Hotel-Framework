import json
import logging
import asyncio
import os
from dotenv import load_dotenv
from redis.exceptions import RedisError
from redis.asyncio import Redis

load_dotenv()

class CrawlerRedisClient:
    def __init__(self, db: int):
        # Adjust connection parameters as needed
        self.client = Redis(
            host=os.getenv('REDIS_HOST','localhost'),
            port=os.getenv('REDIS_PORT','6379'),
            db=db,
            decode_responses=True
        )
        self.logger = logging.getLogger(__name__)

    async def get_cookie(self):

        print(os.getenv('REDIS_HOST'), os.getenv('REDIS_PORT'))
        try:
            key = await self.client.randomkey()
            if not key:
                self.logger.warning("No keys available in Redis cache")
                return None

            raw_data = await self.client.get(key)
            if raw_data:
                self.logger.info(f"Data fetched from Redis with key: {key}")
                return json.loads(raw_data)

            return None

        except RedisError as e:
            self.logger.error(f"Redis error fetching data: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error in get_cookie: {e}")
            return None

    async def close(self):
        await self.client.aclose()


# async def test():
#     redis_client = CrawlerRedisClient(db=1)
#     cookie = await redis_client.get_cookie()
#     print("Fetched Cookie:", cookie)
#     await redis_client.close()
#
# asyncio.run(test())
