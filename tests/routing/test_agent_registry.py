"""Tests for agent registry."""

from routing import AgentRegistry

from contracts import AgentModelConfig, Tier


def test_default_agents_loaded():
    registry = AgentRegistry()
    agents = registry.list_agents()
    assert "code" in agents
    assert "docs" in agents
    assert "planning" in agents
    assert "review" in agents
    assert "debug" in agents
    assert "test" in agents
    assert "general" in agents


def test_get_known_agent():
    registry = AgentRegistry()
    config = registry.get("code")
    assert config.agent_type == "code"
    assert len(config.tiers) > 0
    assert config.tiers[0].name == "free"


def test_get_unknown_returns_general():
    registry = AgentRegistry()
    config = registry.get("nonexistent")
    assert config.agent_type == "general"


def test_register_custom_agent():
    registry = AgentRegistry()
    custom = AgentModelConfig(
        agent_type="custom",
        tiers=[Tier(name="free", models=["gemini/flash"], token_budget=1000)],
    )
    registry.register(custom)
    assert "custom" in registry.list_agents()
    assert registry.get("custom").agent_type == "custom"


def test_agent_tiers_have_models():
    registry = AgentRegistry()
    for agent_type in registry.list_agents():
        config = registry.get(agent_type)
        for tier in config.tiers:
            assert len(tier.models) > 0
