from pydantic import BaseModel, EmailStr, Field


class RegisterRequestSchema(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequestSchema(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class TokenResponseSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
