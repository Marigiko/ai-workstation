"""MCP Protocol server implementation.

Exposes tools via Model Context Protocol (stdio/SSE transport).
"""

import asyncio
import json
import logging
from typing import Any

from mcp import ToolRegistry

logger = logging.getLogger(__name__)


class MCPServer:
    """MCP Protocol server that exposes tools via stdio or SSE.

    Implements the MCP specification for tool discovery and execution.
    """

    def __init__(self, tool_registry: ToolRegistry):
        self.tool_registry = tool_registry
        self._running = False

    async def list_tools(self) -> list[dict[str, Any]]:
        """List all available tools in MCP format."""
        tools = []
        for tool_name in self.tool_registry.list_tools():
            tool = self.tool_registry.get(tool_name)
            if tool:
                tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.input_schema,
                })
        return tools

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool and return result in MCP format."""
        tool = self.tool_registry.get(name)
        if not tool:
            return {
                "content": [{"type": "text", "text": f"Tool '{name}' not found"}],
                "isError": True,
            }

        try:
            result = await tool.execute(arguments)

            if result.success:
                if isinstance(result.output, str):
                    output_text = result.output
                else:
                    output_text = json.dumps(result.output)
                return {
                    "content": [{"type": "text", "text": output_text}],
                    "isError": False,
                }
            else:
                return {
                    "content": [{"type": "text", "text": result.error or "Tool execution failed"}],
                    "isError": True,
                }
        except Exception as e:
            logger.error("MCP tool execution failed: %s", e, exc_info=True)
            return {
                "content": [{"type": "text", "text": str(e)}],
                "isError": True,
            }

    async def handle_message(self, message: dict[str, Any]) -> dict[str, Any]:
        """Handle an incoming MCP message."""
        method = message.get("method")
        params = message.get("params", {})
        msg_id = message.get("id")

        if method == "tools/list":
            tools = await self.list_tools()
            return {"id": msg_id, "result": {"tools": tools}}

        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            result = await self.call_tool(tool_name, arguments)
            return {"id": msg_id, "result": result}

        else:
            return {
                "id": msg_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }

    async def run_stdio(self):
        """Run MCP server over stdio transport."""
        import sys

        self._running = True
        logger.info("MCP server running on stdio")

        while self._running:
            try:
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )
                if not line:
                    break

                message = json.loads(line.strip())
                response = await self.handle_message(message)

                output = json.dumps(response)
                sys.stdout.write(output + "\n")
                sys.stdout.flush()

            except json.JSONDecodeError:
                logger.warning("Invalid JSON received")
            except Exception as e:
                logger.error("MCP stdio error: %s", e, exc_info=True)

    def stop(self):
        """Stop the MCP server."""
        self._running = False
