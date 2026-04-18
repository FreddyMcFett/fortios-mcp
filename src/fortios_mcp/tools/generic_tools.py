"""Generic CRUD primitives that expose the full FortiOS API surface.

These eight tools mirror the underlying REST methods on
``/api/v2/{cmdb,monitor,log,service}`` and are the fallback when no
curated wrapper exists for the endpoint the caller needs. They are
intentionally thin — argument validation, write-guarding, and response
enveloping only.
"""

from __future__ import annotations

import logging
from typing import Any

from fortios_mcp.server import get_mcp
from fortios_mcp.tools import err, get_client, ok, require_writes
from fortios_mcp.utils.errors import FortiOSError
from fortios_mcp.utils.validation import validate_cmdb_path

logger = logging.getLogger(__name__)
mcp = get_mcp()


@mcp.tool()
async def cmdb_get(
    path: str,
    vdom: str | None = None,
    filter: str | None = None,
    format: str | None = None,
    start: int | None = None,
    count: int | None = None,
) -> dict[str, Any]:
    """Read a FortiOS CMDB resource.

    Args:
        path: CMDB path relative to ``/api/v2/cmdb`` (e.g. ``"firewall/policy"``).
        vdom: Target VDOM. Defaults to ``FORTIOS_DEFAULT_VDOM``.
        filter: FortiOS filter expression, e.g. ``"name==HTTPS"``.
        format: Comma-separated list of fields to include.
        start: Pagination offset.
        count: Maximum number of entries to return.

    Returns:
        Standard ``{"status": ..., "data": ...}`` envelope. ``data`` holds the
        FortiOS response including the ``results`` array.
    """
    try:
        validate_cmdb_path(path)
        params: dict[str, Any] = {}
        if filter:
            params["filter"] = filter
        if format:
            params["format"] = format
        if start is not None:
            params["start"] = start
        if count is not None:
            params["count"] = count
        data = await get_client().cmdb_get(path, vdom=vdom, params=params or None)
        return ok(data)
    except (FortiOSError, ValueError) as exc:
        logger.error("cmdb_get(%s) failed: %s", path, exc)
        return err(exc, tool="cmdb_get")


@mcp.tool()
@require_writes
async def cmdb_set(
    path: str, body: dict[str, Any], vdom: str | None = None
) -> dict[str, Any]:
    """Replace a CMDB resource (HTTP PUT). Write-guarded."""
    try:
        validate_cmdb_path(path)
        data = await get_client().cmdb_set(path, body, vdom=vdom)
        return ok(data)
    except (FortiOSError, ValueError) as exc:
        return err(exc, tool="cmdb_set")


@mcp.tool()
@require_writes
async def cmdb_add(
    path: str, body: dict[str, Any], vdom: str | None = None
) -> dict[str, Any]:
    """Create a CMDB resource (HTTP POST). Write-guarded."""
    try:
        validate_cmdb_path(path)
        data = await get_client().cmdb_add(path, body, vdom=vdom)
        return ok(data)
    except (FortiOSError, ValueError) as exc:
        return err(exc, tool="cmdb_add")


@mcp.tool()
@require_writes
async def cmdb_update(
    path: str, body: dict[str, Any], vdom: str | None = None
) -> dict[str, Any]:
    """Partial-update a CMDB resource (HTTP PUT on a specific key). Write-guarded."""
    try:
        validate_cmdb_path(path)
        data = await get_client().cmdb_update(path, body, vdom=vdom)
        return ok(data)
    except (FortiOSError, ValueError) as exc:
        return err(exc, tool="cmdb_update")


@mcp.tool()
@require_writes
async def cmdb_delete(path: str, vdom: str | None = None) -> dict[str, Any]:
    """Delete a CMDB resource (HTTP DELETE). Write-guarded."""
    try:
        validate_cmdb_path(path)
        data = await get_client().cmdb_delete(path, vdom=vdom)
        return ok(data)
    except (FortiOSError, ValueError) as exc:
        return err(exc, tool="cmdb_delete")


@mcp.tool()
async def monitor_get(
    path: str,
    vdom: str | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Call any ``/api/v2/monitor/...`` GET endpoint.

    Args:
        path: Monitor path, e.g. ``"system/status"`` or ``"firewall/session"``.
        vdom: Target VDOM.
        params: Arbitrary query parameters accepted by the endpoint.
    """
    try:
        data = await get_client().monitor_get(path, vdom=vdom, params=params)
        return ok(data)
    except FortiOSError as exc:
        return err(exc, tool="monitor_get")


@mcp.tool()
async def log_search(
    source: str,
    log_type: str,
    filter: str | None = None,
    start: int = 0,
    rows: int = 50,
    vdom: str | None = None,
) -> dict[str, Any]:
    """Search logs stored on the FortiGate.

    Args:
        source: Log storage to query (``"disk"``, ``"memory"``,
            ``"fortianalyzer"`` or ``"forticloud"``).
        log_type: Log category — ``"traffic"``, ``"event"``, ``"utm"``,
            ``"security"`` etc.
        filter: FortiOS log filter expression.
        start: Offset for pagination.
        rows: Number of rows to return (1–1000).
    """
    try:
        if source not in {"disk", "memory", "fortianalyzer", "forticloud"}:
            raise ValueError("source must be disk|memory|fortianalyzer|forticloud")
        params: dict[str, Any] = {"start": start, "rows": max(1, min(rows, 1000))}
        if filter:
            params["filter"] = filter
        data = await get_client().log_get(
            f"{source}/{log_type}", vdom=vdom, params=params
        )
        return ok(data)
    except (FortiOSError, ValueError) as exc:
        return err(exc, tool="log_search")


@mcp.tool()
@require_writes
async def service_execute(
    path: str,
    body: dict[str, Any] | None = None,
    vdom: str | None = None,
) -> dict[str, Any]:
    """Invoke a ``/api/v2/service/...`` operation. Write-guarded."""
    try:
        data = await get_client().service_execute(path, body, vdom=vdom)
        return ok(data)
    except FortiOSError as exc:
        return err(exc, tool="service_execute")
