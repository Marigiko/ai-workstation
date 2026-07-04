# AI Engineering Platform — Architecture Document

## 1. Vision

A modular platform where **intelligence lives in the system, not in the models**.
Models are replaceable backends. The platform provides context, routing, tools, memory, skills, evaluation, and observability.

Conceptual peers: Cursor, Claude Code, Windsurf, Devin.

---

## 2. Bounded Contexts

| Context | Responsibility | Key Entities |
|---|---|---|
| **Gateway** | Ingress, auth, rate limiting, request routing | Session, Request, AuthToken |
| **Conversation** | Chat turns, multi-turn sessions, streaming | Session, Turn, Message |
| **Context Engine** | Repo analysis, embeddings, summaries, tree-sitter | Project, Chunk, Embedding, Summary |
| **Model Router** | Provider/model selection, fallback, quotas, cost | RoutingStrategy, Quota, RoutingDecision |
| **Provider** | Unified adapter over LLM backends | Provider, Model, Completion, StreamChunk |
| **Tooling (MCP)** | Dynamic tool loading, MCP protocol | Tool, ToolRegistry, ToolCall |
| **Skills** | Reusable prompt + tool + eval bundles | Skill, SkillBinding |
| **Memory** | Persistent cross-session knowledge | MemoryEntry, MemoryScope |
| **Evaluation** | Scoring, benchmarking, regression detection | EvalSuite, EvalResult, Metric |
| **Observability** | Logs, traces, metrics, dashboard | Trace, Span, LogEntry, Metric |

---

## 3. Revised Scaffold

Deltas vs. tu propuesta original:

- `packages/core/` → **`packages/contracts/`** — solo interfaces, DTOs, exceptions compartidas. No lógica.
- `packages/workflows/` → **eliminado de fase 1**. Se reintroduce cuando haya un caso real (orquestación multi-step). YAGNI.
- `apps/dashboard/` → **diferido a fase 6+**. Empiezas con CLI + API.
- Añadido `packages/conversation/` — faltaba, y es central.

```
ai-workstation/
│
├── apps/
│   ├── gateway/              # FastAPI app — entry point principal
│   └── cli/                  # CLI para uso local
│
├── packages/
│   ├── contracts/            # Interfaces, DTOs, exceptions (ZERO logic)
│   ├── conversation/         # Sessions, turns, streaming
│   ├── providers/            # LLM adapters (built on LiteLLM)
│   ├── routing/              # Model routing strategies
│   ├── context/              # Repo analysis, tree-sitter, embeddings, repomix
│   ├── memory/               # Persistent cross-session memory
│   ├── mcp/                  # MCP manager, tool loading
│   ├── skills/               # Skill definitions + bindings
│   ├── evaluation/           # Scoring framework
│   └── observability/        # Logs, traces, metrics
│
├── infrastructure/
│   ├── docker/
│   ├── compose/
│   ├── monitoring/           # Prometheus, Grafana configs
│   └── deployment/
│
├── docs/
│   ├── architecture/
│   ├── adr/
│   └── roadmap/
│
├── examples/
└── scripts/
```

---

## 4. Key Interfaces (Contracts)

Estas son las interfaces que definen los límites del sistema. Todo el código depende de abstracciones, no de implementaciones.

### 4.1 Provider (LLM abstraction)

```python
class Provider(Protocol):
    name: str
    
    async def complete(self, request: CompletionRequest) -> CompletionResponse: ...
    async def stream(self, request: CompletionRequest) -> AsyncIterator[StreamChunk]: ...
    async def capabilities(self) -> ProviderCapabilities: ...
    async def health(self) -> bool: ...
```

**Decisión clave: construir SOBRE LiteLLM, no reemplazarlo.** LiteLLM ya soporta 100+ providers con interface unificada, retry, fallback, cost tracking. Nuestro `Provider` layer añade: health checks, capability negotiation, y un punto de extensión para providers custom (llama.cpp local).

### 4.2 ContextSource

```python
class ContextSource(Protocol):
    name: str
    
    async def gather(self, query: ContextQuery) -> ContextResult: ...
    async def index(self, project: ProjectRef) -> IndexResult: ...
    async def search(self, query: str, top_k: int) -> list[ContextChunk]: ...
```

Implementaciones: `TreeSitterSource`, `EmbeddingSource`, `RepomixSource`, `FileSource`.

### 4.3 Router

```python
class Router(Protocol):
    async def resolve(self, request: CompletionRequest) -> RoutingDecision: ...
    async def report_outcome(self, decision: RoutingDecision, outcome: Outcome) -> None: ...
```

`RoutingDecision` contiene: provider, model, fallback_chain, estimated_cost, estimated_latency.

Estrategias: `CostOptimizedRouter`, `LatencyOptimizedRouter`, `CapabilityRouter`, `RoundRobinRouter`.

### 4.4 Tool (MCP-compatible)

```python
class Tool(Protocol):
    name: str
    description: str
    input_schema: dict
    
    async def execute(self, params: dict) -> ToolResult: ...
```

### 4.5 Skill

```python
class Skill:
    name: str
    description: str
    system_prompt: str
    required_tools: list[str]
    evaluator: Evaluator | None
```

### 4.6 MemoryStore

```python
class MemoryStore(Protocol):
    async def store(self, entry: MemoryEntry) -> None: ...
    async def recall(self, query: str, scope: MemoryScope) -> list[MemoryEntry]: ...
    async def forget(self, entry_id: str) -> None: ...
```

### 4.7 Evaluator

```python
class Evaluator(Protocol):
    name: str
    
    async def evaluate(self, response: str, context: EvalContext) -> EvalResult: ...
```

Métricas: relevance, grounding, faithfulness, correctness, cost, latency, token_count.

---

## 5. Dependency Flow (Clean Architecture)

```
apps/ → packages/* → contracts/
                  ↑
         (nothing depends on apps)
```

**Regla estricta:** `contracts/` no depende de NADIE. Todos los packages dependen de `contracts/`. Los packages NO dependen entre sí directamente — se comunican via contracts o via el gateway que los orquesta.

Excepción controlada: `observability/` puede ser importado por cualquier package (cross-cutting concern), pero via una interface en `contracts/`.

---

## 6. Technology Decisions

| Layer | Choice | Rationale |
|---|---|---|
| HTTP / API | FastAPI | Async native, OpenAPI auto, Pydantic integration |
| Validation | Pydantic v2 | Fast, strict typing, JSON Schema generation |
| LLM unified layer | LiteLLM | 100+ providers, fallback, retry, cost tracking. Don't reinvent. |
| DB (metadata) | PostgreSQL | Evals, config, sessions, audit |
| ORM | SQLAlchemy 2.0 | Async, mature, typed |
| Vector DB | Qdrant | Embeddings search for context + memory |
| Cache / Queue | Redis | Caching, rate limiting, streaming pub/sub |
| Code parsing | tree-sitter | Language-agnostic AST for context extraction |
| Repo bundling | repomix | Efficient repo representation for LLM context |
| Tool protocol | MCP | Industry standard for tool interop |
| Containers | Docker + Compose | Reproducible dev + prod |
| Monitoring | OpenTelemetry → Prometheus + Grafana | Industry standard, vendor-neutral |

---

## 7. Tradeoffs

### 7.1 LiteLLM vs. custom provider layer
- **LiteLLM**: menos control, pero 100+ providers gratis, retry/fallback/cost built-in.
- **Custom**: control total, pero meses de trabajo para igualar coverage.
- **Decision**: LiteLLM como backbone. Nuestro Provider layer es un thin wrapper que añade health checks, capability negotiation, y extensibilidad para providers no soportados.

### 7.2 PostgreSQL + Qdrant + Redis (3 databases)
- **Riesgo**: complejidad operacional.
- **Justificación**: cada una resuelve un problema fundamentalmente distinto. PostgreSQL = relational metadata. Qdrant = vector similarity. Redis = hot cache + pub/sub.
- **Mitigación**: Redis es opcional en dev (fallback a in-memory). Qdrant puede arrancar en modo embedded.

### 7.3 Monorepo vs. polyrepo
- **Decision**: monorepo con packages internos.
- **Razón**: un solo equipo (tú), atomic commits across packages, shared CI.
- **Cuando separar**: si un package se convierte en servicio independiente deployable, se extrae.

### 7.4 Synchronous orchestration vs. event-driven
- **Fase 1-4**: synchronous request/response. Simple, debuggable.
- **Fase 5+**: introducir event bus (Redis Streams o similar) cuando haya background jobs reales (indexing, evals).
- **YAGNI**: no construir event bus hasta que lo necesites.

### 7.5 Dashboard timing
- **Decision**: diferido. CLI + API first.
- **Razón**: el dashboard sin backend maduro es tiempo perdido. Cuando el backend tenga 4+ fases, el dashboard se construye rápido con los endpoints existentes.

---

## 8. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Over-engineering en fase 1 | Parálisis, nunca shipping | Roadmap incremental. Cada fase debe ser usable. |
| LiteLLM breaking changes | Provider layer rota | Wrapper delgado + tests de integración por provider. |
| Context window overflow | Respuestas degradadas | Context Engine debe trackear token budget y priorizar. |
| MCP tool explosion | LLM confusion | Skills definen qué tools exponer por contexto. |
| Vendor lock-in (Qdrant) | Costo de migración | Interface `MemoryStore` + `ContextSource` permiten swap. |
| Scope creep | Nunca terminar | Fases definidas. No avanzar sin completar la anterior. |

---

## 9. Incremental Roadmap

### Phase 0 — Foundation (semana 1)
- Scaffold con estructura de paquetes
- `contracts/` con todas las interfaces base
- Docker Compose (Postgres, Redis, Qdrant)
- CI básico (lint, typecheck, test)
- Gateway skeleton (health check, OpenAPI)
- **Exit criteria**: `docker compose up` levanta infra, gateway responde `/health`

### Phase 1 — Provider + Hello LLM (semana 2)
- Provider layer sobre LiteLLM
- Un provider concreto: Claude o GPT
- Gateway endpoint `/chat` que recibe prompt y devuelve completion
- Streaming support
- **Exit criteria**: puedes enviar un prompt via curl y recibir respuesta

### Phase 2 — Conversation (semana 3)
- Session management
- Multi-turn context
- History persistence (PostgreSQL)
- **Exit criteria**: conversación multi-turn con contexto persistente

### Phase 3 — Context Engine (semanas 4-5)
- File context source
- Tree-sitter integration (Python, TypeScript)
- Repomix integration
- Embedding pipeline (Qdrant)
- Token budget management
- **Exit criteria**: el sistema puede analizar un repo y usarlo como contexto

### Phase 4 — Model Router (semana 6)
- Routing strategies (cost, latency, capability)
- Multi-provider config (2+ providers)
- Fallback chains
- Cost tracking
- **Exit criteria**: el router decide automáticamente qué modelo usar

### Phase 5 — MCP Manager (semanas 7-8)
- MCP protocol support
- Tool registry
- 3 tools iniciales: filesystem, git, shell
- Tool execution sandboxing
- **Exit criteria**: el LLM puede ejecutar tools via MCP

### Phase 6 — Skills (semana 9)
- Skill definition format
- Skill loading + binding
- 3 skills iniciales: code-review, refactor, test-generation
- **Exit criteria**: puedes invocar un skill y ejecuta prompt + tools

### Phase 7 — Memory (semana 10)
- MemoryStore implementation (Qdrant)
- Scope: project, device, global
- Recall integration in context pipeline
- **Exit criteria**: el sistema recuerda entre sesiones

### Phase 8 — Evaluation (semanas 11-12)
- Evaluator framework
- 3 evaluators: relevance, faithfulness, correctness
- Benchmark suite
- Regression detection
- **Exit criteria**: puedes evaluar respuestas automáticamente

### Phase 9 — Observability (semana 13)
- OpenTelemetry integration
- Distributed tracing
- Metrics export (Prometheus)
- Grafana dashboards
- **Exit criteria**: puedes tracear un request end-to-end

### Phase 10 — CLI + Polish (semana 14)
- CLI completa
- Config management
- Documentation
- **Exit criteria**: plataforma usable diariamente desde CLI

---

## 10. Principles (non-negotiable)

1. **Contracts first** — interfaces antes que implementaciones
2. **No circular dependencies** — dependency flow es unidireccional
3. **Every package is independently testable** — mock contracts, test logic
4. **No provider-specific logic outside providers/** — el router no sabe que Claude existe
5. **Async everywhere** — I/O nunca bloquea
6. **Strict typing** — Pydantic para datos, Protocol para interfaces
7. **Tests are not optional** — cada package tiene tests desde día 1
8. **Docker-first infra** — si no corre en compose, no existe
