"""Memory tools for MCP integration."""

from typing import Any

from memory.embedding import get_embedding_status

from contracts import MemoryScope, ToolResult


class MemoryRememberTool:
    """Tool: Store a memory for future retrieval.

    Governance: MCP access cannot write to 'global' scope (only project/session).
    CLI has full access.
    """

    name = "memory_remember"
    description = (
        "Store a memory for future retrieval. "
        "Useful for saving decisions, conventions, or facts."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "The information to remember",
            },
            "scope": {
                "type": "string",
                "enum": ["global", "project", "session"],
                "description": (
                    "Memory scope: global (all projects), "
                    "project (specific project), or session (current session only)"
                ),
                "default": "project",
            },
            "project_id": {
                "type": "string",
                "description": "Project ID (required for project scope)",
            },
            "session_id": {
                "type": "string",
                "description": "Session ID (required for session scope)",
            },
        },
        "required": ["content"],
    }

    def __init__(self, memory_service, allow_global: bool = True):
        self.memory_service = memory_service
        self._allow_global = allow_global

    async def execute(self, params: dict[str, Any]) -> ToolResult:
        content = params.get("content", "")
        scope_str = params.get("scope", "project")
        project_id = params.get("project_id")
        session_id = params.get("session_id")

        if not content:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error="",
            )

        # Governance: restrict global scope for MCP access
        if scope_str == "global" and not self._allow_global:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error="Global scope not allowed via MCP. Use 'project' or 'session'.",
            )

        try:
            scope = MemoryScope(scope_str)
            await self.memory_service.remember(
                content=content,
                scope=scope,
                project_id=project_id,
                session_id=session_id,
            )
            return ToolResult(
                tool_name=self.name,
                success=True,
                output="",
            )
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, output="", error=str(e))


class MemoryRecallTool:
    """Tool: Recall memories by semantic query.

    Use this for explicit memory search when you need MORE than what the
    automatic memory recall provides. The pipeline already does basic recall;
    this tool gives you full control over scope and limit.
    """

    name = "memory_recall"
    description = (
        "Deep search in stored memories by semantic relevance. "
        "Use when you need more than automatic recall provides."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query to find relevant memories",
            },
            "scope": {
                "type": "string",
                "enum": ["global", "project", "session"],
                "description": "Scope to search within",
                "default": "project",
            },
            "project_id": {
                "type": "string",
                "description": "Project ID (for project scope)",
            },
            "session_id": {
                "type": "string",
                "description": "Session ID (for session scope)",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results",
                "default": 5,
            },
        },
        "required": ["query"],
    }

    def __init__(self, memory_service):
        self.memory_service = memory_service

    async def execute(self, params: dict[str, Any]) -> ToolResult:
        query = params.get("query", "")
        scope_str = params.get("scope", "project")
        project_id = params.get("project_id")
        session_id = params.get("session_id")
        limit = params.get("limit", 5)

        if not query:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error="",
            )

        try:
            scope = MemoryScope(scope_str)
            memories = await self.memory_service.recall_memories(
                query=query,
                scope=scope,
                project_id=project_id,
                session_id=session_id,
                limit=limit,
            )
            if not memories:
                return ToolResult(
                tool_name=self.name,
                success=True,
                output="",
            )

            output_lines = []
            for m in memories:
                output_lines.append(f"[{m.scope.value}] {m.content}")
            return ToolResult(tool_name=self.name, success=True, output="\n".join(output_lines))
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, output="", error=str(e))


class MemoryStatusTool:
    """Tool: Check embedding provider status for memory."""

    name = "memory_status"
    description = (
        "Check if semantic memory is working. "
        "Returns embedding provider status and whether semantic search is available."
    )
    input_schema = {
        "type": "object",
        "properties": {},
    }

    async def execute(self, params: dict[str, Any]) -> ToolResult:
        status = get_embedding_status()
        if status["semantic"]:
            output = (
                f"Semantic memory ACTIVE\n"
                f"Provider: {status['provider']}\n"
                f"Model: {status['model']}\n"
                f"Dimension: {status['dimension']}"
            )
        else:
            output = (
                "Semantic memory NOT available\n"
                "Using placeholder embeddings (no semantic search)\n"
                "Set OLLAMA_BASE_URL or OPENAI_API_KEY to enable semantic memory"
            )
        return ToolResult(tool_name=self.name, success=True, output=output)
