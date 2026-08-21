"""Core domain exceptions across bounded contexts."""


class DomainError(Exception):
    """Base domain exception."""

    def __init__(self, message: str, code: str = "DOMAIN_ERROR"):
        super().__init__(message)
        self.message = message
        self.code = code


class EntityNotFoundError(DomainError):
    """Raised when an aggregate or entity cannot be found."""

    def __init__(self, entity_name: str, identifier: str | int):
        super().__init__(
            f"{entity_name} with identifier '{identifier}' was not found", code="NOT_FOUND"
        )


class DuplicateEntityError(DomainError):
    """Raised on uniqueness constraint violations."""

    def __init__(self, entity_name: str, value: str):
        super().__init__(f"{entity_name} '{value}' already exists", code="DUPLICATE_ENTITY")


class RateLimitExceededError(DomainError):
    """Raised when upstream rate limits are violated."""

    def __init__(self, service: str, retry_after: int = 60):
        super().__init__(
            f"Rate limit exceeded on {service}. Retry after {retry_after}s", code="RATE_LIMIT"
        )
        self.retry_after = retry_after


class AccountPoolExhaustedError(DomainError):
    """Raised when all worker accounts in pool are in cooling/flood-wait."""

    def __init__(self, message: str = "No available Telegram account in the pool"):
        super().__init__(message, code="POOL_EXHAUSTED")
