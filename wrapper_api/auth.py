import os
from fastapi import HTTPException, status, Security
from fastapi.security.api_key import APIKeyHeader
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_KEY_NAME = "X-API-Key"  # Standard API key header

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def api_key_authentication(api_key_header: str = Security(api_key_header)):
    if api_key_header == API_KEY:
        return api_key_header
    raise HTTPException(
        status_code=401,
        detail="Invalid or missing API Key",
    )
