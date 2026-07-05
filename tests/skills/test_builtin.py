"""Tests for built-in skills."""

from skills import (
    ALL_BUILTIN_SKILLS,
    CODE_REVIEW_SKILL,
    REFACTOR_SKILL,
    TEST_GENERATION_SKILL,
)


def test_code_review_skill():
    """Test code review skill definition."""
    assert CODE_REVIEW_SKILL.name == "code-review"
    assert CODE_REVIEW_SKILL.description
    assert CODE_REVIEW_SKILL.system_prompt
    assert "{code}" in CODE_REVIEW_SKILL.user_prompt_template
    assert "code" in CODE_REVIEW_SKILL.variables
    assert len(CODE_REVIEW_SKILL.tools) > 0


def test_refactor_skill():
    """Test refactor skill definition."""
    assert REFACTOR_SKILL.name == "refactor"
    assert REFACTOR_SKILL.description
    assert REFACTOR_SKILL.system_prompt
    assert "{code}" in REFACTOR_SKILL.user_prompt_template
    assert "{goals}" in REFACTOR_SKILL.user_prompt_template
    assert "code" in REFACTOR_SKILL.variables
    assert "goals" in REFACTOR_SKILL.variables


def test_test_generation_skill():
    """Test test generation skill definition."""
    assert TEST_GENERATION_SKILL.name == "test-generation"
    assert TEST_GENERATION_SKILL.description
    assert TEST_GENERATION_SKILL.system_prompt
    assert "{code}" in TEST_GENERATION_SKILL.user_prompt_template
    assert "{framework}" in TEST_GENERATION_SKILL.user_prompt_template
    assert "code" in TEST_GENERATION_SKILL.variables
    assert "framework" in TEST_GENERATION_SKILL.variables


def test_all_builtin_skills():
    """Test that all built-in skills are included."""
    assert len(ALL_BUILTIN_SKILLS) == 3
    skill_names = [s.name for s in ALL_BUILTIN_SKILLS]
    assert "code-review" in skill_names
    assert "refactor" in skill_names
    assert "test-generation" in skill_names


def test_skill_metadata():
    """Test that skills have proper metadata."""
    for skill in ALL_BUILTIN_SKILLS:
        assert skill.metadata
        assert "category" in skill.metadata
        assert "complexity" in skill.metadata
