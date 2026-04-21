"""FastMCP server bootstrap for FortiOS.

The module-level ``mcp`` instance is defined up-front so tool modules can
import and decorate against it without timing hazards. :func:`build_server`
registers the tool modules; :func:`main` selects a transport and runs.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from collections.abc import AsyncIterator, Sequence
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


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fortios-mcp",
        description=(
            "FortiOS MCP server. Drives one FortiGate through its REST API v2 "
            "for configuration, troubleshooting, monitoring and review. "
            "Read-only by default; set FORTIOS_ENABLE_WRITES=true to allow "
            "mutating tools. All runtime configuration comes from environment "
            "variables — see docs/installation.md."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"fortios-mcp {__version__}",
    )
    parser.add_argument(
        "--transport",
        choices=("auto", "stdio", "http"),
        default=None,
        help=(
            "Transport to run. Overrides MCP_SERVER_MODE. "
            "'auto' picks stdio or http based on env (default via MCP_SERVER_MODE=auto)."
        ),
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help=(
            "Validate configuration (required env vars, credentials, settings) "
            "and exit without starting the server."
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point.

    Parses CLI args, validates credentials up-front, and launches the
    selected transport. Returns a POSIX-style exit code so callers that
    import :func:`main` (and the console-script shim) can propagate it.
    """
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    settings = get_settings()
    settings.configure_logging()

    try:
        settings.require_credentials()
    except RuntimeError as exc:
        parser.exit(
            2,
            f"error: {exc}\n"
            "Set them in the environment (or a .env file) before starting "
            "fortios-mcp. See docs/installation.md.\n",
        )

    build_server(settings)

    requested_mode = args.transport or settings.MCP_SERVER_MODE
    mode = _detect_mode(requested_mode)

    if args.check:
        logger.info("Configuration OK; transport=%s", mode)
        return 0

    logger.info("Launching FortiOS MCP server in %s mode", mode)
    if mode == "stdio":
        mcp.run(transport="stdio")
    elif mode == "http":
        mcp.settings.host = settings.MCP_SERVER_HOST
        mcp.settings.port = settings.MCP_SERVER_PORT
        mcp.run(transport="streamable-http")
    else:  # pragma: no cover - guarded by validator
        raise RuntimeError(f"Unknown MCP_SERVER_MODE: {mode}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
