# CLAUDE.md — Project Handbook

This document is the single source of truth for anyone (human or
LLM) extending `fortios-mcp`. Every contribution must conform to
the rules below; CI and review will reject PRs that deviate.

---

## 1. What this project is

`fortios-mcp` is a Model Context Protocol server that drives a FortiGate
through its FortiOS REST API v2. It targets four workflows:

1. **Configuration** — create / update / remove CMDB objects
   (firewall policies, addresses, services, interfaces, VPNs, users,
   security profiles, etc.).
2. **Troubleshooting** — ping, traceroute, packet capture, session
   inspection, interface and routing-table diagnostics.
3. **Monitoring** — live counters, session tables, SD-WAN health,
   license status, FortiGuard subscription state, Wi-Fi clients, DHCP
   leases.
4. **Review** — bulk read of policies and objects, log searches,
   backup export, HA checksum comparison.

It is a **single-target** server: one instance talks to one FortiGate.
Run multiple instances for multiple FortiGates.

---

## 2. Architecture

```
┌──────────────────┐      stdio / HTTP        ┌────────────────────────┐
│ MCP client       │ ◀──────────────────────▶ │ FortiOS MCP server     │
│ (Claude, etc.)   │                          │ (FastMCP, this repo)   │
└──────────────────┘                          │                        │
                                              │  FortiOSClient (httpx) │
                                              └──────────┬─────────────┘
                                                         │  HTTPS
                                                         ▼
                                               ┌─────────────────────┐
                                               │ FortiGate           │
                                               │  /api/v2/cmdb       │
                                               │  /api/v2/monitor    │
                                               │  /api/v2/log        │
                                               │  /api/v2/service    │
                                               └─────────────────────┘
```

- **FastMCP** (`mcp.server.fastmcp.FastMCP`) hosts the tool surface and
  handles stdio + streamable-HTTP transport.
- **`FortiOSClient`** is a thin async wrapper around `httpx.AsyncClient`
  that bears the `Authorization: Bearer <token>` header, unwraps the
  FortiOS response envelope (`{"http_status", "results", "vdom", ...}`)
  and raises typed exceptions from `utils/errors.py`.
- **`SwaggerIndex`** lazy-parses the 81 bundled api-docs files so the
  LLM can self-discover endpoints that don't have a curated wrapper.

---

## 3. Directory tour

| Path | Purpose |
|------|---------|
| `api-docs/` | 81 FortiOS 7.6.6 Swagger 2.0 definitions, shipped as package data |
| `src/fortios_mcp/server.py` | FastMCP bootstrap, lifespan, transport selection |
| `src/fortios_mcp/api/client.py` | FortiOSClient — the only place that talks HTTP to FortiOS |
| `src/fortios_mcp/tools/__init__.py` | Registration helper and the `@require_writes` decorator |
| `src/fortios_mcp/tools/generic_tools.py` | 8 generic REST primitives |
| `src/fortios_mcp/tools/schema_tools.py` | 4 discovery tools over the Swagger index |
| `src/fortios_mcp/tools/*_tools.py` | Curated workflow tools per feature area |
| `src/fortios_mcp/utils/swagger.py` | `SwaggerIndex` — parses api-docs lazily |
| `src/fortios_mcp/utils/config.py` | Pydantic settings + logging config |
| `src/fortios_mcp/utils/errors.py` | Exception hierarchy and HTTP-code parser |
| `src/fortios_mcp/utils/validation.py` | `sanitize_for_logging`, path / VDOM validation |
| `tests/` | Unit tests (hermetic, `httpx.MockTransport`) |
| `tests/integration/` | Integration tests against a real FortiGate |
| `.github/workflows/` | CI, release, docker publish |

---

## 4. Tool taxonomy (hybrid)

The tool surface is deliberately layered:

1. **Generic primitives** (`generic_tools.py`) — 8 tools that cover every
   FortiOS endpoint (`cmdb_get/set/add/update/delete`, `monitor_get`,
   `log_search`, `service_execute`). These are the *escape hatch*.
2. **Schema discovery** (`schema_tools.py`) — 4 tools that query
   `SwaggerIndex`: `list_api_categories`, `list_endpoints`,
   `describe_endpoint`, `search_endpoints`. The LLM uses these to find
   the right path and parameters when a curated tool doesn't exist.
3. **Curated tools** — ~60 ergonomic wrappers for the operator's most
   common workflows (firewall policies, interfaces, routing, VPN
   tunnels, sessions, Wi-Fi clients, ping, traceroute, etc.). They must
   call through `FortiOSClient` — never build HTTP requests themselves.

**Invariant:** Every tool that performs a state-changing operation (CMDB
write, `service` exec, reboot, tunnel toggle, session kill, packet
capture start/stop) MUST be decorated with `@require_writes`. Reviewers
reject PRs that bypass this.

---

## 5. Coding standards

- **Python**: 3.12+. Use modern syntax (`X | Y`, `match`, PEP 695 if
  needed).
- **Typing**: every function is typed; `mypy --strict` must pass.
- **Formatting / linting**: `ruff check` and `ruff format` must pass
  (line length 100, target py312). Import sorting via `ruff`'s `I`
  rules.
- **Docstrings**: Google style, one-paragraph summary, then `Args:`
  and `Returns:` sections. MCP clients surface these to the model, so
  they must describe FortiOS semantics (VDOMs, access groups, schemas).
- **No broad `except Exception`** in tool code; catch `FortiOSError`
  (plus `ValueError` for local validation) and return the `err(...)`
  envelope.
- **Secrets**: never log tokens, passwords, PSKs — always pass
  untrusted dicts through `sanitize_for_logging()` first.

---

## 6. Testing rules

- **Unit tests** (`tests/`) are hermetic. Use the `tool_client`
  fixture, which wires a `FortiOSClient` to an `httpx.MockTransport`.
- **Every curated tool gets at least one happy-path test**; every write
  tool is listed in `EXPECTED_WRITE_TOOLS` in
  `tests/test_write_guard.py` to guarantee guard coverage.
- **Swagger index**: `tests/test_swagger.py` asserts every bundled
  api-docs file parses and that representative endpoints are
  discoverable.
- **Integration tests** live under `tests/integration/`, marked
  `@pytest.mark.integration`, and are skipped in CI. Run them
  manually against a lab FortiGate.
- `pytest -v --cov=src/fortios_mcp --cov-report=term-missing` must
  stay green and ≥ 80 % covered.

---

## 7. Commit convention — Conventional Commits

Commit messages drive automated versioning. Use:

| Prefix | Meaning | Version bump |
|--------|---------|--------------|
| `feat:` | New user-visible functionality | minor |
| `fix:` | Bug fix | patch |
| `perf:` | Performance improvement | patch |
| `refactor:` | Code change with no external effect | none |
| `docs:` | Docs only | none |
| `test:` | Test-only change | none |
| `chore:` / `ci:` / `build:` / `style:` | Misc | none |
| `feat!:` or `BREAKING CHANGE:` footer | Breaking change | **major** |

Examples:

```
feat(firewall): add move_firewall_policy tool
fix(client): raise NotFoundError on embedded http_status 404
feat!: require FORTIOS_ENABLE_WRITES for every mutating tool
```

---

## 8. Release flow (fully automated)

1. Open a PR against `main` with Conventional Commit messages.
2. CI must pass (ruff, ruff format, mypy, pytest).
3. Merge via squash-commit preserving the Conventional prefix.
4. `.github/workflows/release.yml` runs `python-semantic-release`:
   - Bumps `version` in `pyproject.toml` and `src/fortios_mcp/__init__.py`.
   - Regenerates `CHANGELOG.md` from commit history.
   - Creates a git tag `vX.Y.Z` and GitHub release.
5. The tag triggers `.github/workflows/docker-publish.yml`, which
   builds a multi-arch image and pushes
   `ghcr.io/freddymcfett/fortios-mcp:{major}`, `{major}.{minor}`,
   `{version}`, `latest`.

Never edit `CHANGELOG.md` or bump the version manually; let the
pipeline do it.

---

## 9. Write-guard rule

The default posture of the server is **read-only**. `FORTIOS_ENABLE_WRITES`
is `false` out of the box, and every mutating tool carries
`@require_writes`. This decorator sets
`fn.__fortios_requires_writes__ = True` so
`tests/test_write_guard.py` can verify the guard at import time.

When adding a mutating tool:

1. Decorate it: `@mcp.tool()` *then* `@require_writes` (order matters —
   the guard must run *inside* the MCP tool wrapper so the model sees
   a successful registration).
2. Add its name to `EXPECTED_WRITE_TOOLS` in `tests/test_write_guard.py`.
3. Document the effect in the docstring ("Write-guarded.") so the
   model knows it needs the env flag.

---

## 10. Adding a new curated tool

1. Pick the module that fits (`firewall_tools.py` for firewall, etc.).
2. Define an `async def` function, typed, with a Google-style
   docstring.
3. Call through `get_client()` — never instantiate `httpx` or a new
   `FortiOSClient`.
4. Return `ok(...)` on success and `err(exc, tool="name")` on failure.
5. Decorate with `@mcp.tool()` (and `@require_writes` if it mutates).
6. Add a unit test in the matching `tests/test_*_tools.py`.
7. Add the tool to the catalog table in `README.md`.
8. Commit with `feat(<area>): <name>` so the next release picks it up.

---

## 11. Updating for a new FortiOS release

1. Fetch the new Swagger bundle from FNDN.
2. Replace the contents of `api-docs/` (preserve file-naming
   convention `"{API_TYPE} API {category}.json"` so `SwaggerIndex`
   indexes them).
3. Run `uv run pytest tests/test_swagger.py` to confirm the parser
   still handles every file.
4. Scan the diff for new endpoint categories and add curated wrappers
   where the new feature deserves ergonomics.
5. Commit with `feat(api-docs): update to FortiOS X.Y.Z`.

---

## 12. Security posture

- Default **read-only**; mutating tools require
  `FORTIOS_ENABLE_WRITES=true`.
- TLS verification is **on** by default; disable only for self-signed
  lab devices via `FORTIOS_VERIFY_SSL=false`.
- HTTP transport (Docker) should be fronted by a TLS proxy and should
  set `MCP_AUTH_TOKEN` so the MCP endpoint itself authenticates
  callers.
- API tokens are loaded from env vars — never committed. The `.env`
  file must be `chmod 600`; `utils/config.py` warns otherwise.
- All debug logs pass through `sanitize_for_logging()` — tokens,
  passwords, PSKs and session IDs are redacted before printing.
- Conservative path validation (`utils/validation.py`) prevents path
  traversal in CMDB calls.

---

## 13. Runbook

### stdio (Claude Desktop / Code)
```bash
uv venv
uv pip install -e .
FORTIOS_HOST=fgt.example FORTIOS_API_TOKEN=... uv run fortios-mcp
```

### HTTP (Docker)
```bash
cp .env.example .env   # fill in values
chmod 600 .env
docker compose up -d
# MCP endpoint: http://localhost:8002/
```

### Add to Claude Desktop (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "fortios": {
      "command": "uv",
      "args": ["run", "fortios-mcp"],
      "env": {
        "FORTIOS_HOST": "fgt.example",
        "FORTIOS_API_TOKEN": "xxxxxxxx",
        "FORTIOS_VERIFY_SSL": "false"
      }
    }
  }
}
```

### Add to Claude Code (`.claude/mcp.json`):
```json
{
  "mcpServers": {
    "fortios": {
      "command": "uv",
      "args": ["run", "fortios-mcp"],
      "env": {
        "FORTIOS_HOST": "fgt.example",
        "FORTIOS_API_TOKEN": "xxxxxxxx"
      }
    }
  }
}
```

---

## 14. Non-goals

- **Multi-FortiGate fan-out** inside a single server instance. Spin up
  multiple instances (one per device) if needed.
- **FortiManager / FortiAnalyzer operations.** Use the sibling
  `fortianalyzer-mcp` project for FAZ.
- **Raw SSH / CLI passthrough.** Everything goes through the REST API.
