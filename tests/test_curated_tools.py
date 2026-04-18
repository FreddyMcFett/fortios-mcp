"""Smoke tests for a representative sample of curated tools."""

from __future__ import annotations

from fortios_mcp.tools import firewall_tools, routing_tools, schema_tools, system_tools


async def test_get_system_status(tool_client) -> None:  # type: ignore[no-untyped-def]
    out = await system_tools.get_system_status()
    assert out["status"] == "success"
    data = out["data"]
    assert isinstance(data, dict)


async def test_list_firewall_policies(tool_client) -> None:  # type: ignore[no-untyped-def]
    out = await firewall_tools.list_firewall_policies()
    assert out["status"] == "success"


async def test_list_static_routes(tool_client) -> None:  # type: ignore[no-untyped-def]
    out = await routing_tools.list_static_routes()
    assert out["status"] == "success"


async def test_schema_list_api_categories() -> None:
    out = await schema_tools.list_api_categories()
    assert out["status"] == "success"
    assert "Configuration" in out["data"]


async def test_schema_search_endpoints() -> None:
    out = await schema_tools.search_endpoints(query="policy", limit=5)
    assert out["status"] == "success"
    assert out["data"]["count"] > 0


async def test_schema_describe_endpoint() -> None:
    # pick a known-existing endpoint from the Monitor/system file
    listing = await schema_tools.list_endpoints(
        api_type="Monitor", category="system"
    )
    assert listing["status"] == "success"
    eps = listing["data"]["endpoints"]
    assert eps
    target = eps[0]
    out = await schema_tools.describe_endpoint(
        api_type="Monitor",
        category="system",
        path=target["path"],
        method=target["method"],
    )
    assert out["status"] == "success"
    assert out["data"]["path"] == target["path"]
