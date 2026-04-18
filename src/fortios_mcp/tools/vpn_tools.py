"""VPN: IPsec tunnels, SSL-VPN users and settings."""

from __future__ import annotations

import logging
from typing import Any

from fortios_mcp.server import get_mcp
from fortios_mcp.tools import err, get_client, ok, require_writes
from fortios_mcp.utils.errors import FortiOSError

logger = logging.getLogger(__name__)
mcp = get_mcp()


@mcp.tool()
async def list_ipsec_phase1(vdom: str | None = None) -> dict[str, Any]:
    """List IPsec phase 1 (interface) definitions."""
    try:
        return ok(await get_client().cmdb_get("vpn.ipsec/phase1-interface", vdom=vdom))
    except FortiOSError as exc:
        return err(exc, tool="list_ipsec_phase1")


@mcp.tool()
async def list_ipsec_phase2(vdom: str | None = None) -> dict[str, Any]:
    """List IPsec phase 2 (interface) definitions."""
    try:
        return ok(await get_client().cmdb_get("vpn.ipsec/phase2-interface", vdom=vdom))
    except FortiOSError as exc:
        return err(exc, tool="list_ipsec_phase2")


@mcp.tool()
async def get_ipsec_tunnel_status(vdom: str | None = None) -> dict[str, Any]:
    """Return live IPsec tunnel status (up/down, SPIs, counters)."""
    try:
        return ok(await get_client().monitor_get("vpn/ipsec", vdom=vdom))
    except FortiOSError as exc:
        return err(exc, tool="get_ipsec_tunnel_status")


@mcp.tool()
@require_writes
async def bring_up_ipsec_tunnel(
    phase1_name: str, vdom: str | None = None
) -> dict[str, Any]:
    """Bring an IPsec tunnel up. Write-guarded."""
    try:
        return ok(
            await get_client().monitor_post(
                "vpn/ipsec/tunnel/bring-up",
                {"p1name": phase1_name},
                vdom=vdom,
            )
        )
    except FortiOSError as exc:
        return err(exc, tool="bring_up_ipsec_tunnel")


@mcp.tool()
@require_writes
async def bring_down_ipsec_tunnel(
    phase1_name: str, vdom: str | None = None
) -> dict[str, Any]:
    """Bring an IPsec tunnel down. Write-guarded."""
    try:
        return ok(
            await get_client().monitor_post(
                "vpn/ipsec/tunnel/bring-down",
                {"p1name": phase1_name},
                vdom=vdom,
            )
        )
    except FortiOSError as exc:
        return err(exc, tool="bring_down_ipsec_tunnel")


@mcp.tool()
async def list_ssl_vpn_sessions(vdom: str | None = None) -> dict[str, Any]:
    """List currently connected SSL-VPN users."""
    try:
        return ok(await get_client().monitor_get("vpn/ssl", vdom=vdom))
    except FortiOSError as exc:
        return err(exc, tool="list_ssl_vpn_sessions")


@mcp.tool()
async def get_ssl_vpn_settings(vdom: str | None = None) -> dict[str, Any]:
    """Return the SSL-VPN settings CMDB object."""
    try:
        return ok(await get_client().cmdb_get("vpn.ssl/settings", vdom=vdom))
    except FortiOSError as exc:
        return err(exc, tool="get_ssl_vpn_settings")
