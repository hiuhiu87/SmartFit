from src.infrastructure.security.jwt_provider import JWTProvider
from src.infrastructure.security.password_hasher import PasswordHasher


def test_password_hasher_hash_and_verify() -> None:
    hasher = PasswordHasher()
    raw_password = "super-secret-password"

    hashed_password = hasher.hash(raw_password)

    assert hashed_password != raw_password
    assert hasher.verify(raw_password, hashed_password) is True
    assert hasher.verify("wrong-password", hashed_password) is False


def test_jwt_provider_creates_and_decodes_access_and_refresh_tokens() -> None:
    provider = JWTProvider()
    subject = "00000000-0000-0000-0000-000000000123"

    access_token = provider.create_access_token(subject)
    refresh_token = provider.create_refresh_token(subject)

    access_payload = provider.decode_token(access_token, expected_type="access")
    refresh_payload = provider.decode_token(refresh_token, expected_type="refresh")

    assert access_payload["sub"] == subject
    assert access_payload["type"] == "access"
    assert refresh_payload["sub"] == subject
    assert refresh_payload["type"] == "refresh"
