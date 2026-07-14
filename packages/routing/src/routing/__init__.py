"""AI Workstation Routing package."""

__version__ = "0.1.0"

from contracts import Router
from routing.agent_registry import AgentRegistry
from routing.agent_router import AgentRouter, classify_task
from routing.capability_router import CapabilityRouter
from routing.cost_router import CostOptimizedRouter
from routing.cost_tracker import CostTracker
from routing.fallback import FallbackRouter
from routing.latency_router import LatencyOptimizedRouter
from routing.registry import ProviderRegistry
from routing.tiered_router import TieredRouter

__all__ = [
    "AgentRegistry",
    "AgentRouter",
    "CapabilityRouter",
    "CostOptimizedRouter",
    "CostTracker",
    "FallbackRouter",
    "LatencyOptimizedRouter",
    "ProviderRegistry",
    "Router",
    "TieredRouter",
    "classify_task",
]
