# FortiOS MCP Server — Installation & Setup Guide

This guide walks you through installing and configuring the FortiOS MCP
server and wiring it into Claude Desktop, Claude Code, Perplexity, or any
other MCP-compatible client.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [FortiGate REST API token](#fortigate-rest-api-token)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [MCP Client Setup](#mcp-client-setup)
6. [Docker / HTTP Deployment](#docker--http-deployment)
7. [Production Deployment (Reverse Proxy)](#production-deployment-reverse-proxy)
8. [Testing the Connection](#testing-the-connection)
9. [Troubleshooting](#troubleshooting)
10. [Migration notes](#migration-notes)

---

## Prerequisites

- **Python 3.12+** installed
- **FortiGate** running FortiOS **7.6.6** (the only version the bundled
  Swagger files and curated tools are validated against)
- **FortiGate REST API token** with `trusthost` restricted to the IP of
  the host running `fortios-mcp`
- **Claude Desktop**, **Claude Code**, **Perplexity**, or any other
  MCP-compatible client

---

## FortiGate REST API token

Replace `<workstation-ip>` with the IP of the machine running
`fortios-mcp`. The `trusthost` field is enforced by FortiOS, so the
token is only usable from that source address.

```cli
config system accprofile
    edit "mcp_readonly"
        set scope global
        set sysgrp read
        set fwgrp read
        set netgrp read
        set vpngrp read
        set utmgrp read
        set loggrp read
    next
end

config system api-user
    edit "mcp"
        set accprofile "mcp_readonly"
        set trusthost1 <workstation-ip>/32
    next
end

execute api-user generate-key mcp
```

FortiOS prints the token once — copy it immediately, you cannot fetch
it again.

> Need write access? Create a second `accprofile` with `read-write`
> groups and a separate `mcp_rw` api-user. Keep them apart so you can
> flip between read-only and read-write tokens deliberately.

---

## Installation

### Option 1: Using uv (recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package manager:

```bash
# Install uv (macOS / Linux)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with Homebrew
brew install uv
```

Then install the FortiOS MCP server:

```bash
git clone https://github.com/FreddyMcFett/fortios-mcp.git
cd fortios-mcp

# Create virtual environment and install
uv venv
source .venv/bin/activate
uv pip install -e .
```

### Option 2: Using pip

```bash
git clone https://github.com/FreddyMcFett/fortios-mcp.git
cd fortios-mcp

python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Option 3: Using Docker

See [Docker / HTTP Deployment](#docker--http-deployment) below.

---

## Configuration

The server reads every setting from environment variables. You can set
them via:

- A `.env` file in the project directory (must be `chmod 600`)
- Shell environment variables
- The `env` block in your MCP client's config

### Required variables

| Variable | Description | Example |
|----------|-------------|---------|
| `FORTIOS_HOST` | FortiGate hostname or IP | `fgt.example.com` |
| `FORTIOS_API_TOKEN` | REST API admin token | `xxxxxxxxxxxx` |

### Optional variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `FORTIOS_PORT` | `443` | HTTPS port |
| `FORTIOS_VERIFY_SSL` | `true` | Set `false` for self-signed certs |
| `FORTIOS_TIMEOUT` | `30` | Per-request timeout (seconds) |
| `FORTIOS_MAX_RETRIES` | `3` | Retries on 429 / 5xx / network error |
| `FORTIOS_DEFAULT_VDOM` | `root` | VDOM used when a tool call omits one |
| `FORTIOS_ENABLE_WRITES` | `false` | **Must be `true` for any mutating tool** |
| `FORTIOS_TOOL_MODE` | `full` | `full` or `dynamic` |
| `MCP_SERVER_MODE` | `auto` | `auto`, `stdio`, or `http` |
| `MCP_SERVER_HOST` | `0.0.0.0` | HTTP bind address |
| `MCP_SERVER_PORT` | `8002` | HTTP port |
| `MCP_AUTH_TOKEN` | unset | Bearer token required in HTTP mode |
| `MCP_ALLOWED_HOSTS` | unset | Extra allowed Host headers (JSON array or CSV) |
| `LOG_LEVEL` | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `LOG_FILE` | unset | Path to mirror logs to disk |

### Example `.env` file

```bash
# FortiGate connection
FORTIOS_HOST=fgt.example.com
FORTIOS_API_TOKEN=your-api-token-here
FORTIOS_VERIFY_SSL=false

# Safety
FORTIOS_ENABLE_WRITES=false

# Logging
LOG_LEVEL=INFO
```

Then protect the file:

```bash
chmod 600 .env
```

---

## MCP Client Setup

MCP is supported by many AI clients. Pick yours:

### Claude Desktop

Edit `claude_desktop_config.json`:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "fortios": {
      "command": "/path/to/fortios-mcp/.venv/bin/fortios-mcp",
      "env": {
        "FORTIOS_HOST": "fgt.example.com",
        "FORTIOS_API_TOKEN": "your-api-token-here",
        "FORTIOS_VERIFY_SSL": "false",
        "FORTIOS_DEFAULT_VDOM": "root",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

Restart Claude Desktop (`Cmd+Q` on macOS, then reopen).

### Claude Code (CLI)

```bash
# Install Claude Code
npm install -g @anthropic-ai/claude-code

# Add the MCP server
claude mcp add fortios -s user \
  -e FORTIOS_HOST=fgt.example.com \
  -e FORTIOS_API_TOKEN=your-api-token \
  -e FORTIOS_VERIFY_SSL=false \
  -- /path/to/fortios-mcp/.venv/bin/fortios-mcp

# Verify
claude mcp list
```

Or drop this block into `~/.claude/mcp_servers.json` (or
`.claude/mcp.json` per-project):

```json
{
  "mcpServers": {
    "fortios": {
      "command": "/path/to/fortios-mcp/.venv/bin/fortios-mcp",
      "env": {
        "FORTIOS_HOST": "fgt.example.com",
        "FORTIOS_API_TOKEN": "your-api-token",
        "FORTIOS_VERIFY_SSL": "false"
      }
    }
  }
}
```

### Perplexity (Mac app)

1. Install the **PerplexityXPC** helper (required for local MCP).
2. Open Perplexity Settings → MCP Connectors.
3. Add a new local MCP server:

```json
{
  "fortios": {
    "type": "stdio",
    "command": "/path/to/fortios-mcp/.venv/bin/fortios-mcp",
    "env": {
      "FORTIOS_HOST": "fgt.example.com",
      "FORTIOS_API_TOKEN": "your-api-token",
      "FORTIOS_VERIFY_SSL": "false"
    }
  }
}
```

### Other MCP-compatible clients

| Client | MCP Support | Notes |
|--------|-------------|-------|
| **Claude Desktop** | Native | Full support via config file |
| **Claude Code** | Native | CLI (`claude mcp add`) |
| **Perplexity** | Native | Mac app with PerplexityXPC |
| **ChatGPT** | Yes | Via plugins / actions |
| **Google Gemini** | Yes | Via extensions |
| **VS Code Copilot** | Yes | Via MCP extension |
| **Cursor** | Yes | Native MCP support |

For any other client, use the standard stdio MCP config shown above.

**Important:**
- Use the **full path** to the `fortios-mcp` executable in your venv.
- Replace credentials with real FortiGate details.
- Set `FORTIOS_VERIFY_SSL=false` only for self-signed labs.

---

## Docker / HTTP Deployment

Pre-built images are published on GitHub Container Registry:

```bash
docker pull ghcr.io/freddymcfett/fortios-mcp:latest
```

### Quick start with Docker Compose

```yaml
# docker-compose.yml
services:
  fortios-mcp:
    image: ghcr.io/freddymcfett/fortios-mcp:latest
    container_name: fortios-mcp
    restart: unless-stopped
    ports:
      - "8002:8002"
    env_file:
      - .env
    environment:
      - MCP_SERVER_MODE=http
      - MCP_SERVER_HOST=0.0.0.0
      - MCP_SERVER_PORT=8002
      - FORTIOS_HOST=fgt.example.com
      - FORTIOS_VERIFY_SSL=false
      - FORTIOS_DEFAULT_VDOM=root
      - FORTIOS_TOOL_MODE=full
      - LOG_LEVEL=INFO
```

Put secrets in `.env` (not tracked in git):

```bash
# .env
FORTIOS_API_TOKEN=your-api-token
MCP_AUTH_TOKEN=your-secret-bearer-token
```

```bash
chmod 600 .env
docker compose up -d
```

Verify the server is alive:

```bash
curl http://localhost:8002/health
# {"status": "healthy", "service": "fortios-mcp", "fortigate_connected": true}
```

### Connecting from an MCP client over HTTP

**Claude Code** (`~/.claude/mcp_servers.json`):

```json
{
  "mcpServers": {
    "fortios": {
      "type": "streamable-http",
      "url": "https://your-mcp-host.example.com/mcp",
      "headers": {
        "Authorization": "Bearer your-mcp-auth-token"
      }
    }
  }
}
```

**Claude Desktop** (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "fortios": {
      "type": "streamable-http",
      "url": "https://your-mcp-host.example.com/mcp",
      "headers": {
        "Authorization": "Bearer your-mcp-auth-token"
      }
    }
  }
}
```

---

## Production Deployment (Reverse Proxy)

For production deployments behind a TLS-terminating reverse proxy:

```
MCP Client → HTTPS → Reverse Proxy (Traefik / nginx) → HTTP → fortios-mcp → FortiGate
```

### Key considerations

1. **`MCP_ALLOWED_HOSTS`** — The MCP SDK validates Host headers to
   prevent DNS rebinding attacks. Behind a reverse proxy, the Host
   header is your external hostname (not `localhost`). You must
   configure allowed hosts:

   ```bash
   MCP_ALLOWED_HOSTS=["mcp.example.com"]
   # or comma-separated:
   MCP_ALLOWED_HOSTS=mcp.example.com,mcp-alt.example.com
   ```

2. **`MCP_AUTH_TOKEN`** — Always set a Bearer token for HTTP
   deployments. The server rejects every non-`/health` request unless
   the token matches.

   ```bash
   MCP_AUTH_TOKEN=$(openssl rand -hex 32)
   ```

3. **Secrets management** — Keep API and auth tokens in an `env_file`
   (`.env`), not inline in `docker-compose.yml`.

### Example with Traefik

```yaml
services:
  fortios-mcp:
    image: ghcr.io/freddymcfett/fortios-mcp:latest
    container_name: fortios-mcp
    restart: unless-stopped
    security_opt:
      - no-new-privileges:true
    env_file:
      - .env
    environment:
      - MCP_SERVER_MODE=http
      - MCP_SERVER_HOST=0.0.0.0
      - MCP_SERVER_PORT=8002
      - FORTIOS_HOST=fgt.example.com
      - FORTIOS_VERIFY_SSL=false
      - MCP_ALLOWED_HOSTS=["mcp.example.com"]
      - FORTIOS_DEFAULT_VDOM=root
      - FORTIOS_TOOL_MODE=full
      - LOG_LEVEL=INFO
    networks:
      - frontend
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.fos-mcp-secure.entrypoints=https"
      - "traefik.http.routers.fos-mcp-secure.rule=Host(`mcp.example.com`)"
      - "traefik.http.routers.fos-mcp-secure.tls=true"
      - "traefik.http.services.fos-mcp.loadbalancer.server.port=8002"
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

networks:
  frontend:
    external: true
```

---

## Testing the Connection

### Run from the command line first

Before wiring into an MCP client, verify the server starts and
authenticates:

```bash
cd fortios-mcp
source .venv/bin/activate

export FORTIOS_HOST="fgt.example.com"
export FORTIOS_API_TOKEN="your-api-token"
export FORTIOS_VERIFY_SSL="false"

# Validate config without starting the server
fortios-mcp --check

# Or run it:
fortios-mcp
```

The `--check` flag validates credentials and exits 0 if the environment
is ready. A running server waits for an MCP client on stdio and logs:

```
INFO - Starting FortiOS MCP server v...
INFO - Detected FortiOS version (7, 6, 6)
INFO - Launching FortiOS MCP server in stdio mode
```

Press Ctrl+C to stop.

### Verify in Claude Desktop

Once configured, ask Claude:

> "What FortiOS tools are available?"

or

> "Get the system status of the FortiGate"

Claude should respond using the MCP tools.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `error: Missing required environment variables: FORTIOS_HOST, FORTIOS_API_TOKEN` | Env vars not exported or `.env` not loaded | Export both variables or populate `.env`, then rerun |
| `AuthenticationError` on first call | Wrong token or source IP not in `trusthost` | Re-check the token and `trusthost1` on the api-user |
| `ssl.SSLCertVerificationError` | Self-signed FortiGate cert | Set `FORTIOS_VERIFY_SSL=false` (lab only) or install a trusted cert |
| Tool call returns `"Write operations are disabled"` | Write-guard blocking a mutating tool | Set `FORTIOS_ENABLE_WRITES=true` and restart |
| `NotFoundError` on a valid-looking path | VDOM mismatch | Pass `vdom=` explicitly or set `FORTIOS_DEFAULT_VDOM` |
| Claude Desktop shows no `fortios` server | `command` / `args` / `cwd` wrong in `claude_desktop_config.json` | Use an **absolute** path, and check the Claude Desktop MCP log file |
| HTTP 401 from `/mcp` | `MCP_AUTH_TOKEN` mismatch | Check both ends of the Bearer token |
| HTTP 421 or Host-header rejection behind proxy | `MCP_ALLOWED_HOSTS` unset | Add your public hostname to `MCP_ALLOWED_HOSTS` |
| `fortigate_connected: false` in `/health` | Initial probe failed | Inspect container logs; check network / token |

Enable `LOG_LEVEL=DEBUG` for per-request traces; all tokens, passwords,
and PSKs are redacted by `sanitize_for_logging()` before anything hits
the log.

### Viewing Claude Desktop MCP logs

- **macOS**: `~/Library/Logs/Claude/mcp-server-fortios.log`
- **Windows**: `%APPDATA%\Claude\logs\mcp-server-fortios.log`

---

## Migration notes

This section tracks operator-visible changes between releases.

### Unreleased

- `MCP_AUTH_TOKEN` is now enforced in HTTP mode. Set it before exposing
  the container to a network, or authenticated clients will be
  rejected. Deployments that previously relied on the (unenforced)
  setting and deliberately left it unset will keep working — auth is
  off when `MCP_AUTH_TOKEN` is empty.
- `MCP_ALLOWED_HOSTS` is now enforced by the MCP SDK's transport
  security. Existing localhost/Docker deployments without a reverse
  proxy are unaffected; reverse-proxy deployments **must** list their
  external hostname here.
- `/health` is now a real HTTP endpoint returning JSON. Docker
  healthchecks should target `http://localhost:8002/health`.
- `move_firewall_policy` now issues the correct FortiOS query-parameter
  call (`action=move&before=<id>` or `after=<id>`). The previous
  implementation sent the parameters as a JSON body and always failed
  against a real FortiGate.
