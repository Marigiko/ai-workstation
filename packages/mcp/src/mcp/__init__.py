"""MCP (Model Context Protocol) package."""

from mcp.registry import ToolRegistry
from mcp.server import MCPServer
from mcp.tools import FilesystemTool, GitTool, HttpRequestTool, ShellTool, WebSearchTool

__version__ = "0.1.0"

__all__ = [
    "ToolRegistry",
    "MCPServer",
    "FilesystemTool",
    "GitTool",
    "HttpRequestTool",
    "ShellTool",
    "WebSearchTool",
]
