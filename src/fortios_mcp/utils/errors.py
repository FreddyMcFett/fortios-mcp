"""Exception hierarchy and HTTP-code parser for FortiOS responses."""

from __future__ import annotations

from typing import Any


class FortiOSError(Exception):
    """Base class for all FortiOS MCP errors."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        operation: str | None = None,
        payload: Any = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.operation = operation
        self.payload = payload


class AuthenticationError(FortiOSError):
    """401/403 responses — bad or revoked API token."""


class NotFoundError(FortiOSError):
    """404 — target resource does not exist on the FortiGate."""


class MethodNotAllowedError(FortiOSError):
    """405 — HTTP method not supported for this resource."""


class FailedDependencyError(FortiOSError):
    """424 — FortiOS-specific validation failure (missing attribute, etc.)."""


class RateLimitError(FortiOSError):
    """429 — rate-limited by the FortiGate; retry after backoff."""


class ServerError(FortiOSError):
    """5xx — FortiOS returned an internal error."""


class ConnectionFailed(FortiOSError):
    """Network-level failure contacting the FortiGate."""


def parse_http_error(status: int, message: str, operation: str, payload: Any = None) -> FortiOSError:
    """Map an HTTP status to the most specific FortiOSError subclass."""
    kwargs = {"status_code": status, "operation": operation, "payload": payload}
    if status in (401, 403):
        return AuthenticationError(f"Authentication failed: {message}", **kwargs)
    if status == 404:
        return NotFoundError(f"Resource not found: {message}", **kwargs)
    if status == 405:
        return MethodNotAllowedError(f"Method not allowed: {message}", **kwargs)
    if status == 424:
        return FailedDependencyError(f"Validation error: {message}", **kwargs)
    if status == 429:
        return RateLimitError(f"Rate limit exceeded: {message}", **kwargs)
    if 500 <= status < 600:
        return ServerError(f"FortiGate server error: {message}", **kwargs)
    return FortiOSError(f"FortiOS error (HTTP {status}): {message}", **kwargs)
