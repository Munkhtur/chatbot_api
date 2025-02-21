from fastapi import Depends, HTTPException, Header
secret_key = "your_jwt_secret_key"
algorithm = "HS256"
import jwt


def get_org_id(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    token = authorization.split(" ")[1]  # Extract token from "Bearer <token>"
    
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        org_id = payload.get("org_id")
        print(org_id)
        if not org_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return org_id
    except:
        raise HTTPException(status_code=401, detail="Invalid token -1")
