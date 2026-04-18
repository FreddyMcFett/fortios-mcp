"""Discovery tools backed by the bundled FortiOS Swagger definitions.

These let the LLM browse the 81 FortiOS 7.6.6 API files in
``api-docs/`` to locate the right endpoint before calling one of the
generic CRUD primitives (or any curated wrapper).
"""

from __future__ import annotations

import logging
from typing import Any

from fortios_mcp.server import get_mcp
from fortios_mcp.tools import err, ok
from fortios_mcp.utils.swagger import API_TYPES, get_swagger_index

logger = logging.getLogger(__name__)
mcp = get_mcp()


@mcp.tool()
async def list_api_categories(api_type: str | None = None) -> dict[str, Any]:
    """List available API categories (Swagger files) in the bundled docs.

    Args:
        api_type: Optional filter — ``"Configuration"``, ``"Monitor"``,
            ``"Log"`` or ``"Service"``. Omit to list every type.
    """
    try:
        index = get_swagger_index()
        if api_type:
            if api_type not in API_TYPES:
                raise ValueError(f"api_type must be one of {API_TYPES}")
            return ok({api_type: index.categories(api_type)})
        return ok({t: index.categories(t) for t in index.api_types()})
    except (ValueError, FileNotFoundError) as exc:
        return err(exc, tool="list_api_categories")


@mcp.tool()
async def list_endpoints(api_type: str, category: str) -> dict[str, Any]:
    """List every endpoint (method + path + summary) in one Swagger file.

    Args:
        api_type: ``"Configuration"``, ``"Monitor"``, ``"Log"`` or ``"Service"``.
        category: The file's category (see :func:`list_api_categories`).
    """
    try:
        index = get_swagger_index()
        endpoints = index.endpoints(api_type, category)
        return ok(
            {
                "api_type": api_type,
                "category": category,
                "count": len(endpoints),
                "endpoints": endpoints,
            }
        )
    except (KeyError, ValueError) as exc:
        return err(exc, tool="list_endpoints")


@mcp.tool()
async def describe_endpoint(
    api_type: str,
    category: str,
    path: str,
    method: str = "GET",
) -> dict[str, Any]:
    """Return parameters, body schema and response schema for one endpoint.

    Args:
        api_type: Swagger file type.
        category: Swagger file category.
        path: Swagger-relative path, e.g. ``"/firewall/policy"``.
        method: HTTP method (default ``"GET"``).
    """
    try:
        index = get_swagger_index()
        return ok(index.describe(api_type, category, path, method))
    except KeyError as exc:
        return err(exc, tool="describe_endpoint")


@mcp.tool()
async def search_endpoints(query: str, limit: int = 50) -> dict[str, Any]:
    """Substring search across all endpoint paths, summaries and tags.

    Args:
        query: Free-text search (e.g. ``"bgp"``, ``"policy"``, ``"sdwan"``).
        limit: Maximum hits to return.
    """
    try:
        index = get_swagger_index()
        hits = index.search(query, limit=max(1, min(limit, 500)))
        return ok({"query": query, "count": len(hits), "hits": hits})
    except ValueError as exc:
        return err(exc, tool="search_endpoints")
