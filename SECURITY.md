# Security Policy

## Reporting a vulnerability

Please report suspected vulnerabilities privately by opening a
[private security advisory](https://github.com/FreddyMcFett/fortios-mcp/security/advisories/new)
on GitHub. Do not open a public issue.

You can expect:

- Acknowledgement within 5 business days.
- An assessment and remediation timeline within 15 business days.
- Credit in the CHANGELOG for responsibly disclosed issues (if you want
  it).

## Threat model

`fortios-mcp` holds a FortiGate REST API token and exposes tools that
can mutate firewall configuration and reboot the appliance. Deployments
should:

- Keep `FORTIOS_ENABLE_WRITES=false` unless an operator genuinely needs
  write access in that session.
- Store the API token in an environment variable or a `.env` file with
  `chmod 600` — never in a repository.
- Front the HTTP transport with a TLS-terminating reverse proxy and set
  `MCP_AUTH_TOKEN` so the MCP endpoint requires a bearer token.
- Leave `FORTIOS_VERIFY_SSL=true` in production. Disable only for
  self-signed lab appliances.
- Use a dedicated, least-privilege REST API admin profile on the
  FortiGate, scoped to the VDOMs and access groups your operators
  actually need.
