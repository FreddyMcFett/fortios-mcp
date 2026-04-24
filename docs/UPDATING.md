# Updating FortiOS MCP for new FortiOS releases

This document describes the workflow for bumping the server to a new
FortiOS REST API release.

## Overview

Fortinet ships a new FortiOS release approximately every 6-8 weeks.
Each release may add new endpoints, rename parameters, or change
response shapes. The server pins itself to a single *supported* version
(declared in `src/fortios_mcp/api/client.py` as
`SUPPORTED_FORTIOS_VERSION`) and refuses to hide schema changes —
every bump is a deliberate update to the bundled Swagger files plus
any curated tools whose contract has changed.

## Update workflow

### Step 1: Obtain FNDN API definitions

1. Download the new Swagger bundle from FNDN:
   - https://fndn.fortinet.net/
   - Or extract from the FortiGate: **System → API**.
2. Replace the contents of `api-docs/`. Preserve the file-naming
   convention so `SwaggerIndex` can parse them:

   ```
   api-docs/
   ├── Configuration API firewall.json
   ├── Configuration API system.json
   ├── Monitor API system.json
   ├── Log API disk.json
   └── Service API system.json
   ```

### Step 2: Compare API definitions

Use Claude Code to summarise the diff:

```
Compare the FortiOS Swagger files between 7.6.5 and 7.6.6.
Identify:
1. New endpoints
2. Modified parameters (added / removed / changed)
3. Deprecated endpoints
4. Response-shape changes
```

### Step 3: Review changes

The comparison produces a report like:

```markdown
## API Changes: 7.6.5 → 7.6.6

### New endpoints
- GET /monitor/system/xyz  - new telemetry endpoint
- POST /api/v2/cmdb/firewall/newobject

### Modified endpoints
- GET /api/v2/cmdb/firewall/policy
  - Added parameter: `include_disabled` (boolean)

### Deprecated
- GET /monitor/legacy/...

### Response shape changes
- /monitor/system/status now includes `mitre_attack_id`
```

### Step 4: Update implementation

For each change:

1. **New endpoints** — if they belong to a curated workflow
   (firewall / routing / …), add a curated wrapper in the matching
   `tools/*_tools.py`; otherwise rely on the generic primitives.
2. **Modified parameters** — update tool signatures, docstrings, and
   the catalog table in `README.md`.
3. **Deprecated endpoints** — remove the curated wrapper or mark it
   deprecated; open a `feat!:` commit if the removal is breaking.
4. **Response changes** — update any tool that parses the response.

### Step 5: Tests

```bash
# Swagger parser must still handle every file
uv run pytest tests/test_swagger.py

# Full unit suite
uv run pytest

# Against a real FortiGate on the new release
FORTIOS_HOST=fgt-test FORTIOS_API_TOKEN=... \
  uv run pytest -m integration tests/integration
```

### Step 6: Update documentation

Bump the supported version in:

- `src/fortios_mcp/api/client.py` (`SUPPORTED_FORTIOS_VERSION`)
- `README.md` (prose + Requirements table)
- `CLAUDE.md` (§1 — "what this project is")
- `docs/installation.md` (Prerequisites)

Commit as `feat(api-docs): update to FortiOS X.Y.Z`. The conventional
commit drives the release and populates `CHANGELOG.md` automatically.

## Version support matrix

| FortiOS Version | fortios-mcp Version | Status |
|-----------------|---------------------|--------|
| 7.4.x | — | Unsupported |
| 7.6.4 | — | Unsupported |
| 7.6.5 | 0.1.x | Superseded |
| 7.6.6 | 0.2.x | **Supported** |
| 7.6.7+ | planned | |

## Automated checks (future enhancement)

Ideas worth implementing when there's time:

1. **Schema coverage script** — compare bundled Swagger with
   implemented curated tools, emit an "uncurated endpoints" list.
2. **CI integration** — run `pytest tests/test_swagger.py` on every
   PR that touches `api-docs/`.
3. **Coverage report** — print the percentage of Swagger-described
   endpoints reachable through curated tools (vs. only the generic
   primitives).
