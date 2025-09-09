from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import asyncio

app = FastAPI()

DJANGO_URL = "http://crm-core/api/sendRequest/hotel/"  

class HotelRequest(BaseModel):
    request_id: str
    report_id: str
    client_id: str
    site_id: int
    site_name: str
    retry_count: int
    parameter: dict

@app.post("/sendRequest/")
async def hotel_wrapper(request_body: HotelRequest):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(DJANGO_URL, json=request_body.dict())
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error connecting to Django: {e}")
        if resp.status_code == 200:
            # Got immediate result (cached)
            return resp.json()
        elif resp.status_code == 202:
            # Accepted, need to poll for result
            key = resp.json().get("key")
            if not key:
                raise HTTPException(status_code=500, detail="Key missing in Django response")
            poll_url = f"{DJANGO_URL}?key={key}"
            max_wait = 120  # seconds, to match Django timeout if needed
            interval = 2    # polling interval in seconds
            waited = 0

            while waited < max_wait:
                poll_resp = await client.get(poll_url)
                if poll_resp.status_code != 404:  # Response is ready
                    return poll_resp.json()
                await asyncio.sleep(interval)
                waited += interval

            # If timeout, return last response
            raise HTTPException(
                status_code=202,
                detail="Timed out waiting for hotel response in cache"
            )
        else:
            # Error from Django POST
            raise HTTPException(status_code=resp.status_code, detail=resp.json())

