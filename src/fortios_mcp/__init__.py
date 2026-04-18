"""FortiOS MCP server package."""

from contextlib import suppress
from importlib.metadata import PackageNotFoundError, version

__version__ = "0.1.2"

with suppress(PackageNotFoundError):
    __version__ = version("fortios-mcp")

__all__ = ["__version__"]
