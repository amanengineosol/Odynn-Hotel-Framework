from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi_throttle import RateLimiter
from fastapi.responses import JSONResponse
from fastapi import Depends
from ip_whitelist import ip_whitelist
import httpx
import asyncio
import logging
import logging.config
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
    
limiter = RateLimiter(times=10, seconds=60)
@app.post("/sendRequest/",dependencies=[Depends(ip_whitelist),Depends(limiter)])
async def hotel_wrapper(request_body: HotelRequest):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(DJANGO_URL, json=request_body.dict())
            logger.info(f"Fetched response from hotel POST method. Status: {resp.status_code}")
        except Exception as e:
            logger.error(f"Error connecting to POST method: {e}")
            raise HTTPException(status_code=500, detail=f"Error connecting to Django: {e}")
        if resp.status_code == 200:
            logger.info(f"POST method response is 200")
            return JSONResponse(content=resp.json(), status_code=resp.status_code)
        elif resp.status_code == 202:
            key = resp.json().get("key")
            if not key:
                logger.error("Key missing in POST method response")
                raise HTTPException(status_code=500, detail="Key missing in Django response")
            poll_url = f"{DJANGO_URL}?key={key}"
            max_wait = 120  
            interval = 2    
            waited = 0
            logger.info(f"Polling {poll_url} for up to {max_wait}s")
            while waited < max_wait:
                poll_resp = await client.get(poll_url)
                logger.info(f"Poll attempt after {waited}s - Status: {poll_resp.status_code}")
                if poll_resp.status_code != 404: 
                    crawler_response_data = poll_resp.json().get("response",{})
                    combined = {
                        "request_params": request_body.dict(),
                        "crawler_response": crawler_response_data
                    }
                    logger.info(f"Poll response returned with status {poll_resp.status_code}")
                    return JSONResponse(content=combined, status_code=poll_resp.status_code)
                await asyncio.sleep(interval)
                waited += interval
            logger.error(f"Timed out waiting for hotel response in cache for key {key}")
            raise HTTPException(
                status_code=202,
                detail="Timed out waiting for hotel response in cache"
            )
        else:
            logger.error(f"Unknown response from hotel POST request: Status {resp.status_code}")
            raise HTTPException(status_code=resp.status_code, detail=resp.json())

