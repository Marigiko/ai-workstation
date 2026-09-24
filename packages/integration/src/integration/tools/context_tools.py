"""Context search tool for MCP integration."""

from typing import Any

from contracts import ContextQuery, ToolResult


class ContextSearchTool:
    """Tool: Search context engine for relevant code/doc snippets.

    Use this for explicit context search when you need MORE than what the
    automatic context recall provides. The pipeline already does basic context
    gathering; this tool gives you full control over query and token budget.
    """

    name = "context_search"
    description = (
        "Deep search in context engine for code/docs. "
        "Use when you need more context than automatic recall provides."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query",
            },
            "project_id": {
                "type": "string",
                "description": "Project ID to search within",
            },
            "max_tokens": {
                "type": "integer",
                "description": "Maximum tokens for context",
                "default": 4096,
            },
        },
        "required": ["query"],
    }

    def __init__(self, context_sources: list):
        self.context_sources = context_sources

    async def execute(self, params: dict[str, Any]) -> ToolResult:
        query = params.get("query", "")
        project_id = params.get("project_id", "default")
        max_tokens = params.get("max_tokens", 4096)

        if not query:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error="",
            )

        if not self.context_sources:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error="",
            )

        try:
            context_query = ContextQuery(
                project_id=project_id,
                query=query,
                max_tokens=max_tokens,
            )
            all_chunks = []
            for source in self.context_sources:
                try:
                    result = await source.gather(context_query)
                    for chunk in result.chunks:
                        all_chunks.append({
                            "content": chunk.content,
                            "source": chunk.source,
                            "score": chunk.score,
                        })
                except Exception:
                    continue

            if not all_chunks:
                return ToolResult(
                tool_name=self.name,
                success=True,
                output="",
            )

            output_lines = []
            for i, chunk in enumerate(all_chunks[:10], 1):
                output_lines.append(f"[{i}] {chunk['source']} (score: {chunk['score']:.2f})")
                output_lines.append(chunk['content'][:300])
                output_lines.append("")
            return ToolResult(tool_name=self.name, success=True, output="\n".join(output_lines))
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, output="", error=str(e))
