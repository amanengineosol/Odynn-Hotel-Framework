# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
# from fastapi_throttle import RateLimiter
# from fastapi.responses import JSONResponse
# from fastapi import Depends
# from ip_whitelist import ip_whitelist
# import httpx
# import asyncio
# import logging
# import logging.config
# from log import LOGGING
#
# logging.config.dictConfig(LOGGING)
# logger = logging.getLogger("wrapper_api")
#
#
# app = FastAPI()
#
# DJANGO_URL = "http://crm-core:8000/api/sendRequest/hotel/"
#
# class HotelRequest(BaseModel):
#     request_id: str
#     report_id: str
#     client_id: str
#     site_id: int
#     site_name: str
#     retry_count: int
#     parameter: dict
#
# limiter = RateLimiter(times=60, seconds=60)
# @app.post("/sendRequest/",dependencies=[Depends(ip_whitelist),Depends(limiter)])
# async def hotel_wrapper(request_body: HotelRequest):
#     async with httpx.AsyncClient() as client:
#         try:
#             resp = await client.post(DJANGO_URL, json=request_body.dict())
#             logger.info(f"Fetched response from hotel POST method. Status: {resp.status_code}")
#         except Exception as e:
#             logger.error(f"Error connecting to POST method: {e}")
#             raise HTTPException(status_code=500, detail=f"Error connecting to Django: {e}")
#         if resp.status_code == 200:
#             logger.info(f"POST method response is 200")
#             return JSONResponse(content=resp.json(), status_code=resp.status_code)
#         elif resp.status_code == 202:
#             key = resp.json().get("key")
#             if not key:
#                 logger.error("Key missing in POST method response")
#                 raise HTTPException(status_code=500, detail="Key missing in Django response")
#             poll_url = f"{DJANGO_URL}?key={key}"
#             max_wait = 300
#             interval = 2
#             waited = 0
#             while waited < max_wait:
#                 poll_resp = await client.get(poll_url)
#                 if poll_resp.status_code != 404:
#                     crawler_response_data = poll_resp.json().get("response",{})
#                     combined = {
#                         "request_params": request_body.dict(),
#                         "crawler_response": crawler_response_data
#                     }
#                     logger.info(f"Poll response returned with status {poll_resp.status_code}")
#                     return JSONResponse(content=combined, status_code=poll_resp.status_code)
#                 await asyncio.sleep(interval)
#                 waited += interval
#             logger.error(f"Timed out waiting for hotel response in cache for key {key}")
#             raise HTTPException(
#                 status_code=504,
#                 detail="Timed out waiting for hotel response in cache"
#             )
#         else:
#             logger.error(f"Unknown response from hotel POST request: Status {resp.status_code}")
#             raise HTTPException(status_code=resp.status_code, detail=resp.json())
#
import csv
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi_throttle import RateLimiter
import httpx
import asyncio
import logging
import logging.config
from ip_whitelist import ip_whitelist
from log import LOGGING

logging.config.dictConfig(LOGGING)
logger = logging.getLogger("wrapper_api")

app = FastAPI()

DJANGO_URL = "http://crm-core:8000/api/sendRequest/hotel/"

class HotelRequest(BaseModel):
    request_id: str
    report_id: str
    client_id: str
    site_id: int
    site_name: str
    retry_count: int
    parameter: dict

async def get_client():
    async with httpx.AsyncClient() as client:
        yield client

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

HOTEL_MAP = {}

@app.on_event("startup")
async def load_hotel_map():
    global HOTEL_MAP
    HOTEL_MAP = {}
    # Load Hyatt mapping
    with open("hotel_hyatt_mappings.csv", mode="r", encoding="utf-8") as hyatt_mapping:
        hyatt_reader = csv.DictReader(hyatt_mapping)
        for row in hyatt_reader:
            h_id = str(row['hotel_id']).lower()
            HOTEL_MAP[h_id] = row['combined']
    # Load Marriott mapping and update dictionary
    with open("hotels_marriott_mappings.csv", mode="r", encoding="utf-8") as marriott_mapping:
        marriott_reader = csv.DictReader(marriott_mapping)
        for row in marriott_reader:
            h_id = str(row['hotel_id']).lower()
            HOTEL_MAP[h_id] = row['combined']
    print("HOTEL Mapping Done....................######################################## ")


limiter = RateLimiter(times=60, seconds=60)
@app.post("/sendRequest/", dependencies=[Depends(ip_whitelist), Depends(limiter)])
async def hotel_wrapper(request_body: HotelRequest, client: httpx.AsyncClient = Depends(get_client)):
    try:
        original_hotel_id = str(request_body.parameter.get("hotel_id")).lower()
        combined_hotel_id = HOTEL_MAP.get(original_hotel_id)

        print("Hotel combined",combined_hotel_id)
        if combined_hotel_id:
            request_body.parameter["hotel_id"] = combined_hotel_id
        else:
            raise HTTPException(status_code=404, detail="Hotel not found")
        resp = await client.post(DJANGO_URL, json=request_body.dict())
        logger.info(f"Received POST response status: {resp.status_code}")

        if resp.status_code == 200:
            return JSONResponse(content=resp.json(), status_code=200)

        elif resp.status_code == 202:
            key = resp.json().get("key")
            if not key:
                logger.error("Key missing in 202 response")
                raise HTTPException(status_code=500, detail="Key missing in Django response")

            poll_url = f"{DJANGO_URL}?key={key}"
            max_wait = 300  # max 5 minutes
            interval = 2    # poll every 2 seconds
            waited = 0

            while waited < max_wait:
                poll_resp = await client.get(poll_url)
                if poll_resp.status_code != 404:
                    crawler_response_data = poll_resp.json().get("response", {})
                    combined = {
                        "request_params": request_body.dict(),
                        "crawler_response": crawler_response_data
                    }
                    logger.info(f"Poll succeeded with status {poll_resp.status_code}")
                    return JSONResponse(content=combined, status_code=poll_resp.status_code)
                await asyncio.sleep(interval)
                waited += interval

            logger.error(f"Timed out waiting for response to cache key {key}")
            raise HTTPException(status_code=504, detail="Timed out waiting for hotel response in cache")

        else:
            logger.error(f"Unknown status from POST request: {resp.status_code}")
            raise HTTPException(status_code=resp.status_code, detail=resp.json())

    except httpx.RequestError as e:
        logger.error(f"HTTP request error: {e}")
        raise HTTPException(status_code=500, detail=f"Error connecting to Django: {e}")

    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

