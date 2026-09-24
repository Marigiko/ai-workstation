"""Skill execution tool for MCP integration."""

from typing import Any

from contracts import ToolResult


class SkillExecuteTool:
    """Tool: Execute a registered skill by name."""

    name = "skill_execute"
    description = "Execute a registered skill (workflow) by name with given variables."
    input_schema = {
        "type": "object",
        "properties": {
            "skill_name": {
                "type": "string",
                "description": "Name of the skill to execute (e.g., 'code-review', 'refactor')",
            },
            "variables": {
                "type": "object",
                "description": "Variables to pass to the skill template",
                "additionalProperties": {"type": "string"},
            },
            "context": {
                "type": "string",
                "description": "Additional context for the skill execution",
            },
        },
        "required": ["skill_name"],
    }

    def __init__(self, skill_registry, skill_executor=None):
        self.skill_registry = skill_registry
        self.skill_executor = skill_executor

    async def execute(self, params: dict[str, Any]) -> ToolResult:
        skill_name = params.get("skill_name", "")
        variables = params.get("variables", {})
        context = params.get("context", "")

        if not skill_name:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error="",
            )

        skill = self.skill_registry.get(skill_name)
        if not skill:
            available = [s.name for s in self.skill_registry.list_skills()]
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error=f"Skill '{skill_name}' not found. Available: {available}",
            )

        try:
            if self.skill_executor:
                result = await self.skill_executor.execute(
                    skill_name=skill_name,
                    variables=variables,
                    context=context,
                )
                return ToolResult(tool_name=self.name, success=True, output=str(result))
            else:
                # Return skill info if no executor configured
                return ToolResult(
                    tool_name=self.name,
                    success=True,
                    output=(
                        f"Skill: {skill.name}\n"
                        f"Description: {skill.description}\n"
                        f"Variables: {skill.variables}\n"
                        f"System prompt: {skill.system_prompt[:200]}..."
                    ),
                )
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, output="", error=str(e))
