"""MCP (Model Context Protocol) package."""

from mcp.registry import ToolRegistry
from mcp.tools import FilesystemTool, GitTool, ShellTool

__version__ = "0.1.0"

__all__ = [
    "ToolRegistry",
    "FilesystemTool",
    "GitTool",
    "ShellTool",
]
