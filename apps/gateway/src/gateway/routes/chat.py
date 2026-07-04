"""Chat endpoint."""

import json
import os

from conversation import ConversationService
from conversation.database import get_session
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from providers import LiteLLMProvider
from sqlalchemy.ext.asyncio import AsyncSession

from contracts import CompletionRequest

router = APIRouter(tags=["chat"])

_provider: LiteLLMProvider | None = None


def _get_provider() -> LiteLLMProvider:
    """Get or create the default provider."""
    global _provider
    if _provider is None:
        model = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")
        api_key = os.getenv("OPENAI_API_KEY")
        _provider = LiteLLMProvider(model=model, api_key=api_key)
    return _provider


@router.post("/chat")
async def chat(
    request: CompletionRequest,
    session_id: str | None = None,
    db: AsyncSession = Depends(get_session),
):
    """Chat completion endpoint.

    Supports both regular and streaming responses.
    If session_id is provided, conversation history is loaded and saved.
    """
    provider = _get_provider()
    conv_service = ConversationService(db)

    if session_id:
        session = await conv_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        history = await conv_service.get_history(session_id)
        request.messages = history + request.messages

    if request.stream:
        return StreamingResponse(
            _stream_response(provider, request, conv_service, session_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    try:
        response = await provider.complete(request)

        if session_id:
            for msg in request.messages:
                if msg.role.value in ["user", "system"]:
                    await conv_service.add_turn(
                        session_id=session_id,
                        role=msg.role.value,
                        content=msg.content,
                    )
            await conv_service.add_turn(
                session_id=session_id,
                role="assistant",
                content=response.content,
                model=response.model,
                provider=response.provider,
                tokens_used=response.usage.get("total_tokens"),
                latency_ms=response.latency_ms,
            )

        return response.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


async def _stream_response(
    provider: LiteLLMProvider,
    request: CompletionRequest,
    conv_service: ConversationService,
    session_id: str | None,
):
    """Generate streaming response in SSE format."""
    try:
        full_content = ""
        async for chunk in provider.stream(request):
            data = chunk.model_dump()
            full_content += chunk.delta
            yield f"data: {json.dumps(data)}\n\n"

        if session_id:
            for msg in request.messages:
                if msg.role.value in ["user", "system"]:
                    await conv_service.add_turn(
                        session_id=session_id,
                        role=msg.role.value,
                        content=msg.content,
                    )
            await conv_service.add_turn(
                session_id=session_id,
                role="assistant",
                content=full_content,
            )

        yield "data: [DONE]\n\n"
    except Exception as e:
        error_data = {"error": str(e)}
        yield f"data: {json.dumps(error_data)}\n\n"
