"""Validation and log sanitization tests."""

from __future__ import annotations

import pytest

from fortios_mcp.utils.validation import (
    sanitize_for_logging,
    validate_cmdb_path,
    validate_vdom,
)


def test_sanitize_redacts_nested_secrets() -> None:
    data = {
        "name": "policy1",
        "password": "hunter2",
        "nested": {"api_token": "abc", "keep": 1},
        "list": [{"secret": "s", "safe": 2}],
    }
    out = sanitize_for_logging(data)
    assert out["name"] == "policy1"
    assert out["password"] == "***REDACTED***"
    assert out["nested"]["api_token"] == "***REDACTED***"
    assert out["nested"]["keep"] == 1
    assert out["list"][0]["secret"] == "***REDACTED***"
    assert out["list"][0]["safe"] == 2


def test_validate_cmdb_path_strips_slashes() -> None:
    assert validate_cmdb_path("firewall/policy") == "firewall/policy"


def test_validate_cmdb_path_rejects_leading_slash() -> None:
    with pytest.raises(ValueError):
        validate_cmdb_path("/firewall/policy")


def test_validate_cmdb_path_rejects_traversal() -> None:
    with pytest.raises(ValueError):
        validate_cmdb_path("firewall/../system/global")


def test_validate_vdom_accepts_standard_names() -> None:
    assert validate_vdom("root") == "root"
    assert validate_vdom("vdom_01") == "vdom_01"


def test_validate_vdom_rejects_special_chars() -> None:
    with pytest.raises(ValueError):
        validate_vdom("bad/name")
