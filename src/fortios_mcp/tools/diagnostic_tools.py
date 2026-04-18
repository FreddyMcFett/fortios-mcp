"""Diagnostics: packet capture, ping, traceroute."""

from __future__ import annotations

import logging
from typing import Any

from fortios_mcp.server import get_mcp
from fortios_mcp.tools import err, get_client, ok, require_writes
from fortios_mcp.utils.errors import FortiOSError

logger = logging.getLogger(__name__)
mcp = get_mcp()


@mcp.tool()
async def list_packet_captures() -> dict[str, Any]:
    """List packet-sniffer profiles defined on the FortiGate."""
    try:
        return ok(await get_client().cmdb_get("firewall/sniffer"))
    except FortiOSError as exc:
        return err(exc, tool="list_packet_captures")


@mcp.tool()
@require_writes
async def start_packet_capture(
    interface: str,
    filter: str | None = None,
    max_packets: int = 4000,
) -> dict[str, Any]:
    """Start a packet sniffer session. Write-guarded."""
    try:
        body: dict[str, Any] = {
            "interface": interface,
            "max-packet-count": max(1, min(max_packets, 1000000)),
        }
        if filter:
            body["filter"] = filter
        return ok(await get_client().service_execute("sniffer/start", body))
    except FortiOSError as exc:
        return err(exc, tool="start_packet_capture")


@mcp.tool()
@require_writes
async def stop_packet_capture(session_id: int) -> dict[str, Any]:
    """Stop a running packet sniffer session. Write-guarded."""
    try:
        return ok(await get_client().service_execute("sniffer/stop", {"session_id": session_id}))
    except FortiOSError as exc:
        return err(exc, tool="stop_packet_capture")


@mcp.tool()
async def download_packet_capture(session_id: int) -> dict[str, Any]:
    """Return the download descriptor for a captured PCAP."""
    try:
        return ok(await get_client().monitor_get(f"system/sniffer/download/{session_id}"))
    except FortiOSError as exc:
        return err(exc, tool="download_packet_capture")


@mcp.tool()
async def ping(
    destination: str,
    interface: str | None = None,
    count: int = 5,
    vdom: str | None = None,
) -> dict[str, Any]:
    """Send ICMP echo requests from the FortiGate.

    Args:
        destination: Target IP or hostname.
        interface: Source interface name (optional).
        count: Number of packets (1-100).
    """
    try:
        body: dict[str, Any] = {"host": destination, "count": max(1, min(count, 100))}
        if interface:
            body["interface"] = interface
        return ok(await get_client().monitor_post("network/debug/ping", body, vdom=vdom))
    except FortiOSError as exc:
        return err(exc, tool="ping")


@mcp.tool()
async def traceroute(
    destination: str,
    interface: str | None = None,
    vdom: str | None = None,
) -> dict[str, Any]:
    """Run a traceroute from the FortiGate to ``destination``."""
    try:
        body: dict[str, Any] = {"host": destination}
        if interface:
            body["interface"] = interface
        return ok(await get_client().monitor_post("network/debug/traceroute", body, vdom=vdom))
    except FortiOSError as exc:
        return err(exc, tool="traceroute")
