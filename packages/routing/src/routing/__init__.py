"""AI Workstation Routing package."""

__version__ = "0.1.0"

from routing.base import Router
from routing.capability_router import CapabilityRouter
from routing.cost_router import CostOptimizedRouter
from routing.cost_tracker import CostTracker
from routing.fallback import FallbackRouter
from routing.latency_router import LatencyOptimizedRouter
from routing.registry import ProviderRegistry

__all__ = [
    "CapabilityRouter",
    "CostOptimizedRouter",
    "CostTracker",
    "FallbackRouter",
    "LatencyOptimizedRouter",
    "ProviderRegistry",
    "Router",
]
