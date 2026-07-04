"""Base provider class."""

from collections.abc import AsyncIterator

from contracts import (
    CompletionRequest,
    CompletionResponse,
    ProviderCapabilities,
    StreamChunk,
)


class BaseProvider:
    """Base class for provider implementations."""

    @property
    def name(self) -> str:
        """Provider name."""
        raise NotImplementedError

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Execute a completion request."""
        raise NotImplementedError

    async def stream(self, request: CompletionRequest) -> AsyncIterator[StreamChunk]:
        """Execute a streaming completion request."""
        raise NotImplementedError
        yield  # Make this an async generator

    async def capabilities(self) -> ProviderCapabilities:
        """Return provider capabilities."""
        raise NotImplementedError

    async def health(self) -> bool:
        """Check if provider is healthy."""
        raise NotImplementedError
