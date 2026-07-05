"""Tests for SkillRegistry."""

import pytest
from skills import SkillDefinition, SkillRegistry


@pytest.fixture
def registry():
    """Create a fresh skill registry."""
    return SkillRegistry()


@pytest.fixture
def sample_skill():
    """Create a sample skill for testing."""
    return SkillDefinition(
        name="test-skill",
        description="A test skill",
        system_prompt="You are a test assistant.",
        user_prompt_template="Process this: {input}",
        variables=["input"],
    )


def test_register_skill(registry, sample_skill):
    """Test registering a skill."""
    registry.register(sample_skill)
    assert registry.exists("test-skill")
    assert registry.get("test-skill") == sample_skill


def test_register_duplicate_skill(registry, sample_skill):
    """Test that registering a duplicate skill raises an error."""
    registry.register(sample_skill)
    with pytest.raises(ValueError, match="already registered"):
        registry.register(sample_skill)


def test_unregister_skill(registry, sample_skill):
    """Test unregistering a skill."""
    registry.register(sample_skill)
    registry.unregister("test-skill")
    assert not registry.exists("test-skill")


def test_unregister_nonexistent_skill(registry):
    """Test that unregistering a nonexistent skill raises an error."""
    with pytest.raises(ValueError, match="not found"):
        registry.unregister("nonexistent")


def test_get_nonexistent_skill(registry):
    """Test getting a nonexistent skill returns None."""
    assert registry.get("nonexistent") is None


def test_list_skills(registry, sample_skill):
    """Test listing all skills."""
    registry.register(sample_skill)
    skills = registry.list_skills()
    assert len(skills) == 1
    assert skills[0] == sample_skill


def test_list_empty_skills(registry):
    """Test listing skills when registry is empty."""
    skills = registry.list_skills()
    assert len(skills) == 0
