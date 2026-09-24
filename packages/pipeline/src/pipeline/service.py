"""Pipeline service - orchestrates the full AI request flow."""

import logging
import time
from typing import Any

from evaluation import EvaluationService
from mcp import ToolRegistry
from memory import MemoryService
from observability import ObservabilityService
from observability.models import SpanStatus
from routing import AgentRouter, ProviderRegistry

from contracts import (
    CompletionRequest,
    CompletionResponse,
    ContextChunk,
    ContextQuery,
    EvalContext,
    MemoryScope,
    Message,
    Outcome,
    Role,
)

logger = logging.getLogger(__name__)


class PipelineResult:
    """Result from a pipeline execution."""

    def __init__(
        self,
        response: CompletionResponse,
        context_chunks: list[dict[str, Any]] | None = None,
        memories: list[dict[str, Any]] | None = None,
        routing_info: dict[str, Any] | None = None,
        eval_scores: dict[str, float] | None = None,
        trace_id: str | None = None,
    ):
        self.response = response
        self.context_chunks = context_chunks or []
        self.memories = memories or []
        self.routing_info = routing_info or {}
        self.eval_scores = eval_scores or {}
        self.trace_id = trace_id

    def to_dict(self) -> dict[str, Any]:
        result = self.response.model_dump()
        result["pipeline"] = {
            "context_chunks": len(self.context_chunks),
            "memories": len(self.memories),
            "routing": self.routing_info,
            "eval_scores": self.eval_scores,
            "trace_id": self.trace_id,
        }
        return result


class PipelineService:
    """Orchestrates the full AI request flow.

    Chains: context -> memory -> routing -> tools -> LLM -> evaluation -> observability
    """

    def __init__(
        self,
        provider_registry: ProviderRegistry,
        agent_router: AgentRouter,
        context_sources: list | None = None,
        memory_service: MemoryService | None = None,
        tool_registry: ToolRegistry | None = None,
        evaluation_service: EvaluationService | None = None,
        observability_service: ObservabilityService | None = None,
        auto_recall: bool = True,
    ):
        self.provider_registry = provider_registry
        self.agent_router = agent_router
        self.context_sources = context_sources or []
        self.memory_service = memory_service
        self.tool_registry = tool_registry
        self.evaluation_service = evaluation_service
        self.observability_service = observability_service
        self.auto_recall = auto_recall

    async def _gather_context(
        self, query: str, project_id: str | None = None, max_tokens: int = 4096
    ) -> list[dict[str, Any]]:
        if not self.context_sources or not project_id:
            return []

        context_query = ContextQuery(
            project_id=project_id or "default",
            query=query,
            max_tokens=max_tokens,
        )

        all_chunks = []
        for source in self.context_sources:
            try:
                result = await source.gather(context_query)
                for chunk in result.chunks:
                    all_chunks.append({
                        "content": chunk.content,
                        "source": chunk.source,
                        "score": chunk.score,
                    })
            except Exception as e:
                logger.warning("Context source %s failed: %s", source.name, e)

        return all_chunks

    async def _recall_memories(
        self, query: str, project_id: str | None = None, session_id: str | None = None
    ) -> list[dict[str, Any]]:
        if not self.memory_service:
            return []

        memories = []

        try:
            global_memories = await self.memory_service.recall_memories(
                query=query, scope=MemoryScope.GLOBAL, limit=3
            )
            memories.extend([
                {"content": m.content, "scope": "global"} for m in global_memories
            ])
        except Exception as e:
            logger.warning("Global memory recall failed: %s", e)

        if project_id:
            try:
                project_memories = await self.memory_service.recall_memories(
                    query=query,
                    scope=MemoryScope.PROJECT,
                    project_id=project_id,
                    limit=3,
                )
                memories.extend([
                    {"content": m.content, "scope": "project"} for m in project_memories
                ])
            except Exception as e:
                logger.warning("Project memory recall failed: %s", e)

        if session_id:
            try:
                session_memories = await self.memory_service.recall_memories(
                    query=query,
                    scope=MemoryScope.SESSION,
                    session_id=session_id,
                    limit=3,
                )
                memories.extend([
                    {"content": m.content, "scope": "session"} for m in session_memories
                ])
            except Exception as e:
                logger.warning("Session memory recall failed: %s", e)

        return memories

    def _augment_messages(
        self,
        messages: list[Message],
        context_chunks: list[dict[str, Any]],
        memories: list[dict[str, Any]],
    ) -> list[Message]:
        augmented = []

        context_text = ""
        if context_chunks:
            context_text += "\n\nRelevant context:\n"
            for i, chunk in enumerate(context_chunks[:5]):
                context_text += f"[{i+1}] {chunk['content'][:500]}\n"

        if memories:
            context_text += "\n\nRelevant memories:\n"
            for i, mem in enumerate(memories[:5]):
                context_text += f"[{i+1}] ({mem['scope']}) {mem['content'][:300]}\n"

        if context_text:
            augmented.append(
                Message(role=Role.SYSTEM, content=f"Context information:{context_text}")
            )

        augmented.extend(messages)
        return augmented

    async def _evaluate_response(
        self, query: str, response: str, context_chunks: list[dict[str, Any]]
    ) -> dict[str, float]:
        if not self.evaluation_service:
            return {}

        try:
            eval_context = EvalContext(
                query=query,
                context_chunks=[
                    ContextChunk(
                        id=str(i),
                        content=c["content"],
                        source=c.get("source", "unknown"),
                    )
                    for i, c in enumerate(context_chunks)
                ],
            )

            results = await self.evaluation_service.evaluate(
                query=query,
                response=response,
                context=eval_context,
                metrics=["relevance", "faithfulness"],
            )

            return {r.evaluator: r.score for r in results}
        except Exception as e:
            logger.warning("Evaluation failed: %s", e)
            return {}

    async def execute(
        self,
        request: CompletionRequest,
        project_id: str | None = None,
        session_id: str | None = None,
        auto_recall: bool | None = None,
    ) -> PipelineResult:
        """Execute the pipeline.

        Args:
            request: Completion request
            project_id: Optional project ID
            session_id: Optional session ID
            auto_recall: Override instance auto_recall setting for this request.
                If None, uses self.auto_recall (default True).
        """
        start_time = time.time()
        trace_id = None

        if self.observability_service:
            trace_id = self.observability_service.start_request(operation="pipeline.execute")

        try:
            query = " ".join(m.content for m in request.messages[-3:])

            # Auto-recall: gather context and memories unless disabled
            should_recall = auto_recall if auto_recall is not None else self.auto_recall
            if should_recall:
                context_chunks = await self._gather_context(query, project_id)
                memories = await self._recall_memories(query, project_id, session_id)
            else:
                context_chunks = []
                memories = []

            augmented_messages = self._augment_messages(
                request.messages, context_chunks, memories
            )
            augmented_request = request.model_copy()
            augmented_request.messages = augmented_messages

            decision = await self.agent_router.resolve(augmented_request)
            provider = self.provider_registry.get(decision.provider)
            if not provider:
                raise RuntimeError(f"Provider {decision.provider} not found")

            response = await provider.complete(augmented_request)

            await self.agent_router.report_outcome(
                decision,
                Outcome(
                    success=True,
                    latency_ms=response.latency_ms,
                    cost_usd=response.cost_usd,
                    tokens_used=response.usage.get("total_tokens", 0),
                ),
            )

            eval_scores = await self._evaluate_response(
                query, response.content, context_chunks
            )

            if self.observability_service and trace_id:
                await self.observability_service.end_request(
                    trace_id=trace_id, status=SpanStatus.OK
                )

            latency_ms = (time.time() - start_time) * 1000
            logger.info(
                "Pipeline completed in %.0fms | agent=%s | tier=%s | model=%s",
                latency_ms,
                decision.metadata.get("agent_type"),
                decision.metadata.get("tier_name"),
                response.model,
            )

            return PipelineResult(
                response=response,
                context_chunks=context_chunks,
                memories=memories,
                routing_info={
                    "agent_type": decision.metadata.get("agent_type"),
                    "tier_name": decision.metadata.get("tier_name"),
                    "strategy": decision.strategy,
                    "provider": decision.provider,
                    "model": decision.model,
                },
                eval_scores=eval_scores,
                trace_id=trace_id,
            )

        except Exception as e:
            logger.error("Pipeline execution failed: %s", e, exc_info=True)
            if self.observability_service and trace_id:
                await self.observability_service.end_request(
                    trace_id=trace_id,
                    status=SpanStatus.ERROR,
                    attributes={"error": str(e)},
                )
            raise

    async def execute_stream(
        self,
        request: CompletionRequest,
        project_id: str | None = None,
        session_id: str | None = None,
    ):
        query = " ".join(m.content for m in request.messages[-3:])

        # Auto-recall: gather context and memories unless disabled
        if self.auto_recall:
            context_chunks = await self._gather_context(query, project_id)
            memories = await self._recall_memories(query, project_id, session_id)
        else:
            context_chunks = []
            memories = []

        augmented_messages = self._augment_messages(
            request.messages, context_chunks, memories
        )
        augmented_request = request.model_copy()
        augmented_request.messages = augmented_messages

        decision = await self.agent_router.resolve(augmented_request)
        provider = self.provider_registry.get(decision.provider)
        if not provider:
            raise RuntimeError(f"Provider {decision.provider} not found")

        routing_info = {
            "agent_type": decision.metadata.get("agent_type"),
            "tier_name": decision.metadata.get("tier_name"),
            "strategy": decision.strategy,
            "provider": decision.provider,
            "model": decision.model,
        }

        yield {"type": "routing", "data": routing_info}
        yield {
            "type": "context",
            "data": {"chunks": len(context_chunks), "memories": len(memories)},
        }

        full_content = ""
        async for chunk in provider.stream(augmented_request):
            full_content += chunk.delta
            yield {"type": "chunk", "data": chunk.model_dump()}

        eval_scores = await self._evaluate_response(query, full_content, context_chunks)
        yield {"type": "eval", "data": eval_scores}
        yield {"type": "done", "data": {}}
