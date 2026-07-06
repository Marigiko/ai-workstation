# AI Workstation - Agent Guidelines

## Project Overview

AI Workstation is a modular AI engineering platform for AI-assisted software development. It provides a unified interface to multiple LLM providers with intelligent routing, context management, tool execution, and comprehensive observability.

## Architecture

- **Monorepo Structure**: Single repository with multiple packages
- **Clean Architecture**: Separation of concerns with clear boundaries
- **Modular Design**: Each package is independently testable and deployable
- **Async-First**: Built on async/await patterns for high performance

## Key Technologies

- **Python 3.11+**: Core language
- **FastAPI**: Gateway API framework
- **LiteLLM**: Multi-provider LLM abstraction
- **PostgreSQL**: Conversation and session storage
- **Redis**: Caching and rate limiting
- **Qdrant**: Vector database for embeddings and memory
- **Tree-sitter**: Code parsing and analysis
- **Typer**: CLI framework
- **Pydantic**: Data validation and serialization

## Project Structure

```
ai-workstation/
├── apps/
│   ├── gateway/              # FastAPI application
│   └── cli/                  # Command-line interface
├── packages/
│   ├── contracts/            # Shared interfaces and DTOs
│   ├── conversation/         # Session management
│   ├── providers/            # LLM provider adapters
│   ├── context/              # Context engine (tree-sitter, embeddings)
│   ├── routing/              # Model routing strategies
│   ├── mcp/                  # Tool execution (MCP protocol)
│   ├── skills/               # Reusable AI skills
│   ├── memory/               # Persistent memory (Qdrant)
│   ├── evaluation/           # Response quality evaluation
│   └── observability/        # Tracing, metrics, logging
├── infrastructure/
│   ├── docker/               # Dockerfiles
│   ├── compose/              # Docker Compose configs
│   ├── deployment/           # Deployment scripts
│   └── monitoring/           # Prometheus, Grafana configs
└── docs/
    ├── architecture/         # Architecture documentation
    ├── adr/                  # Architecture Decision Records
    └── roadmap/              # Phase completion docs
```

## Development Commands

### Setup

```bash
# Install dependencies
uv sync --all-packages

# Start infrastructure (PostgreSQL, Redis, Qdrant)
docker compose -f infrastructure/compose/docker-compose.yml up -d

# Run database migrations
uv run alembic upgrade head
```

### Running Services

```bash
# Start gateway
uv run uvicorn gateway.main:app --reload --app-dir apps/gateway/src

# Use CLI
uv run ai status
uv run ai chat "Hello"
```

### Testing

```bash
# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=packages --cov=apps --cov-report=html

# Run specific package tests
uv run pytest tests/contracts/
uv run pytest tests/providers/
uv run pytest tests/routing/
```

### Code Quality

```bash
# Linting
uv run ruff check .

# Auto-fix linting issues
uv run ruff check . --fix

# Type checking
uv run mypy packages/ apps/

# Format code
uv run ruff format .
```

## Code Conventions

### Python Style

- **Line Length**: 100 characters maximum
- **Quotes**: Double quotes for strings
- **Imports**: Sorted and grouped (stdlib, third-party, local)
- **Type Hints**: Required for all function signatures
- **Docstrings**: Google-style docstrings for all public functions

### Naming Conventions

- **Variables/Functions**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private Members**: Prefix with `_`

### Package Structure

Each package follows this structure:

```
packages/<name>/
├── src/<name>/
│   ├── __init__.py          # Public API exports
│   ├── models.py            # Pydantic models
│   ├── service.py           # Business logic
│   └── <specific>.py        # Implementation files
├── tests/
│   └── test_<name>.py       # Unit tests
└── pyproject.toml           # Package dependencies
```

### Testing

- **Framework**: pytest with pytest-asyncio
- **Coverage Target**: 80% minimum
- **Test Naming**: `test_<functionality>_<scenario>`
- **Async Tests**: Use `@pytest.mark.asyncio` decorator
- **Fixtures**: Define in `conftest.py` or test files

### Error Handling

- Use custom exceptions from `contracts.exceptions`
- Always provide meaningful error messages
- Log errors with full context
- Return appropriate HTTP status codes in gateway

### API Design

- RESTful endpoints with clear naming
- Use Pydantic models for request/response validation
- Include OpenAPI documentation
- Version APIs when breaking changes are needed

## Key Patterns

### Provider Pattern

All LLM providers implement the `Provider` protocol:

```python
class Provider(Protocol):
    async def complete(self, request: CompletionRequest) -> CompletionResponse: ...
    async def stream(self, request: CompletionRequest) -> AsyncIterator[StreamChunk]: ...
    async def capabilities(self) -> ProviderCapabilities: ...
    async def health(self) -> bool: ...
```

### Router Pattern

Routing strategies implement the `Router` protocol:

```python
class Router(Protocol):
    async def resolve(self, request: CompletionRequest) -> RoutingDecision: ...
    async def report_outcome(self, decision: RoutingDecision, outcome: Outcome) -> None: ...
```

### Tool Pattern

Tools implement the `Tool` protocol:

```python
class Tool(Protocol):
    name: str
    description: str
    input_schema: dict
    
    async def execute(self, params: dict[str, Any]) -> ToolResult: ...
```

## Database Migrations

Use Alembic for database migrations:

```bash
# Create new migration
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Revert last migration
uv run alembic downgrade -1

# Check current migration
uv run alembic current
```

## Environment Variables

Required environment variables:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/ai_workstation

# Redis
REDIS_URL=redis://localhost:6379

# Qdrant
QDRANT_URL=http://localhost:6333

# LLM Providers (at least one)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...

# Gateway
DEFAULT_MODEL=gpt-4
GATEWAY_URL=http://localhost:8000
```

## Deployment

### Development

```bash
docker compose -f infrastructure/compose/docker-compose.yml up -d
```

### Production

```bash
# Use production compose file
docker compose -f infrastructure/compose/docker-compose.prod.yml up -d

# Or use deployment script
./infrastructure/deployment/deploy.sh deploy
```

## Monitoring

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)
- **Gateway Metrics**: http://localhost:8000/metrics

## Troubleshooting

### Common Issues

1. **Database connection errors**: Check PostgreSQL is running and credentials are correct
2. **Redis connection errors**: Verify Redis is accessible
3. **Qdrant errors**: Ensure Qdrant is running and collections exist
4. **LLM API errors**: Verify API keys are valid and have sufficient quota

### Logs

```bash
# Gateway logs
docker logs ai-workstation-gateway

# PostgreSQL logs
docker logs ai-workstation-postgres

# Redis logs
docker logs ai-workstation-redis

# Qdrant logs
docker logs ai-workstation-qdrant
```

## Contributing

1. Create a feature branch from `main`
2. Write tests for new functionality
3. Ensure all tests pass: `uv run pytest`
4. Ensure code passes linting: `uv run ruff check .`
5. Update documentation as needed
6. Submit a pull request with clear description

## Resources

- [Architecture Documentation](docs/architecture/ARCHITECTURE.md)
- [CLI Documentation](apps/cli/README.md)
- [How-To Guide](docs/HOW_TO.md)
- [Phase Roadmap](docs/roadmap/)
