import redis
import os
from dotenv import load_dotenv
load_dotenv()

_connections = {}

def get_redis_client(db=1):
    if db not in _connections:
        _connections[db] = redis.Redis(
            host=os.getenv('REDIS_HOST'),
            port=os.getenv('REDIS_PORT'),
            db=db
        )
    print(os.getenv('REDIS_HOST'), os.getenv('REDIS_PORT'))
    return _connections[db]
