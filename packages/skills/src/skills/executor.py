"""Skill executor for running skills with LLM and tools."""

import json
import logging
from typing import Any

from mcp import ToolRegistry
from providers import LiteLLMProvider

from contracts import CompletionRequest, Message, Role
from skills.models import (
    SkillDefinition,
    SkillExecutionRequest,
    SkillExecutionResult,
)

logger = logging.getLogger(__name__)


class SkillExecutor:
    """Executor for running skills with LLM and tools.

    Supports agentic loop: iterates tool calls until completion or max iterations.
    """

    def __init__(
        self,
        provider: LiteLLMProvider,
        tool_registry: ToolRegistry,
        max_iterations: int = 10,
    ):
        self.provider = provider
        self.tool_registry = tool_registry
        self.max_iterations = max_iterations

    def _render_prompt(self, template: str, variables: dict[str, Any]) -> str:
        """Render a prompt template with variables."""
        result = template
        for key, value in variables.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result

    def _build_tools(self, skill: SkillDefinition) -> list[dict] | None:
        """Build tool definitions for the LLM."""
        if not skill.tools:
            return None

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
        return tools if tools else None

    async def _execute_tool_call(self, tool_call: dict) -> str:
        """Execute a single tool call and return the result."""
        tool_name = tool_call.get("name")
        arguments = tool_call.get("arguments", "{}")

        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                arguments = {}

        tool = self.tool_registry.get(tool_name)
        if not tool:
            return json.dumps({"error": f"Tool {tool_name} not found"})

        try:
            result = await tool.execute(arguments)
            return json.dumps({
                "success": result.success,
                "output": result.output,
                "error": result.error,
            })
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def execute(
        self,
        skill: SkillDefinition,
        request: SkillExecutionRequest,
    ) -> SkillExecutionResult:
        """Execute a skill with the given request.

        Implements agentic loop: iterates tool calls until completion or max iterations.
        """
        try:
            system_prompt = self._render_prompt(skill.system_prompt, request.variables)
            user_prompt = self._render_prompt(skill.user_prompt_template, request.variables)

            if request.context:
                user_prompt = f"{user_prompt}\n\nContext:\n{request.context}"

            messages = [
                Message(role=Role.SYSTEM, content=system_prompt),
                Message(role=Role.USER, content=user_prompt),
            ]

            tools = self._build_tools(skill)
            all_tool_calls = []
            iteration = 0
            final_response = ""
            total_tokens = 0

            while iteration < self.max_iterations:
                iteration += 1
                logger.debug("Skill execution iteration %d/%d", iteration, self.max_iterations)

                completion_request = CompletionRequest(
                    messages=messages,
                    tools=tools,
                    temperature=0.7,
                )

                response = await self.provider.complete(completion_request)
                total_tokens += response.usage.get("total_tokens", 0)
                final_response = response.content

                tool_calls = response.metadata.get("tool_calls", [])
                if not tool_calls:
                    break

                all_tool_calls.extend(tool_calls)
                messages.append(Message(role=Role.ASSISTANT, content=response.content))

                for tool_call in tool_calls:
                    result = await self._execute_tool_call(tool_call)
                    messages.append(
                        Message(
                            role=Role.TOOL,
                            content=result,
                            tool_call_id=tool_call.get("id"),
                        )
                    )

            if iteration >= self.max_iterations:
                logger.warning("Skill reached max iterations (%d)", self.max_iterations)

            return SkillExecutionResult(
                skill_name=skill.name,
                success=True,
                response=final_response,
                tool_calls=all_tool_calls,
                metadata={
                    "model": response.model,
                    "provider": response.provider,
                    "tokens_used": total_tokens,
                    "iterations": iteration,
                },
            )

        except Exception as e:
            logger.error("Skill execution failed: %s", e, exc_info=True)
            return SkillExecutionResult(
                skill_name=skill.name,
                success=False,
                error=str(e),
            )
