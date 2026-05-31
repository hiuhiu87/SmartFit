from datetime import datetime, timedelta, timezone
from uuid import UUID

from jose import JWTError, jwt

from app.settings import get_settings
from src.domain.common.exceptions import UnauthorizedError


class JWTProvider:
    def __init__(self) -> None:
        self.settings = get_settings()

    def create_access_token(self, subject: str) -> str:
        payload = {
            "sub": subject,
            "type": "access",
            "exp": datetime.now(timezone.utc)
            + timedelta(minutes=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        }
        return jwt.encode(
            payload, self.settings.JWT_SECRET_KEY, algorithm=self.settings.JWT_ALGORITHM
        )

    def create_refresh_token(self, subject: str) -> str:
        payload = {
            "sub": subject,
            "type": "refresh",
            "exp": datetime.now(timezone.utc)
            + timedelta(days=self.settings.REFRESH_TOKEN_EXPIRE_DAYS),
        }
        return jwt.encode(
            payload, self.settings.JWT_SECRET_KEY, algorithm=self.settings.JWT_ALGORITHM
        )

    def decode_token(self, token: str, *, expected_type: str | None = None) -> dict:
        try:
            payload = jwt.decode(
                token,
                self.settings.JWT_SECRET_KEY,
                algorithms=[self.settings.JWT_ALGORITHM],
            )
        except JWTError as exc:
            raise UnauthorizedError("Invalid or expired token") from exc

        token_type = payload.get("type")
        subject = payload.get("sub")

        if expected_type is not None and token_type != expected_type:
            raise UnauthorizedError("Token type is not allowed for this operation")
        if not subject:
            raise UnauthorizedError("Token subject is missing")

        return payload

    def get_subject(self, token: str, *, expected_type: str = "access") -> UUID:
        payload = self.decode_token(token, expected_type=expected_type)
        try:
            return UUID(payload["sub"])
        except ValueError as exc:
            raise UnauthorizedError("Token subject is invalid") from exc
