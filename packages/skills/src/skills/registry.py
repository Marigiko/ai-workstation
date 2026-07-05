"""Skill registry for managing available skills."""

from skills.models import SkillDefinition


class SkillRegistry:
    """Registry for managing and retrieving skills."""

    def __init__(self):
        self._skills: dict[str, SkillDefinition] = {}

    def register(self, skill: SkillDefinition) -> None:
        """Register a new skill."""
        if skill.name in self._skills:
            raise ValueError(f"Skill '{skill.name}' already registered")
        self._skills[skill.name] = skill

    def unregister(self, name: str) -> None:
        """Unregister a skill."""
        if name not in self._skills:
            raise ValueError(f"Skill '{name}' not found")
        del self._skills[name]

    def get(self, name: str) -> SkillDefinition | None:
        """Get a skill by name."""
        return self._skills.get(name)

    def list_skills(self) -> list[SkillDefinition]:
        """List all registered skills."""
        return list(self._skills.values())

    def exists(self, name: str) -> bool:
        """Check if a skill exists."""
        return name in self._skills
