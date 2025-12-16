import redis
import os

_POOLS = {}

def get_redis_client(db=0):
    if db not in _POOLS:
        pool = redis.ConnectionPool(
            host=os.getenv("REDIS_HOST"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=db,
            max_connections=50,
            socket_timeout=2,
            socket_connect_timeout=2,
            retry_on_timeout=True,
            health_check_interval=30,
        )
        _POOLS[db] = redis.Redis(connection_pool=pool)
    return _POOLS[db]
