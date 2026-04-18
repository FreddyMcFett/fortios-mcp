"""Verify every mutating tool is blocked until FORTIOS_ENABLE_WRITES is true."""

from __future__ import annotations

import inspect
import pytest

from fortios_mcp.tools import (
    diagnostic_tools,
    firewall_tools,
    generic_tools,
    monitor_tools,
    routing_tools,
    system_tools,
    vpn_tools,
)

WRITE_MODULES = (
    generic_tools,
    firewall_tools,
    routing_tools,
    vpn_tools,
    monitor_tools,
    system_tools,
    diagnostic_tools,
)

EXPECTED_WRITE_TOOLS: set[str] = {
    "cmdb_set",
    "cmdb_add",
    "cmdb_update",
    "cmdb_delete",
    "service_execute",
    "set_interface",
    "reboot_device",
    "shutdown_device",
    "add_firewall_policy",
    "update_firewall_policy",
    "delete_firewall_policy",
    "move_firewall_policy",
    "add_static_route",
    "delete_static_route",
    "bring_up_ipsec_tunnel",
    "bring_down_ipsec_tunnel",
    "kill_session",
    "start_packet_capture",
    "stop_packet_capture",
}


def _collect_tools() -> dict[str, object]:
    tools: dict[str, object] = {}
    for mod in WRITE_MODULES:
        for name, obj in inspect.getmembers(mod):
            if inspect.iscoroutinefunction(obj):
                tools[name] = obj
    return tools


def test_every_expected_tool_is_guarded() -> None:
    tools = _collect_tools()
    missing = [
        name for name in EXPECTED_WRITE_TOOLS
        if not getattr(tools.get(name), "__fortios_requires_writes__", False)
    ]
    assert not missing, f"Write-guard missing on: {missing}"


@pytest.mark.parametrize("tool_name", sorted(EXPECTED_WRITE_TOOLS))
async def test_guard_blocks_when_writes_disabled(
    tool_name: str,
    set_writes_enabled,  # type: ignore[no-untyped-def]
    tool_client,  # type: ignore[no-untyped-def]
) -> None:
    set_writes_enabled(False)
    tools = _collect_tools()
    fn = tools[tool_name]
    sig = inspect.signature(fn)
    kwargs: dict[str, object] = {}
    for pname, param in sig.parameters.items():
        if param.default is inspect.Parameter.empty:
            kwargs[pname] = _sample_value(pname)
    result = await fn(**kwargs)  # type: ignore[misc]
    assert isinstance(result, dict) and result["status"] == "error"
    assert "disabled" in result["message"].lower()


def _sample_value(name: str) -> object:
    if name.endswith("id") or name in {"session_id", "target", "count", "max_packets", "seq_num"}:
        return 1
    if name == "body":
        return {"name": "test"}
    if name == "action":
        return "before"
    if name == "path":
        return "firewall/policy"
    if name == "source":
        return "disk"
    if name == "log_type":
        return "traffic"
    return "test"
