import csv
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi_throttle import RateLimiter
import asyncio
import logging
import logging.config

from ip_whitelist import ip_whitelist
from log import LOGGING

from celery_config import celery_app
from task import process_live_request
from cache_processor import CrawlerRedisClient
from celery_producer import send_live_request_to_queue

logging.config.dictConfig(LOGGING)
logger = logging.getLogger("wrapper_api")

app = FastAPI()


class HotelRequest(BaseModel):
    request_id: str
    report_id: str
    client_id: str
    site_id: int
    site_name: str
    retry_count: int
    parameter: dict


HOTEL_MAP = {}
CRAWLER_DOMAIN_MAP = {
    "Hyatt": "Hyatt",
    "Marriott": "Marriott",
}



@app.on_event("startup")
async def load_hotel_map():
    global HOTEL_MAP
    HOTEL_MAP = {}
    with open("hotel_hyatt_mappings.csv", mode="r", encoding="utf-8") as hyatt_mapping:
        hyatt_reader = csv.DictReader(hyatt_mapping)
        for row in hyatt_reader:
            h_id = str(row['hotel_site_id']).lower()
            HOTEL_MAP[h_id] = row['combined']
    with open("hotels_marriott_mappings.csv", mode="r", encoding="utf-8") as marriott_mapping:
        marriott_reader = csv.DictReader(marriott_mapping)
        for row in marriott_reader:
            h_id = str(row['hotel_site_id']).lower()
            HOTEL_MAP[h_id] = row['combined']
    print("HOTEL Mapping Done....................######################################## ")


limiter = RateLimiter(times=60, seconds=60)
redis_client = CrawlerRedisClient(0)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTPException: {exc.detail} - Path: {request.url.path}")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail, "path": str(request.url.path)})


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)} - Path: {request.url.path}")
    return JSONResponse(
        status_code=500,
        content={"message": "An unexpected error occurred", "exception": str(exc), "path": str(request.url.path)},
    )


from starlette.middleware.base import BaseHTTPMiddleware


class ExceptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            logger.error(f"Middleware caught exception: {str(exc)}")
            return JSONResponse(status_code=500, content={"message": "Internal server error", "exception": str(exc)})


app.add_middleware(ExceptionMiddleware)


@app.post("/sendRequest/", dependencies=[Depends(ip_whitelist), Depends(limiter)])
async def hotel_wrapper(request_body: HotelRequest):
    try:
        original_hotel_id = str(request_body.parameter.get("hotel_id")).lower()
        site_name = str(request_body.site_name).lower()
        lookup_name = f"{site_name}-{original_hotel_id}"

        combined_hotel_id = HOTEL_MAP.get(lookup_name)
        logger.info("Hotel combined %s", combined_hotel_id)
        if not combined_hotel_id:
            raise HTTPException(status_code=404, detail="Hotel not found")

        # override hotel ID with mapped ID
        request_body.parameter["hotel_id"] = combined_hotel_id

        celery_payload = request_body.dict()
        domain_name = CRAWLER_DOMAIN_MAP.get(request_body.site_name)
        if not domain_name:
            raise HTTPException(status_code=400, detail=f"Domain not found for site {request_body.site_name}")

        crawler_name = request_body.site_name
        parameter = request_body.parameter

        # STEP 1: Build cache key
        cache_key = redis_client.build_key(crawler_name, parameter)

        # STEP 2: Check Redis BEFORE sending to MQ
        cache_resp = redis_client.get_crawler_response(cache_key)
        if cache_resp:
            logger.info(f"Cache HIT for {cache_key}. Returning cached response.")
            combined = {
                "request_params": request_body.dict(),
                "crawler_response": cache_resp,
                "message": "response form cache"
            }
            return JSONResponse(content=combined, status_code=cache_resp.get('status_code', 105))

        # STEP 3: Cache MISS → send MQ task
        logger.info(f"Cache MISS for {cache_key}. Sending task to MQ.")
        task_result = send_live_request_to_queue(celery_payload, domain_name)

        # STEP 4: Poll Redis for the response
        max_wait = 420
        interval = 2
        waited = 0

        while waited < max_wait:
            cache_resp = redis_client.get_crawler_response(cache_key)
            if cache_resp:
                combined = {
                    "request_params": request_body.dict(),
                    "crawler_response": cache_resp
                }
                logger.info(f"Poll succeeded with cache key {cache_key}")
                return JSONResponse(content=combined, status_code=cache_resp.get('status_code', 105))
            await asyncio.sleep(interval)
            waited += interval

        logger.error(f"Timed out waiting for response to cache key {cache_key}")
        raise HTTPException(status_code=504, detail="Timed out waiting for hotel response in cache")

    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

