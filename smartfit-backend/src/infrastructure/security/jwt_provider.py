from datetime import datetime, timedelta, timezone

from jose import jwt

from app.settings import get_settings


class JWTProvider:
    def __init__(self) -> None:
        self.settings = get_settings()

    def create_access_token(self, subject: str) -> str:
        payload = {
            "sub": subject,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        }
        return jwt.encode(payload, self.settings.JWT_SECRET_KEY, algorithm=self.settings.JWT_ALGORITHM)
