"""Router endpoints."""

from fastapi import APIRouter, HTTPException
from providers import OmniRouteProvider
from routing import (
    CapabilityRouter,
    CostOptimizedRouter,
    CostTracker,
    FallbackRouter,
    LatencyOptimizedRouter,
    ProviderRegistry,
)

from contracts import CompletionRequest

router = APIRouter(prefix="/router", tags=["router"])

_registry = ProviderRegistry()
_cost_tracker = CostTracker()
_fallback_router: FallbackRouter | None = None


def _get_fallback_router(strategy: str = "cost") -> FallbackRouter:
    """Get or create fallback router with specified strategy."""
    global _fallback_router

    if strategy == "cost":
        base_router = CostOptimizedRouter(_registry)
    elif strategy == "latency":
        base_router = LatencyOptimizedRouter(_registry)
    elif strategy == "capability":
        base_router = CapabilityRouter(_registry)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown strategy: {strategy}")

    return FallbackRouter(_registry, base_router)


@router.post("/register")
async def register_provider(
    name: str,
    model: str,
):
    """Register a provider (gateway credentials come from the environment)."""
    provider = OmniRouteProvider(model=model)
    _registry.register(provider)
    return {"registered": name, "model": model}


@router.get("/providers")
async def list_providers():
    """List registered providers."""
    return {"providers": _registry.list_providers()}


@router.get("/providers/{name}/capabilities")
async def get_provider_capabilities(name: str):
    """Get capabilities for a provider."""
    caps = await _registry.get_capabilities(name)
    if not caps:
        raise HTTPException(status_code=404, detail="Provider not found")
    return caps.model_dump()


@router.get("/health")
async def check_health():
    """Check health of all providers."""
    results = await _registry.health_check_all()
    return results


@router.post("/resolve")
async def resolve_model(request: CompletionRequest, strategy: str = "cost"):
    """Resolve which model to use for a request."""
    fallback_router = _get_fallback_router(strategy)
    decision = await fallback_router.base_router.resolve(request)
    return decision.model_dump()


@router.post("/execute")
async def execute_with_routing(request: CompletionRequest, strategy: str = "cost"):
    """Execute request with routing and fallback."""
    fallback_router = _get_fallback_router(strategy)

    try:
        response = await fallback_router.execute(request)

        # Track cost
        _cost_tracker.record(
            provider=response.provider,
            model=response.model,
            cost_usd=response.cost_usd,
            tokens_used=response.usage.get("total_tokens", 0),
        )

        return response.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/costs")
async def get_costs(provider: str | None = None):
    """Get cost summary."""
    return {
        "total_cost_usd": _cost_tracker.total_cost(provider),
        "total_tokens": _cost_tracker.total_tokens(provider),
        "records": [
            {
                "provider": r.provider,
                "model": r.model,
                "cost_usd": r.cost_usd,
                "tokens_used": r.tokens_used,
                "timestamp": r.timestamp.isoformat(),
            }
            for r in _cost_tracker.get_records()
        ],
    }
