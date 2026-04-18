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
