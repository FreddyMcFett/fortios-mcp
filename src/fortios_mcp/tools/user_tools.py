"""User and authentication: local users, groups, LDAP, RADIUS, FSSO."""

from __future__ import annotations

import logging
from typing import Any

from fortios_mcp.server import get_mcp
from fortios_mcp.tools import err, get_client, ok
from fortios_mcp.utils.errors import FortiOSError

logger = logging.getLogger(__name__)
mcp = get_mcp()


@mcp.tool()
async def list_local_users(vdom: str | None = None) -> dict[str, Any]:
    """List local user accounts."""
    try:
        return ok(await get_client().cmdb_get("user/local", vdom=vdom))
    except FortiOSError as exc:
        return err(exc, tool="list_local_users")


@mcp.tool()
async def list_user_groups(vdom: str | None = None) -> dict[str, Any]:
    """List user groups."""
    try:
        return ok(await get_client().cmdb_get("user/group", vdom=vdom))
    except FortiOSError as exc:
        return err(exc, tool="list_user_groups")


@mcp.tool()
async def list_ldap_servers(vdom: str | None = None) -> dict[str, Any]:
    """List configured LDAP authentication servers."""
    try:
        return ok(await get_client().cmdb_get("user/ldap", vdom=vdom))
    except FortiOSError as exc:
        return err(exc, tool="list_ldap_servers")


@mcp.tool()
async def list_radius_servers(vdom: str | None = None) -> dict[str, Any]:
    """List configured RADIUS authentication servers."""
    try:
        return ok(await get_client().cmdb_get("user/radius", vdom=vdom))
    except FortiOSError as exc:
        return err(exc, tool="list_radius_servers")


@mcp.tool()
async def list_fsso_agents(vdom: str | None = None) -> dict[str, Any]:
    """List FSSO (Fortinet Single Sign-On) polling agents."""
    try:
        return ok(await get_client().cmdb_get("user/fsso", vdom=vdom))
    except FortiOSError as exc:
        return err(exc, tool="list_fsso_agents")


@mcp.tool()
async def list_firewall_auth_sessions(vdom: str | None = None) -> dict[str, Any]:
    """List currently authenticated firewall users."""
    try:
        return ok(await get_client().monitor_get("user/firewall", vdom=vdom))
    except FortiOSError as exc:
        return err(exc, tool="list_firewall_auth_sessions")
