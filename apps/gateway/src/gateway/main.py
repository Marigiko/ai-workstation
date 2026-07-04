"""FastAPI application factory."""

from contextlib import asynccontextmanager

from conversation import close_db, init_db
from fastapi import FastAPI

from gateway.routes import chat, health, sessions


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

    return app


app = create_app()
