"""FastAPI application factory."""

from contextlib import asynccontextmanager

from conversation import close_db, init_db
from fastapi import FastAPI

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
from gateway.routes import router as router_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    await init_db()
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

    app.include_router(health.router)
    app.include_router(chat.router)
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
