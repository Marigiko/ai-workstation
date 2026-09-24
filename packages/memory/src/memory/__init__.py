"""Memory package for persistent cross-session memory."""

from memory.embedding import (
    LiteLLMEmbeddingProvider,
    OllamaEmbeddingProvider,
    create_embedding_provider,
)
from memory.qdrant_store import QdrantMemoryStore
from memory.service import MemoryService

__version__ = "0.1.0"

__all__ = [
    "MemoryService",
    "QdrantMemoryStore",
    "OllamaEmbeddingProvider",
    "LiteLLMEmbeddingProvider",
    "create_embedding_provider",
]
