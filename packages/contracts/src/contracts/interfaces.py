"""Core interfaces (protocols) for the AI Workstation platform."""

from collections.abc import AsyncIterator
from typing import Any, Protocol, runtime_checkable

from contracts.dtos import (
    CompletionRequest,
    CompletionResponse,
    ContextChunk,
    ContextQuery,
    ContextResult,
    EvalContext,
    EvalResult,
    IndexResult,
    MemoryEntry,
    MemoryScope,
    Outcome,
    ProjectRef,
    ProviderCapabilities,
    RoutingDecision,
    StreamChunk,
    ToolResult,
)


@runtime_checkable
class Provider(Protocol):
    """LLM provider abstraction."""

    name: str

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Execute a completion request."""
        ...

    async def stream(self, request: CompletionRequest) -> AsyncIterator[StreamChunk]:
        """Execute a streaming completion request."""
        ...

    async def capabilities(self) -> ProviderCapabilities:
        """Return provider capabilities."""
        ...

    async def health(self) -> bool:
        """Check if provider is healthy."""
        ...


@runtime_checkable
class ContextSource(Protocol):
    """Context source abstraction."""

    name: str

    async def gather(self, query: ContextQuery) -> ContextResult:
        """Gather context for a query."""
        ...

    async def index(self, project: ProjectRef) -> IndexResult:
        """Index a project for context retrieval."""
        ...

    async def search(self, query: str, top_k: int = 5) -> list[ContextChunk]:
        """Search for relevant context chunks."""
        ...


@runtime_checkable
class Router(Protocol):
    """Model router abstraction."""

    async def resolve(self, request: CompletionRequest) -> RoutingDecision:
        """Decide which provider/model to use."""
        ...

    async def report_outcome(self, decision: RoutingDecision, outcome: Outcome) -> None:
        """Report the outcome of a routing decision for learning."""
        ...


@runtime_checkable
class Tool(Protocol):
    """Tool abstraction (MCP-compatible)."""

    name: str
    description: str
    input_schema: dict[str, Any]

    async def execute(self, params: dict[str, Any]) -> ToolResult:
        """Execute the tool with given parameters."""
        ...


@runtime_checkable
class MemoryStore(Protocol):
    """Memory store abstraction."""

    async def store(self, entry: MemoryEntry) -> None:
        """Store a memory entry."""
        ...

    async def recall(self, query: str, scope: MemoryScope, limit: int = 10) -> list[MemoryEntry]:
        """Recall relevant memories."""
        ...

    async def forget(self, entry_id: str) -> None:
        """Forget a specific memory."""
        ...


@runtime_checkable
class Evaluator(Protocol):
    """Evaluator abstraction."""

    name: str

    async def evaluate(self, response: str, context: EvalContext) -> EvalResult:
        """Evaluate a response against context."""
        ...
