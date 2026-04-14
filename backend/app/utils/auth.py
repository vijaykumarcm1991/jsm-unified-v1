from jose import jwt, JWTError
from datetime import datetime, timedelta
import pytz

IST = pytz.timezone("Asia/Kolkata")

SECRET_KEY = "ee2801cac2939dd0ebc18ace4d3755ae61695dbb61f0f84ee1ea5027629c7495"
ALGORITHM = "HS256"

def create_token(role: str):
    payload = {
        "role": role,
        "exp": datetime.now(IST) + timedelta(hours=8)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None