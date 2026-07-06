# AI Workstation — Roadmap

> Auditoría técnica completada. Este roadmap evoluciona el proyecto desde
> "colección de componentes aislados" hasta "plataforma AI de producción".

---

## Estado actual (base línea)

- **10 paquetes** con código real y funcional
- **0 integración** entre capas — cada componente es una isla
- **/chat** bypass total del router, contexto, memoria, tools y evaluación
- **Embeddings fake** (MD5) — búsqueda semántica no funciona
- **Sin tests** de integración end-to-end
- **Sin autenticación** ni API key management

---

## Fase 1 — Core Pipeline Integration

**Objetivo:** Crear un orquestador que encadene todas las capas en un flujo coherente.

### Tareas

- [x] **1.1** ~~Crear `PipelineService` en `packages/pipeline/`~~ ✅
  - Encadena: context → memory → routing → tools → LLM → evaluation → observability
  - Archivo: `packages/pipeline/src/pipeline/service.py`
- [x] **1.2** ~~Endpoint `POST /v1/chat/completions` compatible con OpenAI API~~ ✅
  - Archivo: `apps/gateway/src/gateway/routes/openai.py`
  - Formato exacto de OpenAI para compatibilidad con OpenCode, Continue, Zed
- [x] **1.3** ~~Middleware de observability real en el gateway~~ ✅
  - Archivo: `apps/gateway/src/gateway/middleware/observability.py`
  - Tracer + metrics + logger integrados
- [x] **1.4** ~~Auth básico: API key validation middleware~~ ✅
  - Archivo: `apps/gateway/src/gateway/middleware/auth.py`
  - Validación via `X-API-Key` header o `Authorization: Bearer`
- [x] **1.5** ~~Reemplazar `/chat` actual para que use el PipelineService~~ ✅
  - Archivo: `apps/gateway/src/gateway/routes/chat.py`
  - Ahora usa el pipeline completo con context, memory, routing, evaluation
- [x] **1.6** ~~Server-Sent Events enriquecidos con metadata~~ ✅
  - Routing info (agent_type, tier_name, strategy)
  - Context info (chunks, memories)
  - Eval scores (relevance, faithfulness)

**Dependencias:** Ninguna — punto de partida
**Entregable:** Un request HTTP dispara el stack completo

---

## Fase 2 — Embeddings reales + RAG + PixelRAG

**Objetivo:** Reemplazar embeddings fake y construir un pipeline RAG funcional incluyendo búsqueda visual.

### Tareas

- [ ] **2.1** Reemplazar MD5 placeholder con embedding model real
  - Opción A: OpenAI `text-embedding-3-small` (cloud)
  - Opción B: `sentence-transformers` local (on-prem)
  - Archivo: `packages/context/src/context/embeddings/pipeline.py`
  - Archivo: `packages/memory/src/memory/qdrant_store.py`
- [ ] **2.2** Implementar `search()` en `FileSource` y `TreeSitterSource`
- [ ] **2.3** Pipeline RAG completo: chunk → embed → store → retrieve → augment → generate
- [x] **2.4** ~~PixelRAG integration~~ ✅ — contexto visual
  - Nuevo source: `packages/context/src/context/sources/visual_source.py`
  - Implementa `ContextSource` protocol
  - Conecta con `pixelrag serve` via HTTP (render + search)
  - Soporta queries por texto e imagen
  - Fallback a `pixelshot` CLI para rendering local
- [ ] **2.5** PixelRAG index builder
  - Script/endpoint para indexar documentos (web pages, PDFs) via PixelRAG
  - Integración con el pipeline de contexto existente
- [ ] **2.6** Hybrid search: combinar text embeddings + PixelRAG visual embeddings
  - Score fusion (RRF o weighted average)
  - `VisualSource` se registra como un `ContextSource` más en el pipeline

**Dependencias:** Fase 1 (para el pipeline)
**Entregable:** Búsqueda semántica real (text + visual) funcionando

---

## Fase 3 — Intelligent Routing

**Objetivo:** Routing inteligente con cascade de tokens gratuitos y routing por agente especializado.

### Tareas

- [x] **3.1** ~~Tiered Token Router~~ ✅ — cascade por consumo
  - Archivo: `packages/routing/src/routing/tiered_router.py`
  - DTOs: `Tier`, `AgentModelConfig`, `TokenBudget` en `contracts/dtos.py`
  - Cascade configurable: OpenCode free → Gemini free → Claude/OpenAI paid
  - Tracking de consumo de tokens por tier
  - Fallback automático al agotar presupuesto
  - Persistencia de consumo (Redis o DB)
- [x] **3.2** ~~Agent Router~~ ✅ — routing por tipo de tarea
  - Archivo: `packages/routing/src/routing/agent_router.py`
  - Clasificación de tareas: code, docs, planning, review, debug, test, general
  - Cada agente tiene su propio cascade de modelos optimizado
  - Configurable via `AgentConfig`
  - Keyword-based classifier (extensible)
- [x] **3.3** ~~Agent Registry~~ ✅
  - Archivo: `packages/routing/src/routing/agent_registry.py`
  - Default agents con modelos pre-configurados
  - Registro de agentes custom
  - Integración con TieredRouter
- [ ] **3.4** Cost data real
  - Reemplazar stubs `_get_cost_per_1k_*()` en `LiteLLMProvider`
  - Usar datos de LiteLLM o tabla de precios configurable
- [ ] **3.5** Latency router cold-start fix
  - New providers should start with median latency, not 0ms
- [x] **3.6** ~~Integrar routing inteligente en el PipelineService~~ ✅
  - `/chat` usa AgentRouter → TieredRouter → Provider
  - Metadata de respuesta incluye: agent_type, tier_name, strategy

**Dependencias:** Fase 1
**Entregable:** Routing que maximiza tokens gratuitos y asigna el modelo óptimo por tarea

---

## Fase 4 — Agentic Loop + MCP Real

**Objetivo:** Loop de tool execution iterativo y protocolo MCP estándar.

### Tareas

- [x] **4.1** ~~Agentic loop en Skills Executor~~ ✅
  - Iterar sobre tool calls: LLM → tool call → execute → feed result → LLM → ...
  - Max iterations configurable
  - Timeout global por skill
- [x] **4.2** ~~MCP Protocol implementation (stdio/SSE transport)~~ ✅
  - MCP server: exponer tools como MCP endpoints
  - MCP client: consumir tools de servidores MCP externos
  - Interoperabilidad con Claude Code, OpenCode, etc.
- [x] **4.3** ~~Más herramientas~~ ✅
  - Web search (SearXNG, Tavily, o similar)
  - Database query (SQL executor con sandboxing)
  - HTTP request tool (con allowlist de dominios)
- [x] **4.4** ~~Multi-step task execution~~ ✅
  - Descomponer tareas complejas en sub-tasks
  - Cada sub-task se rutea al agente especializado
  - Agregar resultados parciales

**Dependencias:** Fases 1-3
**Entregable:** Agentes que pueden usar tools iterativamente y comunicarse via MCP

---

## Fase 5 — Production Hardening

**Objetivo:** Llevar la plataforma a nivel producción.

### Tareas

- [ ] **5.1** Tests de integración end-to-end
  - Coverage target: >80%
  - Integration tests del pipeline completo
  - Contract tests para todos los protocols
- [ ] **5.2** Persistencia
  - Routing: latency history, cost tracking, token consumption (Redis/PostgreSQL)
  - Observability: OTLP export (no solo in-memory)
  - Metrics: export real a Prometheus
- [ ] **5.3** Rate limiting y quota management
  - Per-API-key rate limits
  - Token quotas por tier/usuario
  - Backpressure handling
- [ ] **5.4** Security
  - Input validation en trust boundaries
  - Sandbox mejorado para shell tool
  - Secret management (no env vars en production)
  - CORS configuration
- [ ] **5.5** Health checks y graceful degradation
  - Health check sin API calls (cache + TTL)
  - Circuit breaker pattern para providers
  - Degradación elegante cuando un componente falla
- [ ] **5.6** Docker Compose production ready
  - Gateway con todos los servicios conectados
  - Redis para caching y rate limiting
  - Health checks en compose

**Dependencias:** Fases 1-4
**Entregable:** Plataforma estable, testeada, segura

---

## Fase 6 — Frontend Integration

**Objetivo:** Cualquier frontend puede consumir la plataforma.

### Tareas

- [ ] **6.1** API OpenAI-compatible
  - `POST /v1/chat/completions` — formato exacto de OpenAI
  - `GET /v1/models` — lista de modelos disponibles
  - Compatible con: OpenCode, Continue, Zed, etc.
- [ ] **6.2** WebSocket support
  - Tool execution progress en tiempo real
  - Agent thinking/reasoning streaming
  - Multi-turn conversation updates
- [ ] **6.3** API key management multi-tenant
  - CRUD de API keys
  - Per-key quotas y rate limits
  - Usage analytics per key
- [ ] **6.4** Documentación OpenAPI completa
  - Todos los endpoints documentados
  - Ejemplos de request/response
  - Guías de integración por frontend
- [ ] **6.5** SDK cliente
  - Python SDK para consumo programático
  - TypeScript SDK para frontends web

**Dependencias:** Fases 1-5
**Entregable:** Frontend-agnostic, API estándar, SDKs

---

## Fase 7 — Advanced Features

**Objetivo:** Capacidades avanzadas de AI engineering.

### Tareas

- [ ] **7.1** Workflow Engine
  - DAG executor para multi-step tasks
  - State machine para flujos complejos
  - Visual workflow builder (optional)
- [ ] **7.2** Memory consolidation
  - Importancia y expiración de memorias
  - Summarization automática de memorias antiguas
  - Memory importance scoring
- [ ] **7.3** Adaptive routing
  - ML-based routing en vez de heurísticas
  - Learning from outcomes (reinforcement signal)
  - A/B testing de modelos
- [ ] **7.4** Multi-modal support
  - Vision (image understanding)
  - Audio (transcription + understanding)
  - Video (frame extraction + analysis)
- [ ] **7.5** Evaluation pipeline automático
  - Post-response evaluation integrada en el pipeline
  - Dashboards de calidad (Grafana)
  - Alertas de degradación de calidad
- [ ] **7.6** Cost optimization engine
  - Análisis de patrones de uso
  - Sugerencias de optimización
  - Presupuestos por proyecto/equipo

---

## Prioridades y dependencias

```
Fase 1 (Core Pipeline) ──────────────────────────────────────┐
    │                                                         │
    ├──► Fase 2 (Embeddings + RAG + PixelRAG)                │
    │                                                         │
    ├──► Fase 3 (Intelligent Routing) ◄── IMPLEMENTADA       │
    │        │                                                │
    │        └──► Fase 4 (Agentic Loop + MCP)                │
    │                                                         │
    └──► Fase 5 (Production Hardening) ◄── todas dependen    │
              │                                              │
              └──► Fase 6 (Frontend Integration)             │
                        │                                    │
                        └──► Fase 7 (Advanced) ──────────────┘
```

**Ruta crítica:** Fase 1 → Fase 3 → Fase 5

**Implementado ahora (fuera de fases):**
- TieredRouter (cascade free → paid)
- AgentRouter (routing por tipo de tarea)
- PixelRAG visual context source

---

## Métricas de éxito

| Métrica | Actual | Target Fase 5 |
|---------|--------|---------------|
| Endpoints integrados | 0/10 | 10/10 |
| Embeddings reales | No | Sí |
| Búsqueda visual (PixelRAG) | No | Sí |
| Routing inteligente | No | Sí |
| Agentes especializados | No | 7+ |
| Test coverage | ~0% | >80% |
| Latencia p95 | N/A | <2s |
| Uptime | N/A | 99.9% |
