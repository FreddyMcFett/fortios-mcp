"""Input validation and log sanitization helpers."""

from __future__ import annotations

from typing import Any

SENSITIVE_FIELDS: set[str] = {
    "password",
    "passwd",
    "pass",
    "secret",
    "secretkey",
    "api_token",
    "apikey",
    "token",
    "access_token",
    "authorization",
    "auth",
    "credential",
    "psk",
    "pre_shared_key",
    "preshared_key",
    "shared_secret",
    "sid",
    "session",
    "cookie",
}

_MAX_DEPTH = 8


def _is_sensitive(key: str) -> bool:
    k = key.lower().replace("-", "_").replace(" ", "_")
    return any(s in k for s in SENSITIVE_FIELDS)


def sanitize_for_logging(data: Any, depth: int = 0) -> Any:
    """Return a copy of ``data`` with secret values redacted."""
    if depth > _MAX_DEPTH:
        return "***TRUNCATED***"
    if isinstance(data, dict):
        return {
            k: ("***REDACTED***" if _is_sensitive(str(k)) else sanitize_for_logging(v, depth + 1))
            for k, v in data.items()
        }
    if isinstance(data, list):
        return [sanitize_for_logging(v, depth + 1) for v in data]
    if isinstance(data, tuple):
        return tuple(sanitize_for_logging(v, depth + 1) for v in data)
    return data


def validate_vdom(name: str) -> str:
    """Accept only conservative VDOM names (alnum, underscore, hyphen, dot)."""
    if not name or len(name) > 31:
        raise ValueError("VDOM name must be 1-31 chars")
    if not all(c.isalnum() or c in "_-." for c in name):
        raise ValueError("VDOM name may only contain alnum, underscore, hyphen, dot")
    return name


def validate_cmdb_path(path: str) -> str:
    """Reject obviously unsafe CMDB path inputs."""
    if not path or path.startswith("/"):
        raise ValueError("CMDB path must be relative, e.g. 'firewall/policy'")
    if ".." in path.split("/"):
        raise ValueError("CMDB path must not contain '..'")
    return path.strip("/")
