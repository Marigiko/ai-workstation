"""Embedding providers for semantic memory.

Supports Ollama (local, free) and LiteLLM (OpenAI, etc.) backends.
"""

import logging
import os

logger = logging.getLogger(__name__)


class OllamaEmbeddingProvider:
    """Embedding provider using Ollama (local, free).

    Uses nomic-embed-text model (768-dim) by default.
    Requires Ollama running locally.
    """

    def __init__(
        self,
        model: str = "nomic-embed-text",
        base_url: str | None = None,
    ):
        self.model = model
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self._dimension = 768

    async def embed(self, text: str) -> list[float]:
        """Generate embedding via Ollama API."""
        import httpx

        async with httpx.AsyncClient(base_url=self.base_url, timeout=60.0) as client:
            resp = await client.post(
                "/api/embeddings",
                json={"model": self.model, "prompt": text},
            )
            resp.raise_for_status()
            return resp.json()["embedding"]

    @property
    def dimension(self) -> int:
        return self._dimension


class LiteLLMEmbeddingProvider:
    """Embedding provider using LiteLLM (OpenAI text-embedding-3-small, etc.).

    Falls back to LiteLLM when Ollama is not available.
    Requires appropriate API key (OPENAI_API_KEY, etc.).
    """

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        api_key: str | None = None,
    ):
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self._dimension = 1536  # text-embedding-3-small

    async def embed(self, text: str) -> list[float]:
        """Generate embedding via LiteLLM."""
        import litellm

        response = await litellm.aembedding(
            model=self.model,
            input=[text],
            api_key=self.api_key,
        )
        return response.data[0]["embedding"]

    @property
    def dimension(self) -> int:
        return self._dimension


def create_embedding_provider() -> OllamaEmbeddingProvider | LiteLLMEmbeddingProvider | None:
    """Factory: create best available embedding provider.

    Priority:
    1. Ollama (local, free) if reachable
    2. LiteLLM/OpenAI if OPENAI_API_KEY is set
    3. None (caller should use placeholder fallback)
    """
    # Try Ollama first (local, free)
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    try:
        import httpx

        resp = httpx.get(f"{ollama_url}/api/tags", timeout=2.0)
        if resp.status_code == 200:
            logger.info("Using Ollama embedding provider (nomic-embed-text)")
            return OllamaEmbeddingProvider(base_url=ollama_url)
    except Exception:
        logger.debug("Ollama not reachable, trying LiteLLM")

    # Fallback to LiteLLM/OpenAI
    if os.getenv("OPENAI_API_KEY"):
        logger.info("Using LiteLLM embedding provider (text-embedding-3-small)")
        return LiteLLMEmbeddingProvider()

    logger.warning(
        "No embedding provider available. Set OLLAMA_BASE_URL or OPENAI_API_KEY. "
        "Memory will use placeholder embeddings (no semantic search)."
    )
    return None


def get_embedding_status() -> dict:
    """Get current embedding provider status.

    Returns:
        Dict with keys: provider (str|None), dimension (int), semantic (bool)
    """
    provider = create_embedding_provider()
    if isinstance(provider, OllamaEmbeddingProvider):
        return {
            "provider": "ollama",
            "dimension": 768,
            "semantic": True,
            "model": "nomic-embed-text",
        }
    elif isinstance(provider, LiteLLMEmbeddingProvider):
        return {
            "provider": "litellm",
            "dimension": 1536,
            "semantic": True,
            "model": "text-embedding-3-small",
        }
    else:
        return {
            "provider": None,
            "dimension": 16,
            "semantic": False,
            "model": "placeholder-md5",
        }
