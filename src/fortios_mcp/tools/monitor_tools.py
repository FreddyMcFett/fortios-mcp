"""Live monitoring: sessions, top talkers, bandwidth, licenses, SD-WAN, Wi-Fi, DHCP."""

from __future__ import annotations

import logging
from typing import Any

from fortios_mcp.server import get_mcp
from fortios_mcp.tools import err, get_client, ok, require_writes
from fortios_mcp.utils.errors import FortiOSError

logger = logging.getLogger(__name__)
mcp = get_mcp()


@mcp.tool()
async def list_sessions(
    vdom: str | None = None,
    filter: str | None = None,
    count: int = 50,
) -> dict[str, Any]:
    """List active firewall sessions.

    Args:
        filter: FortiOS session filter, e.g. ``"srcip==10.0.0.1"``.
        count: Maximum rows to return (1–1000).
    """
    try:
        params: dict[str, Any] = {"count": max(1, min(count, 1000))}
        if filter:
            params["filter"] = filter
        return ok(await get_client().monitor_get("firewall/session", vdom=vdom, params=params))
    except FortiOSError as exc:
        return err(exc, tool="list_sessions")


@mcp.tool()
@require_writes
async def kill_session(
    session_id: int, vdom: str | None = None
) -> dict[str, Any]:
    """Terminate a single firewall session. Write-guarded."""
    try:
        return ok(
            await get_client().monitor_post(
                "firewall/session/clear",
                {"session_id": session_id},
                vdom=vdom,
            )
        )
    except FortiOSError as exc:
        return err(exc, tool="kill_session")


@mcp.tool()
async def get_top_sources(
    vdom: str | None = None, count: int = 25
) -> dict[str, Any]:
    """Return top source IPs by bandwidth (FortiView)."""
    try:
        return ok(
            await get_client().monitor_get(
                "fortiview/statistics",
                vdom=vdom,
                params={"report_by": "source", "count": count},
            )
        )
    except FortiOSError as exc:
        return err(exc, tool="get_top_sources")


@mcp.tool()
async def get_top_destinations(
    vdom: str | None = None, count: int = 25
) -> dict[str, Any]:
    """Return top destination IPs by bandwidth (FortiView)."""
    try:
        return ok(
            await get_client().monitor_get(
                "fortiview/statistics",
                vdom=vdom,
                params={"report_by": "destination", "count": count},
            )
        )
    except FortiOSError as exc:
        return err(exc, tool="get_top_destinations")


@mcp.tool()
async def get_bandwidth_by_interface(vdom: str | None = None) -> dict[str, Any]:
    """Return live bandwidth counters for each interface."""
    try:
        return ok(await get_client().monitor_get("system/interface", vdom=vdom))
    except FortiOSError as exc:
        return err(exc, tool="get_bandwidth_by_interface")


@mcp.tool()
async def get_license_status() -> dict[str, Any]:
    """Return FortiCare / FortiGuard license status."""
    try:
        return ok(await get_client().monitor_get("license/status"))
    except FortiOSError as exc:
        return err(exc, tool="get_license_status")


@mcp.tool()
async def get_fortiguard_status() -> dict[str, Any]:
    """Return FortiGuard service subscription and contract info."""
    try:
        return ok(await get_client().monitor_get("fortiguard/service-communication-stats"))
    except FortiOSError as exc:
        return err(exc, tool="get_fortiguard_status")


@mcp.tool()
async def get_sdwan_health(vdom: str | None = None) -> dict[str, Any]:
    """Return SD-WAN health-check member status."""
    try:
        return ok(
            await get_client().monitor_get("virtual-wan/health-check", vdom=vdom)
        )
    except FortiOSError as exc:
        return err(exc, tool="get_sdwan_health")


@mcp.tool()
async def list_wifi_clients(vdom: str | None = None) -> dict[str, Any]:
    """List currently-connected wireless clients."""
    try:
        return ok(await get_client().monitor_get("wifi/client", vdom=vdom))
    except FortiOSError as exc:
        return err(exc, tool="list_wifi_clients")


@mcp.tool()
async def list_dhcp_leases(vdom: str | None = None) -> dict[str, Any]:
    """List active DHCP leases assigned by the FortiGate."""
    try:
        return ok(await get_client().monitor_get("system/dhcp", vdom=vdom))
    except FortiOSError as exc:
        return err(exc, tool="list_dhcp_leases")
