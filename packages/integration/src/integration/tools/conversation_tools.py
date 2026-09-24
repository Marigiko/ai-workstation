"""Conversation history tool for MCP integration."""

from typing import Any

from contracts import ToolResult


class ConversationHistoryTool:
    """Tool: Get conversation history for a session."""

    name = "conversation_history"
    description = "Retrieve conversation history for a session, with optional limits."
    input_schema = {
        "type": "object",
        "properties": {
            "session_id": {
                "type": "string",
                "description": "Session ID to retrieve history for",
            },
            "max_turns": {
                "type": "integer",
                "description": "Maximum number of recent turns to return",
                "default": 20,
            },
            "max_tokens": {
                "type": "integer",
                "description": "Maximum total tokens (truncates oldest first)",
            },
        },
        "required": ["session_id"],
    }

    def __init__(self, conversation_service_factory):
        """Initialize with a factory that creates ConversationService from session."""
        self.conversation_service_factory = conversation_service_factory

    async def execute(self, params: dict[str, Any]) -> ToolResult:
        session_id = params.get("session_id", "")
        max_turns = params.get("max_turns", 20)
        max_tokens = params.get("max_tokens")

        if not session_id:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error="",
            )

        try:
            service = self.conversation_service_factory()
            messages = await service.get_history(
                session_id=session_id,
                max_turns=max_turns,
                max_tokens=max_tokens,
            )
            if not messages:
                return ToolResult(
                tool_name=self.name,
                success=True,
                output="",
            )

            output_lines = []
            for msg in messages:
                role = msg.role.value if hasattr(msg.role, "value") else str(msg.role)
                output_lines.append(f"[{role}] {msg.content}")
            return ToolResult(tool_name=self.name, success=True, output="\n".join(output_lines))
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, output="", error=str(e))
