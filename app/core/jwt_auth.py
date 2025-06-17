import os
from fastapi import HTTPException, Cookie
import jwt
from dotenv import load_dotenv


load_dotenv()
SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = "HS512"

def get_current_user_id(accessToken: str = Cookie(...)) -> int:
    try:
        payload = jwt.decode(accessToken, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"] 
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")