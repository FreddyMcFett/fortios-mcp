"""Security profiles: antivirus, IPS, web/DNS/email filter, app control, DLP, SSL."""

from __future__ import annotations

import logging
from typing import Any

from fortios_mcp.server import get_mcp
from fortios_mcp.tools import err, get_client, ok
from fortios_mcp.utils.errors import FortiOSError

logger = logging.getLogger(__name__)
mcp = get_mcp()


@mcp.tool()
async def list_antivirus_profiles(vdom: str | None = None) -> dict[str, Any]:
    """List antivirus profiles."""
    try:
        return ok(await get_client().cmdb_get("antivirus/profile", vdom=vdom))
    except FortiOSError as exc:
        return err(exc, tool="list_antivirus_profiles")


@mcp.tool()
async def list_ips_sensors(vdom: str | None = None) -> dict[str, Any]:
    """List IPS (intrusion-prevention) sensors."""
    try:
        return ok(await get_client().cmdb_get("ips/sensor", vdom=vdom))
    except FortiOSError as exc:
        return err(exc, tool="list_ips_sensors")


@mcp.tool()
async def list_web_filter_profiles(vdom: str | None = None) -> dict[str, Any]:
    """List web filter profiles."""
    try:
        return ok(await get_client().cmdb_get("webfilter/profile", vdom=vdom))
    except FortiOSError as exc:
        return err(exc, tool="list_web_filter_profiles")


@mcp.tool()
async def list_dns_filter_profiles(vdom: str | None = None) -> dict[str, Any]:
    """List DNS filter profiles."""
    try:
        return ok(await get_client().cmdb_get("dnsfilter/profile", vdom=vdom))
    except FortiOSError as exc:
        return err(exc, tool="list_dns_filter_profiles")


@mcp.tool()
async def list_application_control_lists(vdom: str | None = None) -> dict[str, Any]:
    """List application-control signature lists."""
    try:
        return ok(await get_client().cmdb_get("application/list", vdom=vdom))
    except FortiOSError as exc:
        return err(exc, tool="list_application_control_lists")


@mcp.tool()
async def list_dlp_profiles(vdom: str | None = None) -> dict[str, Any]:
    """List Data Loss Prevention profiles."""
    try:
        return ok(await get_client().cmdb_get("dlp/profile", vdom=vdom))
    except FortiOSError as exc:
        return err(exc, tool="list_dlp_profiles")


@mcp.tool()
async def list_ssl_inspection_profiles(vdom: str | None = None) -> dict[str, Any]:
    """List SSL/TLS inspection profiles."""
    try:
        return ok(
            await get_client().cmdb_get("firewall/ssl-ssh-profile", vdom=vdom)
        )
    except FortiOSError as exc:
        return err(exc, tool="list_ssl_inspection_profiles")


@mcp.tool()
async def list_profile_groups(vdom: str | None = None) -> dict[str, Any]:
    """List UTM profile groups."""
    try:
        return ok(await get_client().cmdb_get("firewall/profile-group", vdom=vdom))
    except FortiOSError as exc:
        return err(exc, tool="list_profile_groups")
