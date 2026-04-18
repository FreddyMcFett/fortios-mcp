"""Lazy index over the bundled FortiOS Swagger definitions.

The repository ships ~81 Swagger 2.0 files under ``api-docs/`` that describe
every FortiOS REST endpoint. This module exposes them as a searchable index
so MCP tools can answer "which endpoints exist, what parameters, what
response schema" without hard-coding each one.
"""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Iterable
from functools import lru_cache
from importlib.resources import as_file, files
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

API_TYPES: tuple[str, ...] = ("Configuration", "Monitor", "Log", "Service")
_FILENAME_RE = re.compile(r"^(Configuration|Monitor|Log|Service) API (.+?)(?: \(\d+\))?\.json$")


def _api_docs_dir() -> Path:
    """Return the directory containing the Swagger files.

    Works both in development (repo root ``api-docs/``) and when installed as a
    wheel (``fortios_mcp/api-docs/`` bundled via hatch force-include).
    """
    try:
        resource = files("fortios_mcp").joinpath("api-docs")
        with as_file(resource) as path:
            if path.is_dir():
                return path
    except (ModuleNotFoundError, FileNotFoundError):
        pass

    here = Path(__file__).resolve()
    for parent in (here.parent, *here.parents):
        candidate = parent / "api-docs"
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("api-docs directory not found; is the package installed correctly?")


class SwaggerIndex:
    """Lazy index of FortiOS Swagger files grouped by API type and category."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or _api_docs_dir()
        self._files: dict[tuple[str, str], Path] = {}
        self._cache: dict[tuple[str, str], dict[str, Any]] = {}
        self._scan()

    def _scan(self) -> None:
        for path in sorted(self.root.glob("*.json")):
            match = _FILENAME_RE.match(path.name)
            if not match:
                logger.debug("Skipping unrecognised api-doc filename: %s", path.name)
                continue
            api_type, category = match.group(1), match.group(2)
            self._files[(api_type, category)] = path

    def _load(self, api_type: str, category: str) -> dict[str, Any]:
        key = (api_type, category)
        if key not in self._cache:
            path = self._files.get(key)
            if path is None:
                raise KeyError(f"No Swagger file for {api_type}/{category}")
            self._cache[key] = json.loads(path.read_text(encoding="utf-8"))
        return self._cache[key]

    # Public API ---------------------------------------------------------

    def api_types(self) -> list[str]:
        """Return the set of API types actually present on disk."""
        return sorted({t for t, _ in self._files})

    def categories(self, api_type: str) -> list[str]:
        """Return all known categories (file groups) for ``api_type``."""
        return sorted(c for t, c in self._files if t == api_type)

    def file_count(self) -> int:
        return len(self._files)

    def endpoints(self, api_type: str, category: str) -> list[dict[str, Any]]:
        """Return a compact summary of every endpoint in one Swagger file."""
        spec = self._load(api_type, category)
        base = spec.get("basePath", "")
        out: list[dict[str, Any]] = []
        for path, methods in spec.get("paths", {}).items():
            for method, op in methods.items():
                if method.lower() not in {"get", "post", "put", "delete", "patch"}:
                    continue
                out.append(
                    {
                        "method": method.upper(),
                        "path": path,
                        "full_path": base + path,
                        "summary": (op.get("summary") or "").strip(),
                        "tags": op.get("tags", []),
                    }
                )
        return out

    def describe(self, api_type: str, category: str, path: str, method: str) -> dict[str, Any]:
        """Return parameters, body schema and response schema for one endpoint."""
        spec = self._load(api_type, category)
        paths = spec.get("paths", {})
        if path not in paths:
            raise KeyError(f"Path {path!r} not found in {api_type}/{category}")
        op = paths[path].get(method.lower())
        if op is None:
            raise KeyError(f"Method {method!r} not defined on {path!r}")
        return {
            "api_type": api_type,
            "category": category,
            "method": method.upper(),
            "path": path,
            "full_path": spec.get("basePath", "") + path,
            "summary": (op.get("summary") or "").strip(),
            "tags": op.get("tags", []),
            "parameters": op.get("parameters", []),
            "responses": op.get("responses", {}),
        }

    def search(self, query: str, limit: int = 50) -> list[dict[str, Any]]:
        """Substring search across paths, summaries and tags."""
        needle = query.lower().strip()
        if not needle:
            return []
        hits: list[dict[str, Any]] = []
        for (api_type, category), path in self._files.items():
            try:
                spec = self._load(api_type, category)
            except Exception as exc:  # pragma: no cover - corrupted file
                logger.warning("Failed to parse %s: %s", path.name, exc)
                continue
            base = spec.get("basePath", "")
            for p, methods in spec.get("paths", {}).items():
                for method, op in methods.items():
                    if method.lower() not in {"get", "post", "put", "delete", "patch"}:
                        continue
                    summary = (op.get("summary") or "").lower()
                    tags = " ".join(op.get("tags", [])).lower()
                    haystack = f"{p.lower()} {summary} {tags}"
                    if needle in haystack:
                        hits.append(
                            {
                                "api_type": api_type,
                                "category": category,
                                "method": method.upper(),
                                "path": p,
                                "full_path": base + p,
                                "summary": (op.get("summary") or "").strip(),
                            }
                        )
                        if len(hits) >= limit:
                            return hits
        return hits

    def all_endpoints(self) -> Iterable[tuple[str, str, str, str]]:
        """Yield ``(api_type, category, method, path)`` for every endpoint."""
        for (api_type, category), _ in self._files.items():
            for ep in self.endpoints(api_type, category):
                yield api_type, category, ep["method"], ep["path"]


@lru_cache
def get_swagger_index() -> SwaggerIndex:
    return SwaggerIndex()
