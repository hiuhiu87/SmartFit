from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from src.domain.common.enums import AIRequestStatus, AIRequestType


@dataclass(slots=True)
class AIRequest:
    id: UUID
    user_id: UUID
    request_type: AIRequestType
    status: AIRequestStatus
    prompt: str
    response: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class AIChatMessage:
    id: UUID
    ai_request_id: UUID
    role: str
    content: str
    created_at: datetime | None = None


@dataclass(slots=True)
class AnalyticsEvent:
    id: UUID
    user_id: UUID
    event_name: str
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
