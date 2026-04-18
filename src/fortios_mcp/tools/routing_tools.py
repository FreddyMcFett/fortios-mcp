"""Routing: static routes, BGP, OSPF, routing monitor, ARP."""

from __future__ import annotations

import logging
from typing import Any

from fortios_mcp.server import get_mcp
from fortios_mcp.tools import err, get_client, ok, require_writes
from fortios_mcp.utils.errors import FortiOSError

logger = logging.getLogger(__name__)
mcp = get_mcp()


@mcp.tool()
async def list_static_routes(vdom: str | None = None) -> dict[str, Any]:
    """List configured static routes."""
    try:
        return ok(await get_client().cmdb_get("router/static", vdom=vdom))
    except FortiOSError as exc:
        return err(exc, tool="list_static_routes")


@mcp.tool()
@require_writes
async def add_static_route(body: dict[str, Any], vdom: str | None = None) -> dict[str, Any]:
    """Create a static route. Write-guarded."""
    try:
        return ok(await get_client().cmdb_add("router/static", body, vdom=vdom))
    except FortiOSError as exc:
        return err(exc, tool="add_static_route")


@mcp.tool()
@require_writes
async def delete_static_route(seq_num: int, vdom: str | None = None) -> dict[str, Any]:
    """Delete a static route by its sequence number. Write-guarded."""
    try:
        return ok(await get_client().cmdb_delete(f"router/static/{seq_num}", vdom=vdom))
    except FortiOSError as exc:
        return err(exc, tool="delete_static_route")


@mcp.tool()
async def get_routing_table(vdom: str | None = None, ip_version: str = "ipv4") -> dict[str, Any]:
    """Return the active routing table (FIB)."""
    try:
        if ip_version not in {"ipv4", "ipv6"}:
            raise ValueError("ip_version must be 'ipv4' or 'ipv6'")
        path = "router/ipv4" if ip_version == "ipv4" else "router/ipv6"
        return ok(await get_client().monitor_get(path, vdom=vdom))
    except (FortiOSError, ValueError) as exc:
        return err(exc, tool="get_routing_table")


@mcp.tool()
async def get_bgp_neighbors(vdom: str | None = None) -> dict[str, Any]:
    """Return BGP neighbor status."""
    try:
        return ok(await get_client().monitor_get("router/bgp/neighbors", vdom=vdom))
    except FortiOSError as exc:
        return err(exc, tool="get_bgp_neighbors")


@mcp.tool()
async def get_ospf_neighbors(vdom: str | None = None) -> dict[str, Any]:
    """Return OSPF neighbor status."""
    try:
        return ok(await get_client().monitor_get("router/ospf/neighbors", vdom=vdom))
    except FortiOSError as exc:
        return err(exc, tool="get_ospf_neighbors")


@mcp.tool()
async def get_policy_routes(vdom: str | None = None) -> dict[str, Any]:
    """Return configured policy-based routes."""
    try:
        return ok(await get_client().cmdb_get("router/policy", vdom=vdom))
    except FortiOSError as exc:
        return err(exc, tool="get_policy_routes")


@mcp.tool()
async def get_arp_table(vdom: str | None = None) -> dict[str, Any]:
    """Return the live ARP table."""
    try:
        return ok(await get_client().monitor_get("network/arp", vdom=vdom))
    except FortiOSError as exc:
        return err(exc, tool="get_arp_table")
