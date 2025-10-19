import uuid
import logging
import json
from redis_client import get_redis_client

class CrawlerRedisClient:
    def __init__(self, db):
        self.logger = logging.getLogger(__name__)
        self.client = get_redis_client(db)


    def generate_uuid_hash(self) -> str:
        return uuid.uuid4().hex

    def save_cookie(self, response, expiration: int = 3600):
        print(response)
        key = self.generate_uuid_hash()
        self.client.set(key, json.dumps(response), ex=expiration)
