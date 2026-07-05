"""Tool registry for managing MCP tools."""

import logging
from typing import Any

from contracts import Tool, ToolResult

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for managing and executing tools."""

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool."""
        if tool.name in self._tools:
            logger.warning(f"Tool {tool.name} already registered, overwriting")
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")

    def unregister(self, name: str) -> None:
        """Unregister a tool."""
        if name in self._tools:
            del self._tools[name]
            logger.info(f"Unregistered tool: {name}")

    def get(self, name: str) -> Tool | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> list[dict[str, Any]]:
        """List all registered tools."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
            }
            for tool in self._tools.values()
        ]

    async def execute(self, name: str, params: dict[str, Any]) -> ToolResult:
        """Execute a tool with given parameters."""
        tool = self.get(name)
        if not tool:
            raise ValueError(f"Tool {name} not found")

        logger.info(f"Executing tool: {name} with params: {params}")

        try:
            result = await tool.execute(params)
            logger.info(f"Tool {name} executed successfully")
            return result
        except Exception as e:
            logger.error(f"Tool {name} execution failed: {e}")
            raise
