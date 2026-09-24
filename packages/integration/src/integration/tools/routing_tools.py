"""Routing info tool for MCP integration."""

from typing import Any

from contracts import ToolResult


class RoutingInfoTool:
    """Tool: Get current routing status and available providers."""

    name = "routing_info"
    description = "Get current routing status: available providers, models, and their capabilities."
    input_schema = {
        "type": "object",
        "properties": {},
    }

    def __init__(self, provider_registry):
        self.provider_registry = provider_registry

    async def execute(self, params: dict[str, Any]) -> ToolResult:
        try:
            names = self.provider_registry.list_providers()
            if not names:
                return ToolResult(
                tool_name=self.name,
                success=True,
                output="",
            )

            output = "Available providers:\n"
            for name in names:
                provider = self.provider_registry.get(name)
                model = getattr(provider, "model", "unknown") if provider else "unknown"
                output += f"  - {name}: {model}\n"
            return ToolResult(tool_name=self.name, success=True, output=output)
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, output="", error=str(e))
