# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and releases adhere to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Entries below the Unreleased section are produced automatically by
[python-semantic-release](https://python-semantic-release.readthedocs.io/)
from [Conventional Commit](https://www.conventionalcommits.org/) messages on
the `main` branch.

## [Unreleased]

## [0.1.0] - 2026-04-18

### Features

- Initial FortiOS MCP server release.
- FastMCP-based server with stdio + HTTP transports and auto-detection.
- FortiOSClient: async httpx client for FortiOS REST API v2 (cmdb, monitor,
  log, service) with token authentication, retries, and TLS verification.
- Hybrid tool surface: 8 generic CRUD primitives, 4 Swagger-backed schema
  discovery tools, and ~60 curated workflow tools across system, firewall,
  routing, VPN, user, security profile, monitor, log, and diagnostic
  categories.
- Read-only by default: `FORTIOS_ENABLE_WRITES=true` required for any
  mutating operation.
- 81 bundled FortiOS 7.6.6 Swagger definitions shipped as package data
  and indexed lazily by the schema tools.
- Dockerfile (multi-stage), docker-compose, GitHub Actions CI +
  python-semantic-release + GHCR publish pipeline.
