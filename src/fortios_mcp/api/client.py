"""Async HTTP client for the FortiOS REST API v2.

FortiOS exposes four API surfaces under ``/api/v2``:

- ``cmdb``     — configuration objects (CRUD)
- ``monitor``  — live status & statistics (GET, some POST)
- ``log``      — log search and retrieval
- ``service``  — one-off operations (security rating, sniffer, system)

Authentication is via ``Authorization: Bearer <token>``. The client unwraps
the FortiOS response envelope (``{"http_status": ..., "results": [...]}``)
and raises the appropriate :class:`~fortios_mcp.utils.errors.FortiOSError`
subclass on failure.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from fortios_mcp.utils.config import Settings
from fortios_mcp.utils.errors import (
    AuthenticationError,
    ConnectionFailed,
    FortiOSError,
    RateLimitError,
    ServerError,
    parse_http_error,
)
from fortios_mcp.utils.validation import sanitize_for_logging

logger = logging.getLogger(__name__)

_API_BASE = "/api/v2"


class FortiOSClient:
    """Minimal async wrapper around the FortiOS REST API."""

    def __init__(
        self,
        host: str,
        api_token: str,
        *,
        port: int = 443,
        verify_ssl: bool = True,
        timeout: int = 30,
        max_retries: int = 3,
        default_vdom: str = "root",
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        if not host:
            raise ValueError("host is required")
        if not api_token:
            raise ValueError("api_token is required")
        self.host = host.replace("https://", "").replace("http://", "").rstrip("/")
        self.port = port
        self.api_token = api_token
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.max_retries = max_retries
        self.default_vdom = default_vdom
        self._version: tuple[int, int, int] | None = None
        self._client = httpx.AsyncClient(
            base_url=f"https://{self.host}:{self.port}",
            headers={
                "Authorization": f"Bearer {self.api_token}",
                "Accept": "application/json",
            },
            verify=verify_ssl,
            timeout=timeout,
            transport=transport,
        )

    # Lifecycle ----------------------------------------------------------

    @classmethod
    def from_settings(
        cls,
        settings: Settings,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> FortiOSClient:
        settings.require_credentials()
        return cls(
            host=settings.FORTIOS_HOST,
            api_token=settings.FORTIOS_API_TOKEN,
            port=settings.FORTIOS_PORT,
            verify_ssl=settings.FORTIOS_VERIFY_SSL,
            timeout=settings.FORTIOS_TIMEOUT,
            max_retries=settings.FORTIOS_MAX_RETRIES,
            default_vdom=settings.FORTIOS_DEFAULT_VDOM,
            transport=transport,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> FortiOSClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    # Introspection ------------------------------------------------------

    @property
    def version(self) -> tuple[int, int, int] | None:
        """Detected FortiOS version, or None before the first call."""
        return self._version

    async def probe(self) -> dict[str, Any]:
        """GET /monitor/system/status — verify auth and cache version."""
        data = await self.monitor_get("system/status")
        self._cache_version(data)
        return data

    def _cache_version(self, status: Any) -> None:
        results = status.get("results") if isinstance(status, dict) else None
        candidate = results if isinstance(results, dict) else status
        if not isinstance(candidate, dict):
            return
        version = candidate.get("version") or candidate.get("Version")
        if not isinstance(version, str):
            return
        cleaned = version.lstrip("v").split("-")[0].split()[0]
        parts = cleaned.split(".")
        try:
            self._version = (
                int(parts[0]) if len(parts) > 0 else 7,
                int(parts[1]) if len(parts) > 1 else 0,
                int(parts[2]) if len(parts) > 2 else 0,
            )
            logger.info("Detected FortiOS version %s", self._version)
        except ValueError:
            logger.debug("Could not parse FortiOS version from %r", version)

    # CMDB (configuration) ----------------------------------------------

    async def cmdb_get(
        self,
        path: str,
        *,
        vdom: str | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        return await self._request("GET", "cmdb", path, vdom=vdom, params=params)

    async def cmdb_set(
        self,
        path: str,
        body: dict[str, Any],
        *,
        vdom: str | None = None,
    ) -> Any:
        return await self._request("PUT", "cmdb", path, vdom=vdom, json=body)

    async def cmdb_add(
        self,
        path: str,
        body: dict[str, Any],
        *,
        vdom: str | None = None,
    ) -> Any:
        return await self._request("POST", "cmdb", path, vdom=vdom, json=body)

    async def cmdb_update(
        self,
        path: str,
        body: dict[str, Any],
        *,
        vdom: str | None = None,
    ) -> Any:
        return await self._request("PUT", "cmdb", path, vdom=vdom, json=body)

    async def cmdb_delete(self, path: str, *, vdom: str | None = None) -> Any:
        return await self._request("DELETE", "cmdb", path, vdom=vdom)

    # Monitor / Log / Service -------------------------------------------

    async def monitor_get(
        self,
        path: str,
        *,
        vdom: str | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        return await self._request("GET", "monitor", path, vdom=vdom, params=params)

    async def monitor_post(
        self,
        path: str,
        body: dict[str, Any] | None = None,
        *,
        vdom: str | None = None,
    ) -> Any:
        return await self._request("POST", "monitor", path, vdom=vdom, json=body or {})

    async def log_get(
        self,
        path: str,
        *,
        vdom: str | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        return await self._request("GET", "log", path, vdom=vdom, params=params)

    async def service_execute(
        self,
        path: str,
        body: dict[str, Any] | None = None,
        *,
        vdom: str | None = None,
    ) -> Any:
        return await self._request("POST", "service", path, vdom=vdom, json=body or {})

    # Core request -------------------------------------------------------

    async def _request(
        self,
        method: str,
        api: str,
        path: str,
        *,
        vdom: str | None = None,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{_API_BASE}/{api}/{path.lstrip('/')}"
        query: dict[str, Any] = dict(params or {})
        effective_vdom = vdom if vdom is not None else self.default_vdom
        if effective_vdom:
            query.setdefault("vdom", effective_vdom)

        attempt = 0
        last_exc: Exception | None = None
        while attempt <= self.max_retries:
            attempt += 1
            try:
                logger.debug(
                    "FortiOS %s %s params=%s body=%s (attempt %d)",
                    method,
                    url,
                    sanitize_for_logging(query),
                    sanitize_for_logging(json),
                    attempt,
                )
                response = await self._client.request(method, url, params=query, json=json)
            except httpx.HTTPError as exc:
                last_exc = exc
                if attempt > self.max_retries:
                    raise ConnectionFailed(
                        f"Network error after {attempt} attempts: {exc}",
                        operation=f"{method} {url}",
                    ) from exc
                await self._backoff(attempt)
                continue

            if response.status_code < 400:
                return self._parse_success(response, method, url)

            parsed = self._parse_failure(response, method, url)
            if isinstance(parsed, RateLimitError | ServerError) and attempt <= self.max_retries:
                logger.warning(
                    "Transient FortiOS error %s on %s %s (attempt %d): %s",
                    response.status_code,
                    method,
                    url,
                    attempt,
                    parsed,
                )
                await self._backoff(attempt)
                continue
            raise parsed

        if last_exc is not None:
            raise ConnectionFailed(str(last_exc), operation=f"{method} {url}") from last_exc
        raise FortiOSError("Request failed after retries", operation=f"{method} {url}")

    @staticmethod
    async def _backoff(attempt: int) -> None:
        await asyncio.sleep(min(2 ** (attempt - 1), 16))

    @staticmethod
    def _parse_success(response: httpx.Response, method: str, url: str) -> Any:
        if not response.content:
            return {"status": "success"}
        try:
            payload = response.json()
        except ValueError as exc:
            raise FortiOSError(
                f"Invalid JSON in response: {exc}",
                status_code=response.status_code,
                operation=f"{method} {url}",
            ) from exc
        if isinstance(payload, dict) and "http_status" in payload:
            code = payload.get("http_status")
            if isinstance(code, int) and code >= 400:
                message = payload.get("cli_error") or payload.get("error") or str(payload)
                raise parse_http_error(code, str(message), f"{method} {url}", payload)
        return payload

    @staticmethod
    def _parse_failure(response: httpx.Response, method: str, url: str) -> FortiOSError:
        try:
            payload = response.json()
        except ValueError:
            payload = None
        message: Any
        if isinstance(payload, dict):
            message = (
                payload.get("cli_error")
                or payload.get("error")
                or payload.get("message")
                or payload
            )
        else:
            message = response.text or f"HTTP {response.status_code}"
        if response.status_code in (401, 403):
            return AuthenticationError(
                f"FortiGate rejected the API token ({response.status_code}): {message}",
                status_code=response.status_code,
                operation=f"{method} {url}",
                payload=payload,
            )
        return parse_http_error(response.status_code, str(message), f"{method} {url}", payload)
