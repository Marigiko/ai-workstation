"""Agent registry — maps task types to model configurations."""

from contracts import AgentModelConfig, Tier

DEFAULT_AGENTS: dict[str, AgentModelConfig] = {
    "code": AgentModelConfig(
        agent_type="code",
        tiers=[
            Tier(
                name="free",
                models=[
                    "omniroute/agente",
                    "omniroute/liviano",
                ],
                token_budget=500_000,
            ),
            Tier(
                name="paid",
                models=["omniroute/agente", "omniroute/liviano"],
                token_budget=-1,
            ),
        ],
    ),
    "docs": AgentModelConfig(
        agent_type="docs",
        tiers=[
            Tier(
                name="free",
                models=[
                    "omniroute/liviano",
                    "omniroute/agente",
                ],
                token_budget=300_000,
            ),
            Tier(
                name="paid",
                models=["omniroute/liviano", "omniroute/agente"],
                token_budget=-1,
            ),
        ],
    ),
    "planning": AgentModelConfig(
        agent_type="planning",
        tiers=[
            Tier(
                name="free",
                models=[
                    "omniroute/agente",
                    "omniroute/liviano",
                ],
                token_budget=200_000,
            ),
            Tier(
                name="paid",
                models=["omniroute/agente", "omniroute/liviano"],
                token_budget=-1,
            ),
        ],
    ),
    "review": AgentModelConfig(
        agent_type="review",
        tiers=[
            Tier(
                name="free",
                models=[
                    "omniroute/agente",
                    "omniroute/liviano",
                ],
                token_budget=200_000,
            ),
            Tier(
                name="paid",
                models=["omniroute/agente", "omniroute/liviano"],
                token_budget=-1,
            ),
        ],
    ),
    "debug": AgentModelConfig(
        agent_type="debug",
        tiers=[
            Tier(
                name="free",
                models=[
                    "omniroute/agente",
                    "omniroute/liviano",
                ],
                token_budget=300_000,
            ),
            Tier(
                name="paid",
                models=["omniroute/agente", "omniroute/liviano"],
                token_budget=-1,
            ),
        ],
    ),
    "test": AgentModelConfig(
        agent_type="test",
        tiers=[
            Tier(
                name="free",
                models=[
                    "omniroute/liviano",
                    "omniroute/agente",
                ],
                token_budget=300_000,
            ),
            Tier(
                name="paid",
                models=["omniroute/liviano", "omniroute/agente"],
                token_budget=-1,
            ),
        ],
    ),
    "general": AgentModelConfig(
        agent_type="general",
        tiers=[
            Tier(
                name="free",
                models=[
                    "omniroute/agente",
                    "omniroute/liviano",
                ],
                token_budget=500_000,
            ),
            Tier(
                name="paid",
                models=["omniroute/agente", "omniroute/liviano"],
                token_budget=-1,
            ),
        ],
    ),
}


class AgentRegistry:
    """Registry mapping agent types to their model configurations."""

    def __init__(self) -> None:
        self._configs: dict[str, AgentModelConfig] = {}
        for agent_type, config in DEFAULT_AGENTS.items():
            self._configs[agent_type] = config

    def register(self, config: AgentModelConfig) -> None:
        self._configs[config.agent_type] = config

    def get(self, agent_type: str) -> AgentModelConfig:
        return self._configs.get(agent_type, self._configs["general"])

    def list_agents(self) -> list[str]:
        return list(self._configs.keys())
