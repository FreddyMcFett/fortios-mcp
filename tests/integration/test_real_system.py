"""Integration test that requires a reachable FortiGate.

Run manually:

    FORTIOS_HOST=... FORTIOS_API_TOKEN=... pytest -m integration tests/integration
"""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.skipif(
    not os.getenv("FORTIOS_HOST") or not os.getenv("FORTIOS_API_TOKEN"),
    reason="FORTIOS_HOST / FORTIOS_API_TOKEN not set",
)
async def test_get_system_status_real() -> None:
    from fortios_mcp.api.client import FortiOSClient
    from fortios_mcp.utils.config import Settings

    async with FortiOSClient.from_settings(Settings()) as client:
        status = await client.monitor_get("system/status")
    assert isinstance(status, dict)
