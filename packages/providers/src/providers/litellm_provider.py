"""LiteLLM-based provider implementation."""

import time
import uuid
from collections.abc import AsyncIterator

from litellm import acompletion

from contracts import (
    CompletionRequest,
    CompletionResponse,
    ProviderCapabilities,
    ProviderError,
    Role,
    StreamChunk,
)
from providers.base import BaseProvider


class LiteLLMProvider(BaseProvider):
    """Provider implementation using LiteLLM."""

    def __init__(self, model: str, api_key: str | None = None, **kwargs):
        """Initialize LiteLLM provider.

        Args:
            model: Model identifier (e.g., "gpt-4", "claude-3-opus-20240229")
            api_key: API key for the provider
            **kwargs: Additional LiteLLM parameters
        """
        self._model = model
        self._api_key = api_key
        self._kwargs = kwargs
        self._name = self._extract_provider_name(model)

    def _extract_provider_name(self, model: str) -> str:
        """Extract provider name from model identifier."""
        if "/" in model:
            return model.split("/")[0]
        if model.startswith("gpt-"):
            return "openai"
        if model.startswith("claude-"):
            return "anthropic"
        if model.startswith("gemini-"):
            return "gemini"
        return "unknown"

    @property
    def name(self) -> str:
        return self._name

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Execute a completion request."""
        start_time = time.time()

        try:
            messages = [
                {"role": msg.role.value, "content": msg.content}
                for msg in request.messages
            ]

            kwargs = {
                "model": self._model,
                "messages": messages,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "stream": False,
            }

            if self._api_key:
                kwargs["api_key"] = self._api_key

            kwargs.update(self._kwargs)

            if request.tools:
                kwargs["tools"] = request.tools

            response = await acompletion(**kwargs)

            latency_ms = (time.time() - start_time) * 1000

            choice = response.choices[0]
            usage = {}
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }

            return CompletionResponse(
                id=response.id or str(uuid.uuid4()),
                provider=self._name,
                model=self._model,
                content=choice.message.content or "",
                role=Role.ASSISTANT,
                finish_reason=choice.finish_reason,
                usage=usage,
                latency_ms=latency_ms,
                cost_usd=getattr(response, "_hidden_params", {}).get("response_cost", 0.0) or 0.0,
                metadata={"model": self._model},
            )

        except Exception as e:
            raise ProviderError(self._name, str(e), e) from e

    async def stream(self, request: CompletionRequest) -> AsyncIterator[StreamChunk]:
        """Execute a streaming completion request."""
        try:
            messages = [
                {"role": msg.role.value, "content": msg.content}
                for msg in request.messages
            ]

            kwargs = {
                "model": self._model,
                "messages": messages,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "stream": True,
            }

            if self._api_key:
                kwargs["api_key"] = self._api_key

            kwargs.update(self._kwargs)

            if request.tools:
                kwargs["tools"] = request.tools

            response = await acompletion(**kwargs)

            chunk_id = str(uuid.uuid4())

            async for chunk in response:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta and delta.content:
                        yield StreamChunk(
                            id=chunk_id,
                            provider=self._name,
                            model=self._model,
                            delta=delta.content,
                            finish_reason=chunk.choices[0].finish_reason,
                        )

        except Exception as e:
            raise ProviderError(self._name, str(e), e) from e

    async def capabilities(self) -> ProviderCapabilities:
        """Return provider capabilities."""
        return ProviderCapabilities(
            provider=self._name,
            model=self._model,
            supports_streaming=True,
            supports_tools=self._model.startswith("gpt-") or self._model.startswith("claude-"),
            supports_vision="vision" in self._model.lower() or "gpt-4" in self._model,
            max_context_tokens=self._get_max_context_tokens(),
            cost_per_1k_input_tokens=self._get_cost_per_1k_input_tokens(),
            cost_per_1k_output_tokens=self._get_cost_per_1k_output_tokens(),
        )

    def _get_max_context_tokens(self) -> int:
        """Get max context tokens for model."""
        if "gpt-4" in self._model:
            return 128000
        if "gpt-3.5" in self._model:
            return 16385
        if "claude-3" in self._model:
            return 200000
        if "claude-2" in self._model:
            return 100000
        return 4096

    def _get_cost_per_1k_input_tokens(self) -> float:
        """Get cost per 1K input tokens (placeholder)."""
        return 0.0

    def _get_cost_per_1k_output_tokens(self) -> float:
        """Get cost per 1K output tokens (placeholder)."""
        return 0.0

    async def health(self) -> bool:
        """Check if provider is healthy."""
        try:
            from contracts import Message
            test_request = CompletionRequest(
                messages=[Message(role=Role.USER, content="Hi")],
                max_tokens=5,
            )
            await self.complete(test_request)
            return True
        except Exception:
            return False
