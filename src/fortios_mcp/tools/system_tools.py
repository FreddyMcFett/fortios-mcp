"""Curated system-level tools: status, interfaces, admins, HA, config backup, reboot."""

from __future__ import annotations

import logging
from typing import Any

from fortios_mcp.server import get_mcp
from fortios_mcp.tools import err, get_client, ok, require_writes
from fortios_mcp.utils.errors import FortiOSError

logger = logging.getLogger(__name__)
mcp = get_mcp()


@mcp.tool()
async def get_system_status() -> dict[str, Any]:
    """Return FortiOS version, serial, uptime, hostname and platform."""
    try:
        return ok(await get_client().monitor_get("system/status"))
    except FortiOSError as exc:
        return err(exc, tool="get_system_status")


@mcp.tool()
async def get_system_performance() -> dict[str, Any]:
    """Return current CPU, memory, and session counters."""
    try:
        return ok(await get_client().monitor_get("system/resource/usage"))
    except FortiOSError as exc:
        return err(exc, tool="get_system_performance")


@mcp.tool()
async def get_system_global() -> dict[str, Any]:
    """Return the ``system global`` CMDB object."""
    try:
        return ok(await get_client().cmdb_get("system/global"))
    except FortiOSError as exc:
        return err(exc, tool="get_system_global")


@mcp.tool()
async def list_interfaces(vdom: str | None = None) -> dict[str, Any]:
    """List every physical/virtual interface configured on the FortiGate."""
    try:
        return ok(await get_client().cmdb_get("system/interface", vdom=vdom))
    except FortiOSError as exc:
        return err(exc, tool="list_interfaces")


@mcp.tool()
async def get_interface(name: str, vdom: str | None = None) -> dict[str, Any]:
    """Return the CMDB entry for a single interface."""
    try:
        return ok(await get_client().cmdb_get(f"system/interface/{name}", vdom=vdom))
    except FortiOSError as exc:
        return err(exc, tool="get_interface")


@mcp.tool()
async def get_interface_status() -> dict[str, Any]:
    """Return live link/speed/duplex status for all interfaces."""
    try:
        return ok(await get_client().monitor_get("system/interface"))
    except FortiOSError as exc:
        return err(exc, tool="get_interface_status")


@mcp.tool()
@require_writes
async def set_interface(
    name: str, body: dict[str, Any], vdom: str | None = None
) -> dict[str, Any]:
    """Update an interface's CMDB entry. Write-guarded."""
    try:
        return ok(await get_client().cmdb_set(f"system/interface/{name}", body, vdom=vdom))
    except FortiOSError as exc:
        return err(exc, tool="set_interface")


@mcp.tool()
async def list_admins() -> dict[str, Any]:
    """List configured administrators."""
    try:
        return ok(await get_client().cmdb_get("system/admin"))
    except FortiOSError as exc:
        return err(exc, tool="list_admins")


@mcp.tool()
async def get_ha_status() -> dict[str, Any]:
    """Return HA cluster status and member roles."""
    try:
        return ok(await get_client().monitor_get("system/ha-statistics"))
    except FortiOSError as exc:
        return err(exc, tool="get_ha_status")


@mcp.tool()
async def get_ha_checksum() -> dict[str, Any]:
    """Return the HA configuration checksum across cluster members."""
    try:
        return ok(await get_client().monitor_get("system/ha-checksums"))
    except FortiOSError as exc:
        return err(exc, tool="get_ha_checksum")


@mcp.tool()
async def get_firmware_info() -> dict[str, Any]:
    """Return current firmware and available upgrade images."""
    try:
        return ok(await get_client().monitor_get("system/firmware"))
    except FortiOSError as exc:
        return err(exc, tool="get_firmware_info")


@mcp.tool()
async def backup_config(scope: str = "global", vdom: str | None = None) -> dict[str, Any]:
    """Download the running configuration.

    Args:
        scope: ``"global"`` for the full device, ``"vdom"`` for a single VDOM.
    """
    try:
        if scope not in {"global", "vdom"}:
            raise ValueError("scope must be 'global' or 'vdom'")
        return ok(
            await get_client().monitor_get(
                "system/config/backup",
                vdom=vdom,
                params={"scope": scope},
            )
        )
    except (FortiOSError, ValueError) as exc:
        return err(exc, tool="backup_config")


@mcp.tool()
@require_writes
async def reboot_device(event_log_message: str = "Rebooted via fortios-mcp") -> dict[str, Any]:
    """Reboot the FortiGate. Write-guarded — use with extreme care."""
    try:
        return ok(
            await get_client().monitor_post(
                "system/os/reboot",
                {"event_log_message": event_log_message},
            )
        )
    except FortiOSError as exc:
        return err(exc, tool="reboot_device")


@mcp.tool()
@require_writes
async def shutdown_device(event_log_message: str = "Shutdown via fortios-mcp") -> dict[str, Any]:
    """Shut down the FortiGate. Write-guarded."""
    try:
        return ok(
            await get_client().monitor_post(
                "system/os/shutdown",
                {"event_log_message": event_log_message},
            )
        )
    except FortiOSError as exc:
        return err(exc, tool="shutdown_device")
