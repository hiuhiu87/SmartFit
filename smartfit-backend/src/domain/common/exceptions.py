class DomainError(Exception):
    """Base exception for domain errors."""


class ValidationError(DomainError):
    """Raised when a domain invariant is violated."""


class NotFoundError(DomainError):
    """Raised when an entity cannot be located."""


class UnauthorizedError(DomainError):
    """Raised when an operation is not permitted."""


class InvalidWorkoutStateError(ValidationError):
    """Raised when a workout lifecycle transition is invalid."""


class AIGenerationError(DomainError):
    """Raised when AI generation fails."""


class AIPaymentRequiredError(AIGenerationError):
    """Raised when AI provider returns 402 Payment Required."""



class AIRateLimitError(AIGenerationError):
    """Raised when AI provider rate limit is hit."""


class AIProviderTimeoutError(AIGenerationError):
    """Raised when AI provider times out."""


class AIInvalidOutputError(AIGenerationError):
    """Raised when AI output cannot be parsed or validated."""


class AIUnsafeOutputError(AIGenerationError):
    """Raised when AI output violates safety constraints."""


class AIExerciseMappingError(AIGenerationError):
    """Raised when AI references unknown or unsupported exercises."""


class AIConfigurationError(AIGenerationError):
    """Raised when AI provider configuration is missing or invalid."""


class AIChatGenerationError(AIGenerationError):
    """Raised when AI chat generation fails."""


class AIChatInvalidOutputError(AIChatGenerationError):
    """Raised when AI chat output cannot be parsed or validated."""


class AIChatUnsafeOutputError(AIChatGenerationError):
    """Raised when AI chat output violates safety constraints."""


class AIUsageLimitExceededError(DomainError):
    """Raised when daily internal AI usage limit is exceeded."""
