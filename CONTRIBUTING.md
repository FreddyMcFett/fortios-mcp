# Contributing to fortios-mcp

Thanks for looking at the code. This guide covers the bits every PR has
to get right; the full developer handbook lives in
[`CLAUDE.md`](CLAUDE.md).

## Getting set up

```bash
git clone https://github.com/FreddyMcFett/fortios-mcp.git
cd fortios-mcp
uv venv
uv pip install -e ".[dev]"
```

## Pre-PR checklist

- [ ] `uv run ruff check src/ tests/`
- [ ] `uv run ruff format --check src/ tests/`
- [ ] `uv run mypy src/`
- [ ] `uv run pytest tests/ --ignore=tests/integration`
- [ ] New tool is listed in the catalogue in `README.md`
- [ ] Every write tool is decorated with `@require_writes` and listed in
      `tests/test_write_guard.py::EXPECTED_WRITE_TOOLS`
- [ ] **Docs updated for every feature change** — see
      [docs requirement](#documentation-required-for-every-feature-change)

## Documentation required for every feature change

Any PR that adds or changes a user-visible feature (new tool, new
env-var, new transport option, changed tool signature, changed
default) MUST ship the matching doc updates in the same PR. Reviewers
reject feature PRs with stale docs.

For a new tool this means, at minimum:

- A Google-style docstring on the tool function describing endpoint,
  VDOM handling, arguments, return shape, and whether it is
  write-guarded. MCP clients surface this to the model at runtime.
- An entry in the **Tool catalog** table in [`README.md`](README.md)
  (trailing `*` if write-guarded).
- Updates to [`docs/installation.md`](docs/installation.md) if the
  change affects configuration, installation steps, usage examples,
  or troubleshooting.
- A new architecture diagram
  ([`docs/architecture.svg`](docs/architecture.svg)) only when the
  change alters the high-level architecture — not for normal tool
  additions.

Do **not** edit `CHANGELOG.md` by hand — `python-semantic-release`
writes it from your Conventional Commit message. Your commit message
is the changelog entry, so be precise. See
[`CLAUDE.md` §10a](CLAUDE.md#10a-documentation-requirement-for-feature-changes)
for the full rule.

## Commit messages — Conventional Commits

Versioning is automated, driven by commit prefixes:

- `feat:` — user-visible feature → **minor** bump
- `fix:` / `perf:` → **patch** bump
- `feat!:` / footer `BREAKING CHANGE:` → **major** bump
- `docs:` / `test:` / `chore:` / `refactor:` / `ci:` / `build:` / `style:` →
  no bump

Example:

```
feat(routing): add BGP summary tool

Exposes /api/v2/monitor/router/bgp/summary via get_bgp_summary().
```

Non-conforming commit messages will break the `release` workflow.
You can install [`commitizen`](https://commitizen-tools.github.io/commitizen/)
locally to avoid mistakes:

```bash
uv pip install commitizen
cz commit
```

## Scope of contributions

- **Add a curated tool** (recommended): pick a feature area, add a
  function to the matching `*_tools.py`, write a unit test, list it in
  the README.
- **Improve the API client** (less common): changes to
  `api/client.py` must ship regression tests using
  `httpx.MockTransport`.
- **Update the api-docs** when a new FortiOS version ships — see
  [`CLAUDE.md` §11](CLAUDE.md).

## Security issues

Please do not file security problems as public issues. See
[`SECURITY.md`](SECURITY.md) for private disclosure instructions.
