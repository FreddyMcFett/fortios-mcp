"""Firewall configuration: policies, addresses, services, VIPs, IP pools."""

from __future__ import annotations

import logging
from typing import Any

from fortios_mcp.server import get_mcp
from fortios_mcp.tools import err, get_client, ok, require_writes
from fortios_mcp.utils.errors import FortiOSError

logger = logging.getLogger(__name__)
mcp = get_mcp()


@mcp.tool()
async def list_firewall_policies(
    vdom: str | None = None, filter: str | None = None
) -> dict[str, Any]:
    """List IPv4/IPv6 firewall policies, optionally filtered."""
    try:
        params = {"filter": filter} if filter else None
        return ok(await get_client().cmdb_get("firewall/policy", vdom=vdom, params=params))
    except FortiOSError as exc:
        return err(exc, tool="list_firewall_policies")


@mcp.tool()
async def get_firewall_policy(policyid: int, vdom: str | None = None) -> dict[str, Any]:
    """Return a single firewall policy by ID."""
    try:
        return ok(await get_client().cmdb_get(f"firewall/policy/{policyid}", vdom=vdom))
    except FortiOSError as exc:
        return err(exc, tool="get_firewall_policy")


@mcp.tool()
@require_writes
async def add_firewall_policy(body: dict[str, Any], vdom: str | None = None) -> dict[str, Any]:
    """Create a new firewall policy. Write-guarded.

    Args:
        body: FortiOS policy payload. Required keys typically include
            ``name``, ``srcintf``, ``dstintf``, ``srcaddr``, ``dstaddr``,
            ``service``, ``action``, ``schedule``.
    """
    try:
        return ok(await get_client().cmdb_add("firewall/policy", body, vdom=vdom))
    except FortiOSError as exc:
        return err(exc, tool="add_firewall_policy")


@mcp.tool()
@require_writes
async def update_firewall_policy(
    policyid: int, body: dict[str, Any], vdom: str | None = None
) -> dict[str, Any]:
    """Update an existing firewall policy. Write-guarded."""
    try:
        return ok(await get_client().cmdb_set(f"firewall/policy/{policyid}", body, vdom=vdom))
    except FortiOSError as exc:
        return err(exc, tool="update_firewall_policy")


@mcp.tool()
@require_writes
async def delete_firewall_policy(policyid: int, vdom: str | None = None) -> dict[str, Any]:
    """Delete a firewall policy by ID. Write-guarded."""
    try:
        return ok(await get_client().cmdb_delete(f"firewall/policy/{policyid}", vdom=vdom))
    except FortiOSError as exc:
        return err(exc, tool="delete_firewall_policy")


@mcp.tool()
@require_writes
async def move_firewall_policy(
    policyid: int,
    action: str,
    target: int,
    vdom: str | None = None,
) -> dict[str, Any]:
    """Reorder a firewall policy. Write-guarded.

    Args:
        policyid: Policy ID to move.
        action: ``"before"`` or ``"after"``.
        target: Reference policy ID.
    """
    try:
        if action not in {"before", "after"}:
            raise ValueError("action must be 'before' or 'after'")
        return ok(
            await get_client().cmdb_update(
                f"firewall/policy/{policyid}",
                {"action": action, "target": target},
                vdom=vdom,
            )
        )
    except (FortiOSError, ValueError) as exc:
        return err(exc, tool="move_firewall_policy")


@mcp.tool()
async def list_firewall_addresses(vdom: str | None = None) -> dict[str, Any]:
    """List IPv4 address objects."""
    try:
        return ok(await get_client().cmdb_get("firewall/address", vdom=vdom))
    except FortiOSError as exc:
        return err(exc, tool="list_firewall_addresses")


@mcp.tool()
async def list_firewall_address_groups(vdom: str | None = None) -> dict[str, Any]:
    """List IPv4 address groups."""
    try:
        return ok(await get_client().cmdb_get("firewall/addrgrp", vdom=vdom))
    except FortiOSError as exc:
        return err(exc, tool="list_firewall_address_groups")


@mcp.tool()
async def list_firewall_services(vdom: str | None = None) -> dict[str, Any]:
    """List firewall service (custom) definitions."""
    try:
        return ok(await get_client().cmdb_get("firewall.service/custom", vdom=vdom))
    except FortiOSError as exc:
        return err(exc, tool="list_firewall_services")


@mcp.tool()
async def list_firewall_vips(vdom: str | None = None) -> dict[str, Any]:
    """List IPv4 virtual IPs."""
    try:
        return ok(await get_client().cmdb_get("firewall/vip", vdom=vdom))
    except FortiOSError as exc:
        return err(exc, tool="list_firewall_vips")


@mcp.tool()
async def list_firewall_ippools(vdom: str | None = None) -> dict[str, Any]:
    """List IPv4 NAT IP pools."""
    try:
        return ok(await get_client().cmdb_get("firewall/ippool", vdom=vdom))
    except FortiOSError as exc:
        return err(exc, tool="list_firewall_ippools")
