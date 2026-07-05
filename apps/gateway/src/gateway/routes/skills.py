"""Skills endpoints for managing and executing skills."""

from fastapi import APIRouter, HTTPException
from mcp import ToolRegistry
from providers import LiteLLMProvider
from pydantic import BaseModel
from skills import (
    ALL_BUILTIN_SKILLS,
    SkillDefinition,
    SkillExecutionRequest,
    SkillExecutor,
    SkillRegistry,
)

router = APIRouter(prefix="/skills", tags=["skills"])

# Initialize registries
_skill_registry = SkillRegistry()
_tool_registry = ToolRegistry()

# Register built-in skills
for skill in ALL_BUILTIN_SKILLS:
    _skill_registry.register(skill)

# Initialize provider (will be configured via environment)
_provider = LiteLLMProvider(model="gpt-4o-mini")
_executor = SkillExecutor(_provider, _tool_registry)


class SkillListResponse(BaseModel):
    """Response for listing skills."""

    skills: list[dict]


@router.get("")
async def list_skills() -> SkillListResponse:
    """List all available skills."""
    skills = _skill_registry.list_skills()
    return SkillListResponse(
        skills=[
            {
                "name": skill.name,
                "description": skill.description,
                "variables": skill.variables,
                "tools": [t.tool_name for t in skill.tools],
                "metadata": skill.metadata,
            }
            for skill in skills
        ]
    )


@router.get("/{skill_name}")
async def get_skill(skill_name: str) -> dict:
    """Get details of a specific skill."""
    skill = _skill_registry.get(skill_name)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not found")

    return {
        "name": skill.name,
        "description": skill.description,
        "system_prompt": skill.system_prompt,
        "user_prompt_template": skill.user_prompt_template,
        "variables": skill.variables,
        "tools": [
            {"name": t.tool_name, "description": t.description, "required": t.required}
            for t in skill.tools
        ],
        "metadata": skill.metadata,
    }


@router.post("/execute")
async def execute_skill(request: SkillExecutionRequest) -> dict:
    """Execute a skill with the given parameters."""
    skill = _skill_registry.get(request.skill_name)
    if not skill:
        raise HTTPException(
            status_code=404, detail=f"Skill '{request.skill_name}' not found"
        )

    result = await _executor.execute(skill, request)

    return {
        "skill_name": result.skill_name,
        "success": result.success,
        "response": result.response,
        "tool_calls": result.tool_calls,
        "error": result.error,
        "metadata": result.metadata,
    }


@router.post("/register")
async def register_skill(skill: SkillDefinition) -> dict:
    """Register a new skill."""
    try:
        _skill_registry.register(skill)
        return {"status": "registered", "skill_name": skill.name}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{skill_name}")
async def unregister_skill(skill_name: str) -> dict:
    """Unregister a skill."""
    try:
        _skill_registry.unregister(skill_name)
        return {"status": "unregistered", "skill_name": skill_name}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
