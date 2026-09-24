"""AI Workstation Contracts - Core interfaces, DTOs, and exceptions."""

__version__ = "0.1.0"

from contracts.dtos import (
    AgentModelConfig,
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
    Message,
    Outcome,
    ProjectRef,
    ProviderCapabilities,
    Role,
    RoutingDecision,
    StreamChunk,
    Tier,
    TokenBudget,
    ToolResult,
)
from contracts.exceptions import (
    ContractError,
    ProviderError,
    RoutingError,
    ToolError,
)
from contracts.interfaces import (
    ContextSource,
    EmbeddingProvider,
    Evaluator,
    MemoryStore,
    Provider,
    Router,
    Tool,
)

__all__ = [
    # DTOs
    "AgentModelConfig",
    "CompletionRequest",
    "CompletionResponse",
    "ContextChunk",
    "ContextQuery",
    "ContextResult",
    "EvalContext",
    "EvalResult",
    "IndexResult",
    "MemoryEntry",
    "MemoryScope",
    "Message",
    "Outcome",
    "ProjectRef",
    "ProviderCapabilities",
    "Role",
    "RoutingDecision",
    "StreamChunk",
    "Tier",
    "TokenBudget",
    "ToolResult",
    # Exceptions
    "ContractError",
    "ProviderError",
    "RoutingError",
    "ToolError",
    # Interfaces
    "ContextSource",
    "EmbeddingProvider",
    "Evaluator",
    "MemoryStore",
    "Provider",
    "Router",
    "Tool",
]
