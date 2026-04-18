"""Configuration validation tests."""

from __future__ import annotations

import pytest

from fortios_mcp.utils.config import Settings


def test_defaults_are_safe() -> None:
    s = Settings()
    assert s.FORTIOS_ENABLE_WRITES is False
    assert s.FORTIOS_VERIFY_SSL is True
    assert s.MCP_SERVER_MODE == "auto"


def test_require_credentials_raises_when_missing() -> None:
    s = Settings(FORTIOS_HOST="", FORTIOS_API_TOKEN="")
    with pytest.raises(RuntimeError) as exc:
        s.require_credentials()
    assert "FORTIOS_HOST" in str(exc.value)
    assert "FORTIOS_API_TOKEN" in str(exc.value)


def test_log_level_normalised_to_upper() -> None:
    s = Settings(LOG_LEVEL="debug")
    assert s.LOG_LEVEL == "DEBUG"


def test_invalid_mode_rejected() -> None:
    with pytest.raises(ValueError):
        Settings(MCP_SERVER_MODE="carrier-pigeon")


def test_allowed_hosts_split_from_csv() -> None:
    s = Settings(MCP_ALLOWED_HOSTS="a.example, b.example ,c.example")
    assert s.MCP_ALLOWED_HOSTS == ["a.example", "b.example", "c.example"]
