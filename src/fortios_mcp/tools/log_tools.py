"""Log search across disk, memory, FortiAnalyzer and FortiCloud backends."""

from __future__ import annotations

import logging
from typing import Any

from fortios_mcp.server import get_mcp
from fortios_mcp.tools import err, get_client, ok
from fortios_mcp.utils.errors import FortiOSError

logger = logging.getLogger(__name__)
mcp = get_mcp()


async def _log_search(
    source: str,
    log_type: str,
    vdom: str | None,
    filter: str | None,
    start: int,
    rows: int,
) -> dict[str, Any]:
    params: dict[str, Any] = {"start": start, "rows": max(1, min(rows, 1000))}
    if filter:
        params["filter"] = filter
    data = await get_client().log_get(f"{source}/{log_type}", vdom=vdom, params=params)
    return ok(data)


@mcp.tool()
async def log_search_disk(
    log_type: str = "traffic",
    filter: str | None = None,
    start: int = 0,
    rows: int = 50,
    vdom: str | None = None,
) -> dict[str, Any]:
    """Search the on-disk log store (``/api/v2/log/disk/{type}``)."""
    try:
        return await _log_search("disk", log_type, vdom, filter, start, rows)
    except FortiOSError as exc:
        return err(exc, tool="log_search_disk")


@mcp.tool()
async def log_search_memory(
    log_type: str = "traffic",
    filter: str | None = None,
    start: int = 0,
    rows: int = 50,
    vdom: str | None = None,
) -> dict[str, Any]:
    """Search the in-memory log store (``/api/v2/log/memory/{type}``)."""
    try:
        return await _log_search("memory", log_type, vdom, filter, start, rows)
    except FortiOSError as exc:
        return err(exc, tool="log_search_memory")


@mcp.tool()
async def log_search_fortianalyzer(
    log_type: str = "traffic",
    filter: str | None = None,
    start: int = 0,
    rows: int = 50,
    vdom: str | None = None,
) -> dict[str, Any]:
    """Search logs stored on the associated FortiAnalyzer."""
    try:
        return await _log_search("fortianalyzer", log_type, vdom, filter, start, rows)
    except FortiOSError as exc:
        return err(exc, tool="log_search_fortianalyzer")


@mcp.tool()
async def log_search_forticloud(
    log_type: str = "traffic",
    filter: str | None = None,
    start: int = 0,
    rows: int = 50,
    vdom: str | None = None,
) -> dict[str, Any]:
    """Search logs stored on FortiCloud."""
    try:
        return await _log_search("forticloud", log_type, vdom, filter, start, rows)
    except FortiOSError as exc:
        return err(exc, tool="log_search_forticloud")


@mcp.tool()
async def log_download(
    source: str = "disk",
    log_type: str = "traffic",
    vdom: str | None = None,
) -> dict[str, Any]:
    """Request a log-file download from the FortiGate.

    Returns the FortiOS download-descriptor payload; actual retrieval uses
    the download URL returned inside ``results``.
    """
    try:
        if source not in {"disk", "memory", "fortianalyzer", "forticloud"}:
            raise ValueError("source must be disk|memory|fortianalyzer|forticloud")
        return ok(
            await get_client().log_get(
                f"{source}/{log_type}/archive/download",
                vdom=vdom,
            )
        )
    except (FortiOSError, ValueError) as exc:
        return err(exc, tool="log_download")
