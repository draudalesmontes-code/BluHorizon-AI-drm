from datetime import datetime, timedelta
from jose import JWTError, jwt
from config import settings


def create_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def verify_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token,settings.secret_key,algorithms=[settings.algorithm])
        user_id = payload.get("sub")
        return int(user_id) if user_id else None
    except JWTError:
        return None
