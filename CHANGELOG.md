# CHANGELOG


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
