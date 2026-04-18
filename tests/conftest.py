"""Shared pytest fixtures for the FortiOS MCP test suite.

Every tool is exercised against an ``httpx.MockTransport`` so the suite
runs hermetically — no FortiGate required. Integration tests that do need
a device live under ``tests/integration/`` and are skipped by default.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator, Callable
from typing import Any

import httpx
import pytest

os.environ.setdefault("FORTIOS_HOST", "fake-fortigate.local")
os.environ.setdefault("FORTIOS_API_TOKEN", "test-token")
os.environ.setdefault("FORTIOS_VERIFY_SSL", "false")

from fortios_mcp.api.client import FortiOSClient  # noqa: E402
from fortios_mcp.server import build_server  # noqa: E402
from fortios_mcp.tools import set_client  # noqa: E402
from fortios_mcp.utils.config import reset_settings_cache  # noqa: E402


# ---------------------------------------------------------------------------
# Mock transport helpers
# ---------------------------------------------------------------------------

Handler = Callable[[httpx.Request], httpx.Response]


def _json_ok(results: Any, *, status: int = 200, vdom: str = "root") -> httpx.Response:
    """Build a valid FortiOS response envelope."""
    return httpx.Response(
        status,
        json={
            "http_status": status,
            "revision": "abc123",
            "results": results,
            "vdom": vdom,
        },
    )


@pytest.fixture
def fortios_response_factory() -> Callable[..., httpx.Response]:
    """Return a helper for building FortiOS responses in tests."""
    return _json_ok


@pytest.fixture
def mock_transport_factory() -> Callable[[Handler], httpx.MockTransport]:
    """Build an ``httpx.MockTransport`` from a handler callable."""

    def _build(handler: Handler) -> httpx.MockTransport:
        return httpx.MockTransport(handler)

    return _build


# ---------------------------------------------------------------------------
# Client / server fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def default_handler() -> Handler:
    """Handler that returns a generic success for any request."""

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/system/status"):
            return _json_ok({"version": "v7.6.6", "hostname": "fgt-test"})
        return _json_ok([])

    return handler


@pytest.fixture
async def client(default_handler: Handler) -> AsyncIterator[FortiOSClient]:
    """A FortiOSClient wired to a mock transport."""
    transport = httpx.MockTransport(default_handler)
    cli = FortiOSClient(
        host="fake-fortigate.local",
        api_token="test-token",
        verify_ssl=False,
        timeout=5,
        max_retries=0,
        transport=transport,
    )
    try:
        yield cli
    finally:
        await cli.close()


@pytest.fixture(scope="session", autouse=True)
def _bootstrap_server() -> None:
    """Ensure build_server() runs once so tool modules can import."""
    reset_settings_cache()
    build_server()


@pytest.fixture
async def tool_client(default_handler: Handler) -> AsyncIterator[FortiOSClient]:
    """Register a mock-backed client so `@mcp.tool` functions can be called directly."""
    transport = httpx.MockTransport(default_handler)
    cli = FortiOSClient(
        host="fake-fortigate.local",
        api_token="test-token",
        verify_ssl=False,
        timeout=5,
        max_retries=0,
        transport=transport,
    )
    set_client(cli)
    try:
        yield cli
    finally:
        set_client(None)
        await cli.close()


@pytest.fixture
def set_writes_enabled(monkeypatch: pytest.MonkeyPatch) -> Callable[[bool], None]:
    """Toggle FORTIOS_ENABLE_WRITES at runtime."""

    def _set(value: bool) -> None:
        monkeypatch.setenv("FORTIOS_ENABLE_WRITES", "true" if value else "false")
        reset_settings_cache()

    return _set
