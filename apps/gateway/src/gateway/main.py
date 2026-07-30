"""FastAPI application factory."""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (4 levels up from gateway/main.py)
load_dotenv(Path(__file__).resolve().parents[4] / ".env", override=True)

from conversation import close_db, init_db
from fastapi import FastAPI
from observability import ObservabilityService
from pipeline import PipelineService
from providers import LiteLLMProvider
from routing import AgentRouter, ProviderRegistry

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


def _create_pipeline() -> PipelineService:
    """Create and configure the pipeline service."""
    registry = ProviderRegistry()

    gemini_key = os.getenv("GOOGLE_API_KEY")
    if gemini_key:
        registry.register(LiteLLMProvider(model="gemini/gemini-2.5-flash", api_key=gemini_key))

    claude_key = os.getenv("ANTHROPIC_API_KEY")
    if claude_key:
        registry.register(LiteLLMProvider(model="claude-sonnet-4-20250514", api_key=claude_key))

    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        registry.register(LiteLLMProvider(model="gpt-4o", api_key=openai_key))

    agent_router = AgentRouter(registry)
    observability_service = ObservabilityService()

    return PipelineService(
        provider_registry=registry,
        agent_router=agent_router,
        observability_service=observability_service,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    await init_db()
    app.state.pipeline = _create_pipeline()
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

    observability_service = ObservabilityService()
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
