"""Verify the Swagger index parses every bundled api-docs file."""

from __future__ import annotations

from fortios_mcp.utils.swagger import API_TYPES, SwaggerIndex, get_swagger_index


def test_all_api_types_present() -> None:
    index = get_swagger_index()
    found = set(index.api_types())
    for t in API_TYPES:
        assert t in found, f"Missing api-docs files for {t}"


def test_file_count_matches_expected() -> None:
    index = SwaggerIndex()
    assert index.file_count() >= 80, "Expected at least 80 Swagger files"


def test_firewall_file_has_policy_endpoint() -> None:
    index = get_swagger_index()
    endpoints = index.endpoints("Configuration", "firewall")
    paths = {(e["method"], e["path"]) for e in endpoints}
    assert any("policy" in p.lower() for _, p in paths), "No firewall/policy endpoint indexed"


def test_monitor_system_status_describable() -> None:
    index = get_swagger_index()
    eps = index.endpoints("Monitor", "system")
    status = next((e for e in eps if e["path"].endswith("/status")), None)
    assert status is not None, "Monitor API system must expose /status"
    described = index.describe("Monitor", "system", status["path"], status["method"])
    assert described["method"] == status["method"]


def test_search_finds_policy_endpoints() -> None:
    index = get_swagger_index()
    hits = index.search("policy", limit=10)
    assert hits, "Search for 'policy' should return results"
    assert all("policy" in h["path"].lower() or "policy" in h["summary"].lower() for h in hits)
