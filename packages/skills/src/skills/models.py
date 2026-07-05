"""Skill models for defining reusable AI capabilities."""

from typing import Any

from pydantic import BaseModel, Field


class ToolBinding(BaseModel):
    """Binding between a skill and a tool it can use."""

    tool_name: str
    description: str = Field(description="How this tool is used in the skill")
    required: bool = Field(default=False, description="Whether this tool is required")


class SkillDefinition(BaseModel):
    """Definition of a reusable skill."""

    name: str = Field(description="Unique identifier for the skill")
    description: str = Field(description="What this skill does")
    system_prompt: str = Field(description="System prompt for the skill")
    user_prompt_template: str = Field(
        default="",
        description="Template for user prompt with {variables}",
    )
    tools: list[ToolBinding] = Field(
        default_factory=list,
        description="Tools this skill can use",
    )
    variables: list[str] = Field(
        default_factory=list,
        description="Variables that can be used in prompts",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata",
    )


class SkillExecutionRequest(BaseModel):
    """Request to execute a skill."""

    skill_name: str
    variables: dict[str, Any] = Field(
        default_factory=dict,
        description="Variable values for prompt templates",
    )
    context: str = Field(
        default="",
        description="Additional context for the skill",
    )


class SkillExecutionResult(BaseModel):
    """Result of skill execution."""

    skill_name: str
    success: bool
    response: str = Field(default="", description="LLM response")
    tool_calls: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Tool calls made during execution",
    )
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
