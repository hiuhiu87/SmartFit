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
