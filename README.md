# AI Workstation

Una plataforma modular de ingeniería de IA para desarrollo de software asistido por IA. Construida con arquitectura limpia y principios SOLID.

## Características

- **Multi-Provider LLM**: Soporte para OpenAI, Anthropic, Google, Ollama y más via LiteLLM
- **Enrutamiento Inteligente**: Selección automática de modelos basada en costo, latencia y capacidades
- **Motor de Contexto**: Análisis de código con tree-sitter, embeddings con Qdrant
- **Gestión de Sesiones**: Conversaciones multi-turno con persistencia en PostgreSQL
- **Sistema de Herramientas (MCP)**: Ejecución segura de herramientas (filesystem, git, shell)
- **Skills Reutilizables**: Prompts especializados con herramientas integradas
- **Memoria Persistente**: Almacenamiento vectorial con Qdrant para recuperación semántica
- **Evaluación Automática**: Métricas de calidad (relevancia, grounding, faithfulness, correctness)
- **Observabilidad Completa**: Tracing distribuido, métricas Prometheus, logs estructurados
- **CLI Interactivo**: Interfaz de línea de comandos para todas las operaciones

## Requisitos Previos

- Python 3.11+
- Docker & Docker Compose
- uv (recomendado) o pip

## Instalación

```bash
# Instalar uv si no lo tienes
pip install uv

# Clonar el repositorio
git clone <repository-url>
cd ai-workstation

# Instalar dependencias
uv sync --all-packages

# Iniciar infraestructura (PostgreSQL, Redis, Qdrant)
docker compose -f infrastructure/compose/docker-compose.yml up -d

# Las tablas se crean automáticamente al iniciar el gateway
# Para migraciones futuras, usar:
uv run alembic upgrade head

# Iniciar el gateway
uv run uvicorn gateway.main:app --reload --app-dir apps/gateway/src
```

## Uso

### Verificar Instalación

```bash
# Health check
curl http://localhost:8000/health

# Documentación API interactiva
open http://localhost:8000/docs
```

### CLI (Interfaz de Línea de Comandos)

```bash
# Ver estado del gateway
ai status

# Chat con el LLM
ai chat "¿Qué es Python?"

# Gestionar sesiones
ai session create --title "Mi Proyecto"
ai session list
ai session show <session-id>

# Ejecutar herramientas
ai tools list
ai tools exec filesystem --params '{"operation": "read", "path": "/test.txt"}'

# Ejecutar skills
ai skills list
ai skills exec code-review --vars '{"code": "def test(): pass"}'

# Gestionar memoria
ai memory remember "Usuario prefiere Python" --scope global
ai memory recall "preferencias Python" --scope global

# Evaluar respuestas
ai eval run --query "¿Qué es Python?" --response "Python es un lenguaje" --metrics relevance,grounding

# Ver métricas
ai metrics
```

### API REST

#### Chat
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hola"}],
    "session_id": "opcional"
  }'
```

#### Sesiones
```bash
# Crear sesión
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{"title": "Mi Sesión"}'

# Listar sesiones
curl http://localhost:8000/sessions

# Obtener sesión
curl http://localhost:8000/sessions/<session-id>
```

#### Herramientas
```bash
# Listar herramientas
curl http://localhost:8000/tools

# Ejecutar herramienta
curl -X POST http://localhost:8000/tools/<tool-name>/execute \
  -H "Content-Type: application/json" \
  -d '{"params": {"operation": "read", "path": "/test.txt"}}'
```

#### Skills
```bash
# Listar skills
curl http://localhost:8000/skills

# Ejecutar skill
curl -X POST http://localhost:8000/skills/execute \
  -H "Content-Type: application/json" \
  -d '{
    "skill_name": "code-review",
    "variables": {"code": "def test(): pass"}
  }'
```

#### Memoria
```bash
# Guardar memoria
curl -X POST "http://localhost:8000/memory/remember?content=Usuario%20prefiere%20Python&scope=global"

# Recuperar memorias
curl -X POST "http://localhost:8000/memory/recall?query=preferencias%20Python&scope=global&limit=5"
```

#### Evaluación
```bash
curl -X POST http://localhost:8000/evaluation/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "query": "¿Qué es Python?",
    "response": "Python es un lenguaje de programación",
    "context": ["Python es un lenguaje de alto nivel"],
    "metrics": ["relevance", "grounding", "faithfulness", "correctness"]
  }'
```

#### Observabilidad
```bash
# Resumen de métricas
curl http://localhost:8000/observability/summary

# Listar traces
curl http://localhost:8000/observability/traces

# Exportar métricas Prometheus
curl http://localhost:8000/observability/metrics/prometheus
```

## Arquitectura

```
ai-workstation/
├── apps/
│   ├── gateway/              # FastAPI entry point (40+ endpoints)
│   └── cli/                  # CLI interface (Typer)
├── packages/
│   ├── contracts/            # Core interfaces & DTOs
│   ├── conversation/         # Session management (SQLAlchemy)
│   ├── providers/            # LLM adapters (LiteLLM)
│   ├── context/              # Context engine (tree-sitter, Qdrant)
│   ├── routing/              # Model routing strategies
│   ├── mcp/                  # Tool management (filesystem, git, shell)
│   ├── skills/               # Reusable skills (code-review, refactor, test-gen)
│   ├── memory/               # Persistent memory (Qdrant)
│   ├── evaluation/           # Evaluation framework (8 evaluators)
│   └── observability/        # Tracing, metrics, logging
├── infrastructure/
│   ├── compose/              # Docker Compose configs
│   └── docker/               # Dockerfiles
└── docs/
    ├── architecture/         # Architecture documentation
    └── roadmap/              # Phase completion docs
```

## Módulos

### Core
- **contracts**: Interfaces y DTOs compartidos
- **conversation**: Gestión de sesiones y turnos
- **providers**: Adaptadores para múltiples LLMs

### Intelligence
- **context**: Motor de contexto con tree-sitter y embeddings
- **routing**: Enrutamiento inteligente de modelos
- **memory**: Memoria persistente con búsqueda semántica

### Execution
- **mcp**: Sistema de herramientas (MCP protocol)
- **skills**: Skills reutilizables con prompts especializados
- **evaluation**: Framework de evaluación de calidad

### Operations
- **observability**: Tracing, métricas y logging

## Desarrollo

```bash
# Ejecutar tests
uv run pytest

# Ejecutar tests con cobertura
uv run pytest --cov=packages --cov=apps --cov-report=html

# Linting
uv run ruff check .

# Formateo automático
uv run ruff check . --fix

# Type checking
uv run mypy packages/ apps/
```

## Testing

La plataforma incluye **194 tests** con cobertura completa:

```bash
# Todos los tests
uv run pytest

# Tests por módulo
uv run pytest tests/contracts/
uv run pytest tests/providers/
uv run pytest tests/routing/
uv run pytest tests/context/
uv run pytest tests/conversation/
uv run pytest tests/mcp/
uv run pytest tests/skills/
uv run pytest tests/memory/
uv run pytest tests/evaluation/
uv run pytest tests/observability/
uv run pytest tests/cli/
uv run pytest tests/gateway/
```

## Roadmap Completado

✅ **Fase 0**: Foundation (monorepo, contracts, gateway skeleton)  
✅ **Fase 1**: Provider + Hello LLM (LiteLLM integration)  
✅ **Fase 2**: Conversation (sessions, multi-turn)  
✅ **Fase 3**: Context Engine (file, tree-sitter, embeddings)  
✅ **Fase 4**: Model Router (cost, latency, capability routing)  
✅ **Fase 5**: MCP Manager (tools registry, filesystem, git, shell)  
✅ **Fase 6**: Skills (skill definitions, execution)  
✅ **Fase 7**: Memory (Qdrant-based persistent memory)  
✅ **Fase 8**: Evaluation (8 evaluators, benchmarks)  
✅ **Fase 9**: Observability (tracing, metrics, logging)  
✅ **Fase 10**: CLI (complete command-line interface)  

## Configuración

### Variables de Entorno

```bash
# Gateway
GATEWAY_URL=http://localhost:8000

# Base de datos
DATABASE_URL=postgresql+asyncpg://ai_workstation:ai_workstation_dev@localhost:5432/ai_workstation

# Redis
REDIS_URL=redis://localhost:6379

# Qdrant
QDRANT_URL=http://localhost:6333

# Modelos (opcional)
DEFAULT_MODEL=gpt-4
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

## Estadísticas

- **194 tests passing**
- **11 packages** modulares
- **40+ endpoints REST**
- **100% linting compliance**
- **Type-safe** con mypy strict mode

## Documentación Adicional

- [Arquitectura](docs/architecture/ARCHITECTURE.md)
- [ADR-001: Monorepo Structure](docs/adr/001-monorepo-structure.md)
- [ADR-002: LiteLLM Provider Backbone](docs/adr/002-litellm-provider-backbone.md)
- [Roadmap](docs/roadmap/)

## Licencia

Privado - Solo uso interno
