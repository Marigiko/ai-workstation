"""Skill executor for running skills with LLM and tools."""

from typing import Any

from mcp import ToolRegistry
from providers import LiteLLMProvider

from contracts import CompletionRequest, Message, Role
from skills.models import (
    SkillDefinition,
    SkillExecutionRequest,
    SkillExecutionResult,
)


class SkillExecutor:
    """Executor for running skills with LLM and tools."""

    def __init__(self, provider: LiteLLMProvider, tool_registry: ToolRegistry):
        self.provider = provider
        self.tool_registry = tool_registry

    def _render_prompt(self, template: str, variables: dict[str, Any]) -> str:
        """Render a prompt template with variables."""
        result = template
        for key, value in variables.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result

    async def execute(
        self,
        skill: SkillDefinition,
        request: SkillExecutionRequest,
    ) -> SkillExecutionResult:
        """Execute a skill with the given request."""
        try:
            # Render prompts
            system_prompt = self._render_prompt(skill.system_prompt, request.variables)
            user_prompt = self._render_prompt(skill.user_prompt_template, request.variables)

            if request.context:
                user_prompt = f"{user_prompt}\n\nContext:\n{request.context}"

            # Build messages
            messages = [
                Message(role=Role.SYSTEM, content=system_prompt),
                Message(role=Role.USER, content=user_prompt),
            ]

            # Prepare tools if skill has tool bindings
            tools = None
            if skill.tools:
                tools = []
                for tool_binding in skill.tools:
                    tool = self.tool_registry.get(tool_binding.tool_name)
                    if tool:
                        tools.append(
                            {
                                "type": "function",
                                "function": {
                                    "name": tool.name,
                                    "description": tool.description,
                                    "parameters": tool.input_schema,
                                },
                            }
                        )

            # Create completion request
            completion_request = CompletionRequest(
                messages=messages,
                tools=tools,
                temperature=0.7,
            )

            # Execute with provider
            response = await self.provider.complete(completion_request)

            # Track tool calls if any
            tool_calls = []
            if response.metadata.get("tool_calls"):
                tool_calls = response.metadata["tool_calls"]

            return SkillExecutionResult(
                skill_name=skill.name,
                success=True,
                response=response.content,
                tool_calls=tool_calls,
                metadata={
                    "model": response.model,
                    "provider": response.provider,
                    "tokens_used": response.usage.get("total_tokens", 0),
                },
            )

        except Exception as e:
            return SkillExecutionResult(
                skill_name=skill.name,
                success=False,
                error=str(e),
            )
