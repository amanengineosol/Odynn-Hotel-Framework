from fastapi import Request, HTTPException

WHITELISTED_IPS = ["127.0.0.1:9000", "10.5.50.117", "172.18.0.1"]  

def ip_whitelist(request: Request):
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.client.host

    agent = request.headers.get("APP-ID", "unknown")

    if ip not in WHITELISTED_IPS and agent != 'HOTEL-PLATFORM':
        raise HTTPException(status_code=403, detail="Request not allowed!! IP and User-Agent not allowed.")
