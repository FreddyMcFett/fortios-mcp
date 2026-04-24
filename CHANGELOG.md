# CHANGELOG


## v0.3.0 (2026-04-24)

### Documentation

- Clarify that Claude Desktop HTTP connector requires https
  ([`fe1f8c9`](https://github.com/FreddyMcFett/fortios-mcp/commit/fe1f8c9d865e4a0ce3edbe47007b804775b31446))

Claude Desktop's and Claude Code's custom-connector UI rejects plain http:// URLs, so the
  http://localhost:8002/ endpoint documented in the Docker quick-start is usable only from direct
  HTTP clients (LangGraph, curl, custom SDKs). Document that users must front the container with a
  TLS terminator (Caddy / Nginx / Tailscale Funnel / Cloudflare Tunnel) and point Claude Desktop at
  the resulting https:// URL, and add a new "Connecting Claude Desktop to the HTTP endpoint"
  subsection showing two concrete paths.

- Consolidate installation guide into README and simplify install paths
  ([`f2269c0`](https://github.com/FreddyMcFett/fortios-mcp/commit/f2269c01a67956a10df8e52ec62e2ca8bc34a07c))

- Merge docs/installation.md content into README.md so the README is self-contained - Reduce
  install/update/uninstall to the recommended uv flow only - Drop pipx, Docker, systemd alternative
  install paths from the user- facing instructions to keep onboarding focused

- Remove docs/installation.md (content folded into README)
  ([`18d5586`](https://github.com/FreddyMcFett/fortios-mcp/commit/18d5586dfe9d347cc10e20deff29334b01706b99))

### Features

- Align install docs and Docker surface with fortianalyzer-mcp; fix HTTP auth + policy move
  ([`3cf4826`](https://github.com/FreddyMcFett/fortios-mcp/commit/3cf4826463f6814c5877b7d20a40ef7bc5b585bf))

Installation docs now match the fortianalyzer-mcp experience end to end:

- Restore docs/installation.md (referenced from server.py and CLAUDE.md §10a but missing on disk)
  with prerequisites, client setup for Claude Desktop / Claude Code / Perplexity, a Docker / HTTP
  section, a reverse-proxy deployment section, and a troubleshooting table. - Add docs/UPDATING.md
  describing the workflow for bumping to a new FortiOS release. - Add .dockerignore mirroring
  fortianalyzer-mcp. - docker-compose.yml: add healthcheck hitting /health, resource limits, a
  dedicated network, and forward every env var through the compose environment block. - Dockerfile
  healthcheck now targets /health instead of /. - .env.example reorganised into labelled sections
  matching fortianalyzer-mcp. - README.md: add Docker / HTTP Deployment, Production Deployment
  (reverse proxy), MCP_* env-var rows, new troubleshooting rows, and pointers to
  docs/installation.md and docs/UPDATING.md.

Bug fixes that make the documented install actually work:

- fix(server): wire up MCP_AUTH_TOKEN and MCP_ALLOWED_HOSTS. Both were declared in Settings and
  advertised in README/.env.example but the HTTP transport never enforced them. HTTP mode now runs
  via a Starlette app that mounts the MCP streamable-HTTP app, adds a constant-time Bearer-token
  middleware (when MCP_AUTH_TOKEN is set), and passes TransportSecuritySettings(allowed_hosts=...)
  to FastMCP so deployments behind Traefik/nginx aren't rejected by the SDK's DNS-rebinding check. -
  fix(server): add a real /health endpoint returning {status, service, version, fortigate_connected}
  so Docker/compose healthchecks and reverse proxies can probe the server. - fix(firewall):
  move_firewall_policy now issues PUT /api/v2/cmdb/firewall/policy/<id>?action=move&before=<id> (or
  &after=<id>) with no body, which is what FortiOS actually expects. The previous implementation
  sent the target as a JSON body and silently failed against real hardware. Extends cmdb_update on
  the client to accept optional query params; adds a regression test that asserts the exact wire
  form.


## v0.2.1 (2026-04-21)

### Bug Fixes

- **cli**: Exit cleanly on SIGINT instead of leaking a traceback
  ([`29f6bf0`](https://github.com/FreddyMcFett/fortios-mcp/commit/29f6bf0c19ef56eb44ecab416df209d883d25093))

anyio re-raises KeyboardInterrupt out of the event loop when Ctrl+C hits the stdio/HTTP run, so the
  shutdown message was followed by an anyio.WouldBlock -> asyncio.CancelledError ->
  KeyboardInterrupt chain. Catch KeyboardInterrupt around mcp.run() in main() and return 130 so the
  operator sees a single "Interrupted by user; exiting" log line.


## v0.2.0 (2026-04-21)

### Features

- **cli**: Add --help/--version/--check flags and fail fast on missing creds
  ([`33b2cba`](https://github.com/FreddyMcFett/fortios-mcp/commit/33b2cbaa0b776ada396beb691c79524eb785d12c))

`uv run fortios-mcp --help` (the sanity check in docs/installation.md) used to be silently ignored —
  main() took no arguments, so the server started, connected through _lifespan, and only then raised
  `RuntimeError: Missing required environment variables ...` buried inside an anyio ExceptionGroup
  traceback.

Parse argv with argparse and validate credentials in main() before building the transport. Missing
  env vars now exit 2 with a short stderr message that points at docs/installation.md, and --help /
  --version / --check work as advertised. --check dry-runs the configuration without starting the
  server.


## v0.1.2 (2026-04-18)

### Bug Fixes

- **ci**: Resolve mypy and test failures, pin support to FortiOS 7.6.6
  ([`8a0a5ac`](https://github.com/FreddyMcFett/fortios-mcp/commit/8a0a5ac372431b4a55fa4d71d382efcb85784af7))

- client.probe: cast monitor_get result to dict to satisfy warn_return_any. - client: add
  SUPPORTED_FORTIOS_VERSION constant (7.6.6) and log a warning on first probe when the FortiGate
  reports a different version. - tests/test_client: avoid duplicate max_retries kwarg so 429-retry
  test can pass through overrides cleanly. - tests/test_config: isolate test_defaults_are_safe from
  the session-wide env vars set by the bootstrap fixture (and by CI), otherwise
  FORTIOS_VERIFY_SSL=false leaks into Settings() defaults. - docs: state explicitly that FortiOS
  7.6.6 is the only supported version in README and docs/installation.md.

### Documentation

- **installation**: Add download section and fast-upgrade one-liners
  ([`569780d`](https://github.com/FreddyMcFett/fortios-mcp/commit/569780d09cf2475bad6aa701a6ced502ea3d2da2))

Adds a dedicated Downloading section that chooses between git clone, release tarball, GHCR image,
  and pipx/uv tool installs. Expands the Upgrading section with one-liner shortcuts per install
  path, version pinning guidance, and a rollback recipe.


## v0.1.1 (2026-04-18)

### Bug Fixes

- **lint**: Resolve ruff violations flagged by CI
  ([`8f196cf`](https://github.com/FreddyMcFett/fortios-mcp/commit/8f196cf2b2aa70d04f481ffca6ba9d8dd4b40cf1))

CI failed on the ruff lint step. This fixes all 16 violations:

- SIM105: use contextlib.suppress for PackageNotFoundError in __init__. - UP037 (x2): drop quoted
  self-type annotations (from __future__ imports already make them forward refs). - UP038: merge
  isinstance tuple into a union type in client._request. - UP035 (x3): import
  AsyncIterator/Awaitable/Callable/Iterable from collections.abc instead of typing. - RUF002 (x3):
  replace en dashes with hyphens in numeric-range docstrings where ruff flagged them as ambiguous. -
  RUF100 (x4) + I001 (x2): drop unused 'noqa: E402' directives and reorganise the conftest imports
  so env bootstrapping happens inside the session fixture, leaving module-top imports clean.

Also runs ruff format across the codebase so 'ruff format --check' passes in CI.

### Documentation

- Add architecture diagram, detailed install guide, feature-doc rule
  ([`8691a1d`](https://github.com/FreddyMcFett/fortios-mcp/commit/8691a1d6b9dd0ad4eb0aa10c821fa57b3dafada0))

- New docs/architecture.svg — clean SVG architecture diagram with Fortinet-inspired styling (red
  chassis, port row, endpoint list); replaces the ASCII sketch in the README. - New
  docs/installation.md — long-form install & usage guide covering prerequisites, FortiGate token
  setup (RO + RW), uv / pipx / Docker / systemd paths, Claude Desktop and Claude Code wiring, VDOM
  handling, TLS hardening, upgrades, and troubleshooting. - CLAUDE.md §10a and CONTRIBUTING.md:
  require every feature-changing PR to ship matching doc updates (tool docstring, README catalog,
  installation guide, and architecture diagram where relevant). - README.md: embed the new SVG, add
  a documentation map, and point the quick-start at the detailed guide.


## v0.1.0 (2026-04-18)

### Chores

- Add project scaffolding, packaging, and release config
  ([`c8bacfc`](https://github.com/FreddyMcFett/fortios-mcp/commit/c8bacfcea958e2d83b5ed5317df705d9ba700033))

Introduces the pyproject.toml (hatchling build, ruff + mypy + pytest + python-semantic-release
  config), MIT LICENSE, .gitignore, a seeded CHANGELOG.md, and the .env.example template for
  environment-driven configuration.

### Continuous Integration

- Add GitHub Actions for tests, semantic-release, and GHCR publish
  ([`80274ea`](https://github.com/FreddyMcFett/fortios-mcp/commit/80274ea051f4790e17212a59aaed0a00e6c3d809))

- ci.yml: ruff lint + format check, mypy strict, pytest with coverage across Python 3.12 and 3.13. -
  release.yml: python-semantic-release on push to main — bumps pyproject.toml +
  __init__.__version__, regenerates CHANGELOG, creates tag and GitHub release. - docker-publish.yml:
  on tag v*, build multi-arch (amd64 + arm64) image and push to ghcr.io/freddymcfett/fortios-mcp
  with semver tags. - Dockerfile: multi-stage (uv-powered builder + python:3.12-slim runtime) with
  non-root user and HTTP healthcheck. - docker-compose.yml: reference deployment on port 8002.

### Documentation

- Add CLAUDE.md handbook, README, CONTRIBUTING, and SECURITY
  ([`f997846`](https://github.com/FreddyMcFett/fortios-mcp/commit/f997846568908430421f3c13a9992ecffe98d57b))

CLAUDE.md is the contributor bible: architecture, directory tour, tool taxonomy, coding standards,
  testing rules, Conventional Commits guide, release flow, write-guard invariant, and a runbook for
  stdio/HTTP/ Claude Desktop deployments.

README.md replaces the stub with a full tool catalogue (~88 tools across 11 categories), config
  reference, and quick-start instructions.

CONTRIBUTING.md documents the Conventional Commits contract that drives automated releases.
  SECURITY.md defines the threat model and private disclosure process.

### Features

- Initial FortiOS MCP server with hybrid tool surface
  ([`bca0f27`](https://github.com/FreddyMcFett/fortios-mcp/commit/bca0f27399bf3dd5e3931d865fbe854abd46fd73))

Ships a FastMCP server that drives a FortiGate via its FortiOS REST API v2 for configuration,
  troubleshooting, monitoring, and review.

Highlights:

- FortiOSClient: async httpx wrapper around /api/v2/{cmdb,monitor,log, service} with Bearer-token
  auth, retries on 429/5xx/network errors, TLS verification, response envelope parsing, and version
  detection. - Hybrid tool surface (~88 tools): 8 generic CRUD primitives for full API coverage, 4
  Swagger-backed schema discovery tools reading the bundled 7.6.6 api-docs, and curated wrappers
  across system, firewall, routing, VPN, user, security-profile, monitor, log, and diagnostic
  categories. - Read-only by default: every mutating tool is decorated with @require_writes and
  refuses to run unless FORTIOS_ENABLE_WRITES=true. - Pydantic settings with .env support,
  permission-warning on loose .env files, and sensitive-field redaction before any log output. -
  stdio and streamable-HTTP transports with Docker-aware auto-detection.

### Testing

- Add hermetic unit tests and integration placeholder
  ([`0da59cd`](https://github.com/FreddyMcFett/fortios-mcp/commit/0da59cd17052429cee9c8b76e27a9b7b08c5245a))

Tests run against httpx.MockTransport so no real FortiGate is required.

- test_client: HTTP path construction, Bearer auth, error mapping for 401/404/429/424 + version
  parsing from probe(). - test_swagger: every bundled api-doc parses, Firewall/Monitor endpoints are
  discoverable, keyword search works. - test_write_guard: parametrised check that every expected
  mutating tool carries @require_writes and returns the guard error when FORTIOS_ENABLE_WRITES is
  false. - test_generic_tools, test_curated_tools, test_config, test_validation for additional
  happy-path and negative coverage. - tests/integration/test_real_system.py skipped by default; runs
  only when FORTIOS_HOST and FORTIOS_API_TOKEN are set.
