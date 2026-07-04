# AI Workstation

AI Engineering Platform - A modular platform for AI-assisted software development.

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- uv (recommended) or pip

### Installation

```bash
# Install uv if you don't have it
pip install uv

# Install dependencies
uv sync

# Start infrastructure
docker compose -f infrastructure/compose/docker-compose.yml up -d

# Run gateway
uv run uvicorn gateway.main:app --reload --app-dir apps/gateway/src
```

### Verify

```bash
# Health check
curl http://localhost:8000/health

# API docs
open http://localhost:8000/docs
```

## Architecture

See `docs/architecture/ARCHITECTURE.md` for full architecture documentation.

## Development

```bash
# Run tests
uv run pytest

# Run linting
uv run ruff check .

# Run type checking
uv run mypy .
```

## Project Structure

```
ai-workstation/
├── apps/
│   ├── gateway/          # FastAPI entry point
│   └── cli/              # CLI interface
├── packages/
│   ├── contracts/        # Core interfaces & DTOs
│   ├── providers/        # LLM adapters
│   ├── routing/          # Model routing
│   ├── context/          # Context engine
│   ├── memory/           # Persistent memory
│   ├── mcp/              # Tool management
│   ├── skills/           # Reusable skills
│   ├── evaluation/       # Evaluation framework
│   └── observability/    # Logs, traces, metrics
├── infrastructure/
│   └── compose/          # Docker Compose configs
└── docs/
    └── architecture/     # Architecture docs
```

## License

Private - Internal use only
