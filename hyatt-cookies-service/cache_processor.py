from redis_client import get_redis_client
import json
import uuid
import logging
from redis.exceptions import RedisError


class CrawlerRedisClient:

    def __init__(self, db):
        self.logger = logging.getLogger(__name__)
        self.client = get_redis_client(db)

    def generate_uuid_hash(self) -> str:
        """Generate a unique UUID key."""
        return uuid.uuid4().hex

    def save_cookie(self, response, expiration: int = 3600):
        key = self.generate_uuid_hash()
        self.client.set(key, json.dumps(response), ex=expiration)

    def get_cookie(self):
        try:
            key = self.client.randomkey()
            if not key:
                self.logger.warning("No keys available in Redis cache")
                return None

            raw_data = self.client.get(key)
            if raw_data:
                self.logger.info(f"Data fetched from Redis with key: {key}")
                value = json.loads(raw_data)
                return value
            return None
        except RedisError as e:
            self.logger.error(f"Redis error fetching data: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error in get_from_redis: {e}")
            return None

    def redis_db_count(self) -> int:
        """Get count of keys in current Redis database."""
        try:
            count = self.client.dbsize()
            self.logger.info(f"Redis DB count: {count}")
            return count
        except RedisError as e:
            self.logger.error(f"Redis error getting DB count: {e}")
            return 0
        except Exception as e:
            self.logger.error(f"Unexpected error in redis_db_count: {e}")
            return 0

    def delete_key(self, key):
        """
        Delete the given key from Redis.
        Returns True if deletion was successful, False otherwise.
        """
        try:
            deleted_count = self.client.delete(key)
            if deleted_count > 0:
                self.logger.info(f"Deleted key '{key}' from Redis")
                return True
            else:
                self.logger.warning(f"Key '{key}' not found for deletion")
                return False
        except RedisError as e:
            self.logger.error(f"Redis error deleting key '{key}': {e}")
            return False
