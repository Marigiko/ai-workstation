# AI Engineering Platform — Architecture Summary

## Scaffold
```
apps/ (gateway, cli)
packages/ (contracts, conversation, providers, routing, context, memory, mcp, skills, evaluation, observability)
infrastructure/ (docker, compose, monitoring, deployment)
docs/ (architecture, adr, roadmap)
```

## Key decisions
- Build ON LiteLLM, not under it (100+ providers free)
- contracts/ has ZERO logic — only interfaces, DTOs, exceptions
- packages/ don't depend on each other — communicate via contracts or gateway orchestration
- observability/ is the only cross-cutting exception
- Redis optional in dev (fallback to in-memory)
- Dashboard deferred to phase 6+
- Event bus deferred until background jobs are real (YAGNI)

## 10 key interfaces
Provider, ContextSource, Router, Tool, Skill, MemoryStore, Evaluator (see docs/architecture/ARCHITECTURE.md §4)

## Roadmap (Progress)
✓ Phase 0: Foundation (COMPLETED)
✓ Phase 1: Provider (COMPLETED)
✓ Phase 2: Conversation (COMPLETED) — SQLAlchemy async, Session/Turn models, ConversationService, /sessions endpoints, multi-turn /chat
✓ Phase 3: Context Engine (COMPLETED) — TokenBudget, FileContextSource, TreeSitterSource (Python/TS), EmbeddingPipeline (Qdrant), /context endpoints
✓ Phase 4: Model Router (COMPLETED) — ProviderRegistry, CostOptimizedRouter, LatencyOptimizedRouter, CapabilityRouter, FallbackRouter, CostTracker, /router endpoints
✓ Phase 5: MCP Manager (COMPLETED) — ToolRegistry, FilesystemTool, GitTool, ShellTool, sandboxing, /tools endpoints
✓ Phase 6: Skills (COMPLETED) — SkillDefinition, SkillRegistry, SkillExecutor, 3 built-in skills (code-review, refactor, test-generation), /skills endpoints
✓ Phase 7: Memory (COMPLETED) — QdrantMemoryStore, MemoryService, 3 scopes (global/project/session), /memory endpoints, 100/100 tests
✓ Phase 8: Evaluation (COMPLETED) — 8 evaluators (cost, latency, tokens, relevance, grounding, faithfulness, correctness, completeness), EvaluationService, benchmarks, /evaluation endpoints, 119/119 tests
✓ Phase 9: Observability (COMPLETED) — Tracer (distributed tracing), MetricsCollector (counters/gauges/histograms), StructuredLogger (JSON logs), ObservabilityService, /observability endpoints, 162/162 tests
✓ Phase 10: CLI (COMPLETED) — GatewayClient (HTTP client), Typer-based CLI with commands for chat/sessions/tools/skills/memory/eval/metrics, Rich output, 194/194 tests total
Phase 3: Context → Phase 4: Router → Phase 5: MCP → Phase 6: Skills → Phase 7: Memory → Phase 8: Eval → Phase 9: Observability → Phase 10: CLI

## Full doc
docs/architecture/ARCHITECTURE.md