"""FastMCP server bootstrap for FortiOS.

The module-level ``mcp`` instance is defined up-front so tool modules can
import and decorate against it without timing hazards. :func:`build_server`
registers the tool modules; :func:`main` selects a transport and runs.
"""

from __future__ import annotations

import logging
import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP

from fortios_mcp import __version__
from fortios_mcp.api.client import FortiOSClient
from fortios_mcp.utils.config import Settings, get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def _lifespan(_server: FastMCP) -> AsyncIterator[dict[str, FortiOSClient]]:
    # Imports inside the lifespan keep module-load order independent of runtime wiring.
    from fortios_mcp.tools import set_client

    settings = get_settings()
    settings.require_credentials()
    logger.info("Starting FortiOS MCP server v%s", __version__)
    client = FortiOSClient.from_settings(settings)
    set_client(client)
    try:
        try:
            await client.probe()
        except Exception as exc:  # pragma: no cover - network probe
            logger.warning(
                "Initial FortiGate probe failed (%s); tools will surface the error on first call.",
                exc,
            )
        yield {"fortios_client": client}
    finally:
        logger.info("Shutting down FortiOS MCP server")
        set_client(None)
        await client.close()


mcp: FastMCP = FastMCP(
    "FortiOS MCP Server",
    instructions=(
        "Drives a FortiGate via its REST API v2 for configuration, "
        "troubleshooting, monitoring and review. Read-only by default; "
        "set FORTIOS_ENABLE_WRITES=true to allow mutating tools."
    ),
    stateless_http=True,
    lifespan=_lifespan,
)


def get_mcp() -> FastMCP:
    """Return the shared FastMCP instance."""
    return mcp


def build_server(settings: Settings | None = None) -> FastMCP:
    """Ensure tools are registered and logging is configured."""
    from fortios_mcp.tools import register_all

    settings = settings or get_settings()
    settings.configure_logging()
    register_all(mcp)
    return mcp


def _detect_mode(requested: str) -> str:
    if requested != "auto":
        return requested
    if os.path.exists("/.dockerenv") or os.getenv("DOCKER_CONTAINER") == "1":
        return "http"
    if not sys.stdin.isatty():
        return "stdio"
    return "stdio"


def main() -> None:
    """CLI entry point."""
    settings = get_settings()
    build_server(settings)
    mode = _detect_mode(settings.MCP_SERVER_MODE)
    logger.info("Launching FortiOS MCP server in %s mode", mode)
    if mode == "stdio":
        mcp.run(transport="stdio")
    elif mode == "http":
        mcp.settings.host = settings.MCP_SERVER_HOST
        mcp.settings.port = settings.MCP_SERVER_PORT
        mcp.run(transport="streamable-http")
    else:  # pragma: no cover - guarded by validator
        raise RuntimeError(f"Unknown MCP_SERVER_MODE: {mode}")


if __name__ == "__main__":
    main()
