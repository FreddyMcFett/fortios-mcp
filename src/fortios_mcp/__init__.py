"""FortiOS MCP server package."""

from importlib.metadata import PackageNotFoundError, version

__version__ = "0.1.0"

try:
    __version__ = version("fortios-mcp")
except PackageNotFoundError:
    pass

__all__ = ["__version__"]
