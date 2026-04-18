"""Unit tests for the FortiOSClient HTTP layer."""

from __future__ import annotations

import httpx
import pytest

from fortios_mcp.api.client import FortiOSClient
from fortios_mcp.utils.errors import (
    AuthenticationError,
    FortiOSError,
    NotFoundError,
    RateLimitError,
)


def _make_client(handler: object, *, max_retries: int = 0, **overrides: object) -> FortiOSClient:
    return FortiOSClient(
        host="fgt.example",
        api_token="secret",
        verify_ssl=False,
        timeout=5,
        max_retries=max_retries,
        transport=httpx.MockTransport(handler),  # type: ignore[arg-type]
        **overrides,  # type: ignore[arg-type]
    )


async def test_cmdb_get_returns_payload() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/v2/cmdb/firewall/policy"
        assert request.url.params["vdom"] == "root"
        return httpx.Response(
            200,
            json={"http_status": 200, "results": [{"policyid": 1}], "vdom": "root"},
        )

    client = _make_client(handler)
    result = await client.cmdb_get("firewall/policy")
    assert result["results"] == [{"policyid": 1}]
    await client.close()


async def test_bearer_token_header() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["auth"] = request.headers.get("Authorization", "")
        return httpx.Response(200, json={"http_status": 200, "results": []})

    client = _make_client(handler)
    await client.cmdb_get("system/global")
    assert captured["auth"] == "Bearer secret"
    await client.close()


async def test_401_raises_authentication_error() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "invalid token"})

    client = _make_client(handler)
    with pytest.raises(AuthenticationError):
        await client.cmdb_get("firewall/policy")
    await client.close()


async def test_404_raises_not_found() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"error": "no such object"})

    client = _make_client(handler)
    with pytest.raises(NotFoundError):
        await client.cmdb_get("firewall/policy/9999")
    await client.close()


async def test_429_retries_then_fails_as_rate_limit() -> None:
    calls = {"n": 0}

    def handler(_: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(429, json={"error": "too many"})

    client = _make_client(handler, max_retries=2)
    with pytest.raises(RateLimitError):
        await client.cmdb_get("firewall/policy")
    assert calls["n"] == 3
    await client.close()


async def test_embedded_http_status_in_body_raises() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"http_status": 424, "cli_error": "missing attribute", "results": []},
        )

    client = _make_client(handler)
    with pytest.raises(FortiOSError) as exc:
        await client.cmdb_get("firewall/policy")
    assert exc.value.status_code == 424
    await client.close()


async def test_monitor_get_cmdb_and_log_paths() -> None:
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.url.path)
        return httpx.Response(200, json={"http_status": 200, "results": []})

    client = _make_client(handler)
    await client.monitor_get("system/status")
    await client.log_get("disk/traffic")
    await client.service_execute("system/reboot", {"reason": "test"})
    assert "/api/v2/monitor/system/status" in seen
    assert "/api/v2/log/disk/traffic" in seen
    assert "/api/v2/service/system/reboot" in seen
    await client.close()


async def test_version_parsed_from_probe() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "http_status": 200,
                "results": {"version": "v7.6.6-build7777 240101 (GA.M)"},
            },
        )

    client = _make_client(handler)
    await client.probe()
    assert client.version == (7, 6, 6)
    await client.close()
