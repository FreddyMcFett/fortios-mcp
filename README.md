# fortios-mcp

[![CI](https://github.com/FreddyMcFett/fortios-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/FreddyMcFett/fortios-mcp/actions/workflows/ci.yml)
[![Release](https://github.com/FreddyMcFett/fortios-mcp/actions/workflows/release.yml/badge.svg)](https://github.com/FreddyMcFett/fortios-mcp/actions/workflows/release.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

A [Model Context Protocol](https://modelcontextprotocol.io) server that
lets an LLM drive a **FortiGate** via its FortiOS REST API v2. It covers
the operator workflows you'd otherwise perform through the GUI or CLI:

- **Configuration** — firewall policies, addresses, services, VIPs,
  interfaces, routing, VPN, security profiles, users.
- **Troubleshooting** — ping, traceroute, packet capture, session
  inspection, routing-table and ARP checks.
- **Monitoring** — live counters, sessions, SD-WAN health, licenses,
  FortiGuard status, Wi-Fi clients, DHCP leases.
- **Review** — bulk reads, log searches, backup export, HA checksum
  comparison.

Safe by default: every mutating operation is blocked unless
`FORTIOS_ENABLE_WRITES=true`.

> FortiOS 7.6.6 API surface is bundled as 81 Swagger JSON files under
> [`api-docs/`](api-docs/) and exposed via the built-in **schema
> discovery tools** so an LLM can dynamically find any endpoint that
> doesn't already have a curated wrapper.

---

## Architecture

![fortios-mcp architecture](docs/architecture.svg)

One server instance talks to one FortiGate. The MCP client speaks the
Model Context Protocol over stdio or streamable HTTP; the server
translates tool calls into authenticated REST requests against
`/api/v2/cmdb`, `/monitor`, `/log`, and `/service`. See
[`docs/installation.md`](docs/installation.md) for the full deployment
guide.

---

## Quick start

> Want the detailed walkthrough — prerequisites, token creation,
> Docker / systemd, TLS hardening, VDOMs, troubleshooting, and
> upgrades? Jump to
> **[`docs/installation.md`](docs/installation.md)**.

### 1. Create a REST API admin + token on the FortiGate

```cli
config system accprofile
    edit "mcp_readonly"
        set scope global
        set sysgrp read
        set fwgrp read
        set netgrp read
        set vpngrp read
        set utmgrp read
    next
end

config system api-user
    edit "mcp"
        set accprofile "mcp_readonly"
        set trusthost1 <your-workstation-ip>/32
    next
end
execute api-user generate-key mcp
```

Copy the generated token.

### 2. Install and run (uv)

```bash
uv venv
uv pip install -e .
FORTIOS_HOST=fgt.example.com \
FORTIOS_API_TOKEN=xxxxxxxxxxxx \
  uv run fortios-mcp
```

### 3. Or run via Docker

```bash
cp .env.example .env        # edit credentials
chmod 600 .env
docker compose up -d
# MCP streamable HTTP endpoint → http://localhost:8002/
```

### 4. Hook it up to Claude Desktop

`claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "fortios": {
      "command": "uv",
      "args": ["run", "fortios-mcp"],
      "env": {
        "FORTIOS_HOST": "fgt.example.com",
        "FORTIOS_API_TOKEN": "xxxxxxxxxxxx",
        "FORTIOS_VERIFY_SSL": "false"
      }
    }
  }
}
```

---

## Configuration

All settings come from environment variables (or a `.env` file):

| Variable | Default | Purpose |
|----------|---------|---------|
| `FORTIOS_HOST` | *required* | FortiGate hostname / IP |
| `FORTIOS_PORT` | `443` | HTTPS port |
| `FORTIOS_API_TOKEN` | *required* | REST API admin token |
| `FORTIOS_VERIFY_SSL` | `true` | Set `false` for self-signed certs |
| `FORTIOS_TIMEOUT` | `30` | Per-request timeout (seconds) |
| `FORTIOS_MAX_RETRIES` | `3` | Retries on 429 / 5xx / network error |
| `FORTIOS_DEFAULT_VDOM` | `root` | VDOM used when a tool call omits one |
| `FORTIOS_ENABLE_WRITES` | `false` | **Must be `true` for any mutating tool** |
| `FORTIOS_TOOL_MODE` | `full` | `full` registers everything, `dynamic` registers only discovery tools |
| `MCP_SERVER_MODE` | `auto` | `auto` / `stdio` / `http` |
| `MCP_SERVER_HOST` | `0.0.0.0` | HTTP bind |
| `MCP_SERVER_PORT` | `8002` | HTTP port |
| `MCP_AUTH_TOKEN` | — | Bearer token required in HTTP mode |
| `LOG_LEVEL` | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |

See [`.env.example`](.env.example) for the full template.

---

## Tool catalog

### Generic primitives (8) — cover the full API
`cmdb_get`, `cmdb_set*`, `cmdb_add*`, `cmdb_update*`, `cmdb_delete*`,
`monitor_get`, `log_search`, `service_execute*`

### Schema discovery (4) — browse the bundled Swagger
`list_api_categories`, `list_endpoints`, `describe_endpoint`,
`search_endpoints`

### Curated — System (14)
`get_system_status`, `get_system_performance`, `get_system_global`,
`list_interfaces`, `get_interface`, `get_interface_status`,
`set_interface*`, `list_admins`, `get_ha_status`, `get_ha_checksum`,
`get_firmware_info`, `backup_config`, `reboot_device*`, `shutdown_device*`

### Curated — Firewall (12)
`list_firewall_policies`, `get_firewall_policy`, `add_firewall_policy*`,
`update_firewall_policy*`, `delete_firewall_policy*`,
`move_firewall_policy*`, `list_firewall_addresses`,
`list_firewall_address_groups`, `list_firewall_services`,
`list_firewall_vips`, `list_firewall_ippools`

### Curated — Routing (8)
`list_static_routes`, `add_static_route*`, `delete_static_route*`,
`get_routing_table`, `get_bgp_neighbors`, `get_ospf_neighbors`,
`get_policy_routes`, `get_arp_table`

### Curated — VPN (7)
`list_ipsec_phase1`, `list_ipsec_phase2`, `get_ipsec_tunnel_status`,
`bring_up_ipsec_tunnel*`, `bring_down_ipsec_tunnel*`,
`list_ssl_vpn_sessions`, `get_ssl_vpn_settings`

### Curated — Users & auth (6)
`list_local_users`, `list_user_groups`, `list_ldap_servers`,
`list_radius_servers`, `list_fsso_agents`,
`list_firewall_auth_sessions`

### Curated — Security profiles (8)
`list_antivirus_profiles`, `list_ips_sensors`,
`list_web_filter_profiles`, `list_dns_filter_profiles`,
`list_application_control_lists`, `list_dlp_profiles`,
`list_ssl_inspection_profiles`, `list_profile_groups`

### Curated — Monitoring (10)
`list_sessions`, `kill_session*`, `get_top_sources`,
`get_top_destinations`, `get_bandwidth_by_interface`,
`get_license_status`, `get_fortiguard_status`, `get_sdwan_health`,
`list_wifi_clients`, `list_dhcp_leases`

### Curated — Logs (5)
`log_search_disk`, `log_search_memory`, `log_search_fortianalyzer`,
`log_search_forticloud`, `log_download`

### Curated — Diagnostics (6)
`list_packet_captures`, `start_packet_capture*`,
`stop_packet_capture*`, `download_packet_capture`, `ping`, `traceroute`

`*` = write-guarded (requires `FORTIOS_ENABLE_WRITES=true`).

**Total: ~88 tools.** Everything not listed above is still reachable via
the generic primitives combined with `describe_endpoint`.

---

## How write-guarding works

1. Every mutating tool is decorated with `@require_writes`.
2. When `FORTIOS_ENABLE_WRITES=false`, the decorator short-circuits the
   call and returns `{"status": "error", "message": "..."}`.
3. `tests/test_write_guard.py` fails if anyone adds a mutating tool
   without the guard.

Turn writes on per session (stdio) or per container (HTTP) —
never leave it on globally.

---

## Development

```bash
uv venv
uv pip install -e ".[dev]"
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
uv run mypy src/
uv run pytest
```

Integration tests against a real FortiGate:

```bash
FORTIOS_HOST=... FORTIOS_API_TOKEN=... \
  uv run pytest -m integration tests/integration
```

See [`CLAUDE.md`](CLAUDE.md) for the contributor handbook and
[`CONTRIBUTING.md`](CONTRIBUTING.md) for commit conventions.

Every feature change must ship with matching doc updates — see
[`CLAUDE.md` §10a](CLAUDE.md#10a-documentation-requirement-for-feature-changes).

---

## Documentation map

| Doc | What's in it |
|-----|--------------|
| [`docs/installation.md`](docs/installation.md) | Prerequisites, token creation, all deployment modes (uv / pipx / Docker / systemd), MCP client wiring, usage recipes, TLS hardening, troubleshooting, upgrades |
| [`docs/architecture.svg`](docs/architecture.svg) | High-level architecture diagram |
| [`CLAUDE.md`](CLAUDE.md) | Project handbook — architecture, coding standards, tool taxonomy, release flow, security posture |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Pre-PR checklist and commit conventions |
| [`SECURITY.md`](SECURITY.md) | Private-disclosure process for security issues |
| [`CHANGELOG.md`](CHANGELOG.md) | Auto-generated release notes — do not edit by hand |

---

## Versioning & release

Fully automated via
[python-semantic-release](https://python-semantic-release.readthedocs.io/):

- Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/).
- Every push to `main` runs `.github/workflows/release.yml`, which
  bumps the version, updates `CHANGELOG.md`, tags, and drafts a GitHub
  release.
- Tags matching `v*` trigger `.github/workflows/docker-publish.yml`
  and push a multi-arch image to
  `ghcr.io/freddymcfett/fortios-mcp`.

Never edit `CHANGELOG.md` or bump `pyproject.toml` manually.

---

## License

[MIT](LICENSE) © FreddyMcFett
