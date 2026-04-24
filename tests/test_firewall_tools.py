"""Tests for curated firewall tools."""

from __future__ import annotations

import httpx

from fortios_mcp.api.client import FortiOSClient
from fortios_mcp.tools import firewall_tools, set_client
from fortios_mcp.utils.config import reset_settings_cache


async def test_move_firewall_policy_uses_query_params(
    monkeypatch,  # type: ignore[no-untyped-def]
) -> None:
    """Regression test: the move operation must go out as query params, not JSON body.

    FortiOS expects ``PUT /api/v2/cmdb/firewall/policy/<id>?action=move&before=<target>``
    (or ``&after=<target>``) with no body. The previous implementation sent
    ``{"action": "before", "target": ...}`` as a JSON body, which FortiOS ignores.
    """
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["path"] = request.url.path
        captured["params"] = dict(request.url.params)
        captured["content"] = request.content.decode() if request.content else ""
        return httpx.Response(200, json={"http_status": 200, "results": [], "vdom": "root"})

    client = FortiOSClient(
        host="fgt.example",
        api_token="secret",
        verify_ssl=False,
        timeout=5,
        max_retries=0,
        transport=httpx.MockTransport(handler),
    )
    set_client(client)
    monkeypatch.setenv("FORTIOS_ENABLE_WRITES", "true")
    reset_settings_cache()

    try:
        result = await firewall_tools.move_firewall_policy(policyid=1, action="before", target=5)
    finally:
        set_client(None)
        await client.close()
        monkeypatch.delenv("FORTIOS_ENABLE_WRITES", raising=False)
        reset_settings_cache()

    assert result["status"] == "success"
    assert captured["method"] == "PUT"
    assert captured["path"] == "/api/v2/cmdb/firewall/policy/1"
    assert captured["params"]["action"] == "move"
    assert captured["params"]["before"] == "5"
    assert "after" not in captured["params"]
    # No JSON body is sent — FortiOS reads the move target from query params.
    assert captured["content"] == ""


async def test_move_firewall_policy_rejects_invalid_action(
    tool_client,  # type: ignore[no-untyped-def]
    monkeypatch,  # type: ignore[no-untyped-def]
) -> None:
    monkeypatch.setenv("FORTIOS_ENABLE_WRITES", "true")
    reset_settings_cache()
    try:
        out = await firewall_tools.move_firewall_policy(policyid=1, action="above", target=5)
    finally:
        monkeypatch.delenv("FORTIOS_ENABLE_WRITES", raising=False)
        reset_settings_cache()
    assert out["status"] == "error"
    assert "before" in out["message"] or "after" in out["message"]


async def test_list_firewall_policies_happy_path(tool_client) -> None:  # type: ignore[no-untyped-def]
    out = await firewall_tools.list_firewall_policies()
    assert out["status"] == "success"
