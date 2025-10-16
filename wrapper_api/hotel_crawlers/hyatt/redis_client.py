import redis
import os

_connections = {}

def get_redis_client(db=1):
    if db not in _connections:
        _connections[db] = redis.Redis(host=os.getenv('REDIS_HOST'), port=int(os.getenv('REDIS_PORT')), db=db)
    return _connections[db]
