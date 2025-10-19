import redis
import os
from dotenv import load_dotenv

load_dotenv()
_connections = {}

def get_redis_client(db=1):
    if db not in _connections:
        _connections[db] = redis.Redis(host='localhost', port=int(os.getenv('REDIS_PORT')), db=db)
    return _connections[db]
