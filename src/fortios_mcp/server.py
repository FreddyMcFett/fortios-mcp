"""FastMCP server bootstrap for FortiOS.

The module-level ``mcp`` instance is defined up-front so tool modules can
import and decorate against it without timing hazards. :func:`build_server`
registers the tool modules; :func:`main` selects a transport and runs.
"""

from __future__ import annotations

import argparse
import hmac
import json
import logging
import os
import sys
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

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


def _build_transport_security(settings: Settings) -> TransportSecuritySettings | None:
    """Build MCP transport-security settings from MCP_ALLOWED_HOSTS.

    Returns ``None`` when no extra hosts are configured (localhost /
    127.0.0.1 are always allowed by the SDK regardless).
    """
    if not settings.MCP_ALLOWED_HOSTS:
        return None
    return TransportSecuritySettings(allowed_hosts=settings.MCP_ALLOWED_HOSTS)


_boot_settings = get_settings()

mcp: FastMCP = FastMCP(
    "FortiOS MCP Server",
    instructions=(
        "Drives a FortiGate via its REST API v2 for configuration, "
        "troubleshooting, monitoring and review. Read-only by default; "
        "set FORTIOS_ENABLE_WRITES=true to allow mutating tools."
    ),
    stateless_http=True,
    lifespan=_lifespan,
    transport_security=_build_transport_security(_boot_settings),
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


def _run_http(settings: Settings) -> None:
    """Serve the MCP streamable-HTTP app via uvicorn, with /health and optional auth."""
    import uvicorn
    from starlette.applications import Starlette
    from starlette.middleware import Middleware
    from starlette.requests import Request
    from starlette.responses import JSONResponse, Response
    from starlette.routing import Mount, Route
    from starlette.types import ASGIApp, Receive, Scope, Send

    class AuthMiddleware:
        """ASGI middleware: require ``Authorization: Bearer <MCP_AUTH_TOKEN>`` on non-/health paths."""

        def __init__(self, app: ASGIApp) -> None:
            self.app = app

        async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
            if scope["type"] != "http":
                await self.app(scope, receive, send)
                return
            token = settings.MCP_AUTH_TOKEN
            if not token:
                await self.app(scope, receive, send)
                return
            if scope.get("path", "") == "/health":
                await self.app(scope, receive, send)
                return
            headers = dict(scope.get("headers", []))
            auth_value = headers.get(b"authorization", b"").decode()
            expected = f"Bearer {token}"
            if not hmac.compare_digest(auth_value, expected):
                response = Response(
                    content=json.dumps(
                        {"error": "Unauthorized", "detail": "Invalid or missing Bearer token"}
                    ),
                    status_code=401,
                    media_type="application/json",
                )
                await response(scope, receive, send)
                return
            await self.app(scope, receive, send)

    async def health_endpoint(_request: Request) -> JSONResponse:
        from fortios_mcp import tools as tools_mod

        client = tools_mod._client
        connected = client is not None and client.version is not None
        return JSONResponse(
            {
                "status": "healthy",
                "service": "fortios-mcp",
                "version": __version__,
                "fortigate_connected": connected,
            }
        )

    @asynccontextmanager
    async def _app_lifespan(_app: Starlette) -> AsyncIterator[None]:
        # Set up the FortiOSClient once for the life of the process, so every
        # streamable-HTTP session reuses it instead of reconnecting per request.
        from fortios_mcp.tools import set_client

        client = FortiOSClient.from_settings(settings)
        set_client(client)
        try:
            try:
                await client.probe()
            except Exception as exc:  # pragma: no cover - network probe
                logger.warning(
                    "Initial FortiGate probe failed (%s); tools will surface "
                    "the error on first call.",
                    exc,
                )
            async with mcp.session_manager.run():
                yield
        finally:
            set_client(None)
            await client.close()

    app = Starlette(
        routes=[
            Route("/health", health_endpoint, methods=["GET"]),
            Mount("/", app=mcp.streamable_http_app()),
        ],
        lifespan=_app_lifespan,
        middleware=[Middleware(AuthMiddleware)],
    )

    uvicorn.run(
        app,
        host=settings.MCP_SERVER_HOST,
        port=settings.MCP_SERVER_PORT,
        log_level=settings.LOG_LEVEL.lower(),
    )


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
    try:
        if mode == "stdio":
            mcp.run(transport="stdio")
        elif mode == "http":
            _run_http(settings)
        else:  # pragma: no cover - guarded by validator
            raise RuntimeError(f"Unknown MCP_SERVER_MODE: {mode}")
    except KeyboardInterrupt:
        # anyio re-raises KeyboardInterrupt out of the event loop on SIGINT;
        # swallow it here so Ctrl+C yields a clean exit instead of a traceback.
        logger.info("Interrupted by user; exiting")
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
