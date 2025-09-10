from fastapi import Request, HTTPException

WHITELISTED_IPS = ["127.0.0.1:9000", "10.5.50.117", "172.18.0.1"]  

def ip_whitelist(request: Request):
    ip = request.headers.get("X-Forwarded-For", request.client.host)
    print("8888888888888888888888888888888888888888888888888888888888888")
    print(ip)
    if ip not in WHITELISTED_IPS:
        raise HTTPException(status_code=403, detail="Request not allowed!! IP not whitelisted.")