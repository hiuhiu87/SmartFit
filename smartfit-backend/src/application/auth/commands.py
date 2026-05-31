from dataclasses import dataclass


@dataclass(slots=True)
class RegisterUserCommand:
    email: str
    password: str


@dataclass(slots=True)
class LoginCommand:
    email: str
    password: str
