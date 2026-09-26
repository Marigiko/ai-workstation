"""FastAPI application factory."""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (4 levels up from gateway/main.py)
load_dotenv(Path(__file__).resolve().parents[4] / ".env", override=True)

from conversation import async_session_factory, close_db, init_db
from fastapi import FastAPI
from observability import ObservabilityService
from pipeline import PipelineService
from providers import OmniRouteProvider
from routing import ProviderRegistry
from routing.unified_router import UnifiedRouter
from skills import SkillRegistry
from skills.builtin import register_builtin_skills

from gateway.middleware import APIKeyMiddleware, ObservabilityMiddleware
from gateway.middleware.rate_limit import RateLimitMiddleware
from gateway.routes import (
    chat,
    context,
    evaluation,
    health,
    memory,
    observability,
    sessions,
    skills,
    tools,
)
from gateway.routes import openai as openai_routes
from gateway.routes import router as router_routes

logger = logging.getLogger(__name__)


def _create_pipeline() -> PipelineService:
    """Create and configure the pipeline service."""
    registry = ProviderRegistry()

    gateway_key = os.getenv("OMNIROUTE_API_KEY")
    if not gateway_key:
        logger.warning(
            "OMNIROUTE_API_KEY is not set; no LLM providers will be registered. "
            "All completion endpoints will fail until it is configured."
        )

    # Unified router: capability filter + cost + latency scoring
    unified_router = UnifiedRouter(
        registry,
        cost_weight=0.3,
        latency_weight=0.4,
        tier_weight=0.3,
    )
    # Set provider tiers (0=free, 1=budget, 2=standard, 3=premium)
    if gateway_key:
        models_env = os.getenv("OMNIROUTE_MODELS", "liviano,agente")
        for model in [m.strip() for m in models_env.split(",") if m.strip()]:
            provider = OmniRouteProvider(model=model)
            registry.register(provider)
            tier = 0 if model == "liviano" else 1 if model == "agente" else 2
            unified_router.set_provider_tier(provider.name, tier=tier)

    observability_service = ObservabilityService(session_factory=async_session_factory)

    return PipelineService(
        provider_registry=registry,
        agent_router=unified_router,
        observability_service=observability_service,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    await init_db()
    app.state.pipeline = _create_pipeline()

    # Register built-in skills
    app.state.skill_registry = SkillRegistry()
    register_builtin_skills(app.state.skill_registry)

    yield
    await close_db()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="AI Workstation Gateway",
        description="AI Engineering Platform - Gateway",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    observability_service = ObservabilityService(session_factory=async_session_factory)
    app.add_middleware(ObservabilityMiddleware, observability_service=observability_service)

    api_keys = os.getenv("API_KEYS", "").split(",") if os.getenv("API_KEYS") else []
    if api_keys:
        app.add_middleware(APIKeyMiddleware, api_keys=api_keys)

    rate_limit = os.getenv("RATE_LIMIT_RPM")
    if rate_limit and rate_limit.isdigit():
        app.add_middleware(RateLimitMiddleware, requests_per_minute=int(rate_limit))

    app.include_router(health.router)
    app.include_router(chat.router)
    app.include_router(openai_routes.router)
    app.include_router(sessions.router)
    app.include_router(context.router)
    app.include_router(router_routes.router)
    app.include_router(tools.router)
    app.include_router(skills.router)
    app.include_router(memory.router)
    app.include_router(evaluation.router)
    app.include_router(observability.router)

    return app


app = create_app()
