"""Integration MCP Server for external AI clients (Claude Code, Kimi, etc.).

Exposes AI Workstation capabilities via Model Context Protocol.
"""

import asyncio
import json
import logging
from typing import Any

from mcp import ToolRegistry

from integration.tools import (
    ContextSearchTool,
    ConversationHistoryTool,
    MemoryRecallTool,
    MemoryRememberTool,
    MemoryStatusTool,
    RoutingInfoTool,
    SkillExecuteTool,
)

logger = logging.getLogger(__name__)


class IntegrationMCPServer:
    """MCP server exposing AI Workstation tools to external clients.

    Usage:
        server = IntegrationMCPServer(
            memory_service=memory_service,
            skill_registry=skill_registry,
            provider_registry=provider_registry,
            conversation_service_factory=factory,
            context_sources=context_sources,
        )
        await server.run_stdio()  # for Claude Code / Kimi local connection
    """

    def __init__(
        self,
        memory_service=None,
        skill_registry=None,
        provider_registry=None,
        conversation_service_factory=None,
        context_sources: list | None = None,
        allow_global_memory: bool = True,
    ):
        """

        Args:
            memory_service: Memory service instance
            skill_registry: Skill registry instance
            provider_registry: Provider registry instance
            conversation_service_factory: Factory for conversation services
            context_sources: List of context sources
            allow_global_memory: If False, restricts MCP from writing to global
                memory scope (security for external agents).
        """
        self.tool_registry = ToolRegistry()
        self._register_tools(
            memory_service=memory_service,
            skill_registry=skill_registry,
            provider_registry=provider_registry,
            conversation_service_factory=conversation_service_factory,
            context_sources=context_sources or [],
            allow_global_memory=allow_global_memory,
        )

    def _register_tools(self, **kwargs):
        """Register all available integration tools."""
        allow_global = kwargs.get("allow_global_memory", True)
        if kwargs.get("memory_service"):
            self.tool_registry.register(
                MemoryRememberTool(kwargs["memory_service"], allow_global=allow_global)
            )
            self.tool_registry.register(MemoryRecallTool(kwargs["memory_service"]))
            self.tool_registry.register(MemoryStatusTool())

        if kwargs.get("skill_registry"):
            self.tool_registry.register(SkillExecuteTool(kwargs["skill_registry"]))

        if kwargs.get("provider_registry"):
            self.tool_registry.register(RoutingInfoTool(kwargs["provider_registry"]))

        if kwargs.get("conversation_service_factory"):
            self.tool_registry.register(
                ConversationHistoryTool(kwargs["conversation_service_factory"])
            )

        if kwargs.get("context_sources"):
            self.tool_registry.register(
                ContextSearchTool(kwargs["context_sources"])
            )

    async def list_tools(self) -> list[dict[str, Any]]:
        """List all available tools in MCP format."""
        tools = []
        for tool_info in self.tool_registry.list_tools():
            tools.append({
                "name": tool_info["name"],
                "description": tool_info["description"],
                "inputSchema": tool_info["input_schema"],
            })
        return tools

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool and return result."""
        tool = self.tool_registry.get(name)
        if not tool:
            return {
                "content": [{"type": "text", "text": f"Tool '{name}' not found"}],
                "isError": True,
            }

        try:
            result = await tool.execute(arguments)
            if result.success:
                output = (
                    result.output
                    if isinstance(result.output, str)
                    else json.dumps(result.output)
                )
                return {
                    "content": [{"type": "text", "text": output}],
                    "isError": False,
                }
            else:
                return {
                    "content": [{"type": "text", "text": result.error or "Tool execution failed"}],
                    "isError": True,
                }
        except Exception as e:
            logger.error("Tool execution failed: %s", e, exc_info=True)
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
        """Run MCP server over stdio transport (for Claude Code / Kimi)."""
        self._running = True
        logger.info("Integration MCP server running on stdio")

        while self._running:
            try:
                line = await asyncio.get_event_loop().run_in_executor(
                    None, input
                )
                if not line:
                    break

                message = json.loads(line.strip())
                response = await self.handle_message(message)

                output = json.dumps(response)
                print(output, flush=True)

            except EOFError:
                logger.info("stdin closed, stopping MCP server")
                break
            except json.JSONDecodeError:
                logger.warning("Invalid JSON received")
            except Exception as e:
                logger.error("MCP stdio error: %s", e, exc_info=True)

    def stop(self):
        """Stop the server."""
        self._running = False
