"""MCP tool registration and shared helpers (write-guard, client accessor)."""

from __future__ import annotations

import functools
import logging
from typing import Any, Awaitable, Callable

from fortios_mcp.api.client import FortiOSClient
from fortios_mcp.utils.config import get_settings

logger = logging.getLogger(__name__)

_client: FortiOSClient | None = None


def set_client(client: FortiOSClient | None) -> None:
    """Register the shared FortiOSClient used by every tool."""
    global _client
    _client = client


def get_client() -> FortiOSClient:
    """Return the registered client or raise if the server is not ready."""
    if _client is None:
        raise RuntimeError(
            "FortiOSClient is not initialised. The MCP server lifespan must run first."
        )
    return _client


def writes_enabled() -> bool:
    """Report whether ``FORTIOS_ENABLE_WRITES`` permits mutating operations."""
    return get_settings().FORTIOS_ENABLE_WRITES


def require_writes(
    fn: Callable[..., Awaitable[dict[str, Any]]],
) -> Callable[..., Awaitable[dict[str, Any]]]:
    """Block a coroutine tool unless writes are explicitly enabled."""

    @functools.wraps(fn)
    async def wrapped(*args: Any, **kwargs: Any) -> dict[str, Any]:
        if not writes_enabled():
            return {
                "status": "error",
                "message": (
                    "Write operations are disabled. Set FORTIOS_ENABLE_WRITES=true "
                    "to allow this tool to modify the FortiGate."
                ),
                "tool": fn.__name__,
            }
        return await fn(*args, **kwargs)

    wrapped.__fortios_requires_writes__ = True  # type: ignore[attr-defined]
    return wrapped


def ok(data: Any) -> dict[str, Any]:
    """Standard success envelope for MCP tool responses."""
    return {"status": "success", "data": data}


def err(exc: BaseException | str, *, tool: str | None = None) -> dict[str, Any]:
    """Standard error envelope for MCP tool responses."""
    message = str(exc)
    out: dict[str, Any] = {"status": "error", "message": message}
    if tool:
        out["tool"] = tool
    status_code = getattr(exc, "status_code", None)
    if status_code is not None:
        out["status_code"] = status_code
    return out


def register_all(mcp: Any) -> None:
    """Import each tool module so its ``@mcp.tool`` decorators fire.

    The modules themselves reference the shared ``mcp`` instance via
    :func:`~fortios_mcp.server.get_mcp`, which is set during
    :func:`fortios_mcp.server.build_server`.
    """
    from fortios_mcp.tools import (  # noqa: F401
        diagnostic_tools,
        firewall_tools,
        generic_tools,
        log_tools,
        monitor_tools,
        routing_tools,
        schema_tools,
        security_profile_tools,
        system_tools,
        user_tools,
        vpn_tools,
    )

    logger.info("Registered FortiOS MCP tool modules")
