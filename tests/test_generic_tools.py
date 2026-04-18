"""Smoke tests for generic CRUD tool primitives."""

from __future__ import annotations

import pytest

from fortios_mcp.tools import generic_tools


async def test_cmdb_get_validates_path(tool_client) -> None:  # type: ignore[no-untyped-def]
    bad = await generic_tools.cmdb_get(path="/leading/slash")
    assert bad["status"] == "error"
    assert "relative" in bad["message"]


async def test_cmdb_get_rejects_traversal(tool_client) -> None:  # type: ignore[no-untyped-def]
    bad = await generic_tools.cmdb_get(path="firewall/../secret")
    assert bad["status"] == "error"


async def test_cmdb_get_forwards_filter_params(tool_client) -> None:  # type: ignore[no-untyped-def]
    result = await generic_tools.cmdb_get(path="firewall/policy", filter="name==HTTPS", count=10)
    assert result["status"] == "success"


@pytest.mark.parametrize(
    "source",
    ["disk", "memory", "fortianalyzer", "forticloud"],
)
async def test_log_search_accepts_all_sources(
    source: str,
    tool_client,  # type: ignore[no-untyped-def]
) -> None:
    out = await generic_tools.log_search(source=source, log_type="traffic")
    assert out["status"] == "success"


async def test_log_search_rejects_bad_source(tool_client) -> None:  # type: ignore[no-untyped-def]
    out = await generic_tools.log_search(source="tape", log_type="traffic")
    assert out["status"] == "error"


async def test_monitor_get_passes_params(tool_client) -> None:  # type: ignore[no-untyped-def]
    out = await generic_tools.monitor_get(path="firewall/session", params={"count": 1})
    assert out["status"] == "success"
