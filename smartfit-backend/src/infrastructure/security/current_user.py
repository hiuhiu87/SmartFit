from uuid import UUID

from fastapi import Header


async def get_current_user_id(x_user_id: str = Header(default="00000000-0000-0000-0000-000000000001")) -> UUID:
    # TODO: replace header stub with JWT authentication dependency.
    return UUID(x_user_id)
