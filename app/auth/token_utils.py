# app/auth/token_utils.py
import jwt
from datetime import datetime, timedelta, timezone
from config.settings import JWT_SECRET_KEY

def generate_api_token(user_id: str) -> tuple[str, datetime]:
    """Generate a new API token for Agent Builder."""
    expiry = datetime.now(timezone.utc) + timedelta(days=90)  # 90 day token
    payload = {
        "user_id": user_id,
        "type": "api_token",
        "iat": datetime.now(timezone.utc),
        "exp": expiry
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")
    return token, expiry