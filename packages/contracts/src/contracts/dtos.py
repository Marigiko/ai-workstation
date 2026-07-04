"""Data Transfer Objects for the AI Workstation platform."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

# ============================================================================
# Provider & Completion
# ============================================================================


class Role(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class Message(BaseModel):
    role: Role
    content: str
    name: str | None = None
    tool_call_id: str | None = None


class CompletionRequest(BaseModel):
    messages: list[Message]
    model: str | None = None
    provider: str | None = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, gt=0)
    stream: bool = False
    tools: list[dict[str, Any]] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CompletionResponse(BaseModel):
    id: str
    provider: str
    model: str
    content: str
    role: Role = Role.ASSISTANT
    finish_reason: str | None = None
    usage: dict[str, int] = Field(default_factory=dict)
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class StreamChunk(BaseModel):
    id: str
    provider: str
    model: str
    delta: str
    finish_reason: str | None = None
    usage: dict[str, int] = Field(default_factory=dict)


class ProviderCapabilities(BaseModel):
    provider: str
    model: str
    supports_streaming: bool = True
    supports_tools: bool = False
    supports_vision: bool = False
    max_context_tokens: int = 4096
    cost_per_1k_input_tokens: float = 0.0
    cost_per_1k_output_tokens: float = 0.0


# ============================================================================
# Context
# ============================================================================


class ProjectRef(BaseModel):
    id: str
    name: str
    path: str
    language: str | None = None


class ContextQuery(BaseModel):
    project_id: str
    query: str
    max_tokens: int = 4096
    filters: dict[str, Any] = Field(default_factory=dict)


class ContextChunk(BaseModel):
    id: str
    content: str
    source: str
    file_path: str | None = None
    line_start: int | None = None
    line_end: int | None = None
    score: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class ContextResult(BaseModel):
    chunks: list[ContextChunk]
    total_tokens: int = 0
    query_time_ms: float = 0.0


class IndexResult(BaseModel):
    project_id: str
    chunks_indexed: int
    index_time_ms: float
    status: str


# ============================================================================
# Routing
# ============================================================================


class RoutingDecision(BaseModel):
    provider: str
    model: str
    fallback_chain: list[tuple[str, str]] = Field(default_factory=list)
    estimated_cost_usd: float = 0.0
    estimated_latency_ms: float = 0.0
    strategy: str = "default"
    metadata: dict[str, Any] = Field(default_factory=dict)


class Outcome(BaseModel):
    success: bool
    latency_ms: float
    cost_usd: float
    tokens_used: int
    error: str | None = None


# ============================================================================
# Tools
# ============================================================================


class ToolResult(BaseModel):
    tool_name: str
    success: bool
    output: Any
    error: str | None = None
    execution_time_ms: float = 0.0


# ============================================================================
# Memory
# ============================================================================


class MemoryScope(StrEnum):
    GLOBAL = "global"
    PROJECT = "project"
    SESSION = "session"


class MemoryEntry(BaseModel):
    id: str
    content: str
    scope: MemoryScope
    project_id: str | None = None
    session_id: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Evaluation
# ============================================================================


class EvalContext(BaseModel):
    query: str
    expected_response: str | None = None
    context_chunks: list[ContextChunk] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvalResult(BaseModel):
    evaluator: str
    score: float
    metrics: dict[str, float] = Field(default_factory=dict)
    details: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
