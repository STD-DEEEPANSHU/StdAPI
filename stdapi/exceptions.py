"""
StdAPI Custom Exception Hierarchy
Provides explicit, catchable errors for bots and production systems.
"""

class StdAPIError(Exception):
    """Base exception for all StdAPI errors."""
    def __init__(self, message: str, status_code: int = 500, details: dict = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}

    def __str__(self):
        return f"[{self.status_code}] {self.message}" if self.status_code else self.message


class ConnectionError(StdAPIError):
    """Raised when server connection fails, DNS fails, or server is unreachable."""
    def __init__(self, message: str = "Could not connect to StdAPI gateway.", details: dict = None):
        super().__init__(message, status_code=503, details=details)


class RateLimitError(StdAPIError):
    """Raised when rate limit is exceeded (HTTP 429)."""
    def __init__(self, message: str = "Rate limit reached on StdAPI server.", retry_after: int = 60, details: dict = None):
        super().__init__(message, status_code=429, details=details)
        self.retry_after = retry_after


class AuthenticationError(StdAPIError):
    """Raised when API key or authorization token is invalid or missing."""
    def __init__(self, message: str = "Invalid or missing StdAPI key.", details: dict = None):
        super().__init__(message, status_code=401, details=details)


class MediaExtractionError(StdAPIError):
    """Raised when media extraction or stream parsing fails."""
    def __init__(self, message: str = "Unable to extract media from the given URL.", details: dict = None):
        super().__init__(message, status_code=422, details=details)


class ContentBlockedError(StdAPIError):
    """Raised when media or content is age-restricted, geoblocked, or removed."""
    def __init__(self, message: str = "Content is age-restricted or copyright blocked.", details: dict = None):
        super().__init__(message, status_code=403, details=details)


class ValidationError(StdAPIError):
    """Raised when invalid parameters or arguments are supplied."""
    def __init__(self, message: str = "Invalid input parameter.", details: dict = None):
        super().__init__(message, status_code=400, details=details)


class NotFoundError(StdAPIError):
    """Raised when the requested resource or endpoint is not found."""
    def __init__(self, message: str = "Resource not found.", details: dict = None):
        super().__init__(message, status_code=404, details=details)
