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
