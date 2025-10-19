# from fastapi import FastAPI
# # from schema import PostCookieOne, PostCookiesList
# # from cache_utils import CrawlerRedisClient
# from redis_om import JsonModel, get_redis_connection
# from typing import List, Optional, Dict, Any
#
# # cache_client = CrawlerRedisClient(db=1)
# REDIS_DATA_URL = "redis://localhost:6379/1"
#
# app = FastAPI(
#     title="Hyatt Cookie Manager"
# )
#
#
# class PostCookiesList(JsonModel):
#     cookie_list: List[Dict[str:Any]]
#     browser_name: str
#
#     class Meta:
#         database = redis_connection
#
#
#
# @app.post("/platform/set-cookies")
# async def set_multiple_cookies(cookie_list: PostCookiesList):
#     cookie_list.save()
#
#
# @app.on_event("startup")
# async def startup():
#     PostCookiesList.Meta.database = get_redis_connection(
#         url=REDIS_DATA_URL,
#         decode_responses=True
#     )
import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from dotenv import load_dotenv
import redis
import json

load_dotenv()
REDIS_URL = f"redis://{os.getenv('REDIS_HOST')}:6379/1"
EXPIRE_SECONDS = 8 * 60 * 60  # 8 hours

app = FastAPI(title="Hyatt Cookie Manager")


# Use Pydantic for validation (not redis-om)
class PostCookiesList(BaseModel):
    cookie_list: List[Dict[str, Any]]
    browser_name: str


# Global Redis client
redis_client = None


@app.post("/platform/set-cookies")
async def set_multiple_cookies(cookie_data: PostCookiesList):
    # Generate unique key
    import uuid
    pk = str(uuid.uuid4())

    # Store as JSON string with expiration
    key = f"cookies:{pk}"
    redis_client.setex(
        key,
        EXPIRE_SECONDS,
        json.dumps(cookie_data.dict())
    )

    return {
        "pk": pk,
        "status": "saved",
        "cookie_count": len(cookie_data.cookie_list),
        "expires_in_hours": 8
    }


@app.get("/platform/get-cookies/{pk}")
async def get_cookies(pk: str):
    key = f"cookies:{pk}"
    data = redis_client.get(key)

    if not data:
        raise HTTPException(status_code=404, detail="Cookies not found or expired")

    # Get remaining TTL
    ttl = redis_client.ttl(key)

    return {
        "data": json.loads(data),
        "ttl_hours_remaining": round(ttl / 3600, 2) if ttl > 0 else 0
    }


@app.delete("/platform/delete-cookies/{pk}")
async def delete_cookies(pk: str):
    key = f"cookies:{pk}"
    deleted = redis_client.delete(key)

    if deleted:
        return {"status": "deleted", "pk": pk}
    else:
        raise HTTPException(status_code=404, detail="Cookies not found")


@app.get("/platform/by-browser/{browser_name}")
async def get_by_browser(browser_name: str):
    """Get all cookies for a specific browser"""
    keys = redis_client.keys("cookies:*")
    results = []

    for key in keys:
        data = redis_client.get(key)
        if data:
            cookie_data = json.loads(data)
            if cookie_data.get("browser_name") == browser_name:
                pk = key.decode().split(":")[-1]
                results.append({
                    "pk": pk,
                    **cookie_data
                })

    return {"results": results, "count": len(results)}


@app.on_event("startup")
async def startup():
    global redis_client
    redis_client = redis.from_url(
        REDIS_URL,
        decode_responses=True
    )
    # Test connection
    redis_client.ping()
    print("✅ Connected to Redis successfully")


@app.on_event("shutdown")
async def shutdown():
    redis_client.close()
