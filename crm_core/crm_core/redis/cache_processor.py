from .domain_parameter_map import DOMAIN_PARAMETER_MAP
from .redis_client import get_redis_client
import json

class CrawlerRedisClient:
    
    def __init__(self, db):
        self.client = get_redis_client(db)
   
    def build_key(self, crawler_name, parameter, domain):
        key_parts = [crawler_name]
        param_fields = DOMAIN_PARAMETER_MAP.get(domain, [])
        for field in param_fields:
            key_parts.append(str(parameter.get(field, "")))
        return ":".join(p for p in key_parts if p)
    
    def set_crawler_response(self, key, response, expiration:int= 300):
        self.client.set(key, json.dumps(response), ex=expiration)
        
    # def set_crawler_name(self, key, response):
    #     self.client.set(key, "||".join(response))
        
    def get_crawler_response(self, key):
        value =  self.client.get(key)
        return json.loads(value) if value else None
    
    # def get_crawler_name(self, key):
    #     value =  self.client.get(key)
    #     return value if value else None
