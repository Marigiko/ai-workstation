"""OpenAI-compatible chat completions endpoint."""

import json

from conversation import ConversationService
from conversation.database import get_session
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pipeline import PipelineService
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from contracts import CompletionRequest, Message, Role

router = APIRouter(prefix="/v1", tags=["openai"])


class OpenAIChatRequest(BaseModel):
    """OpenAI-compatible chat request format."""

    model: str = "auto"
    messages: list[dict]
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int | None = None
    stream: bool = False
    tools: list[dict] | None = None


class OpenAIChatResponse(BaseModel):
    """OpenAI-compatible chat response format."""

    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[dict]
    usage: dict
    system_fingerprint: str | None = None


def _get_pipeline(request: Request) -> PipelineService:
    if not hasattr(request.app.state, "pipeline"):
        from gateway.main import _create_pipeline
        request.app.state.pipeline = _create_pipeline()
    return request.app.state.pipeline


@router.post("/chat/completions")
async def openai_chat_completions(
    request: OpenAIChatRequest,
    http_request: Request,
    session_id: str | None = None,
    project_id: str | None = None,
    db: AsyncSession = Depends(get_session),
):
    """OpenAI-compatible chat completions endpoint.

    This endpoint accepts and returns data in the exact OpenAI API format,
    making it compatible with OpenCode, Continue, Zed, and other tools.
    """
    pipeline = _get_pipeline(http_request)
    conv_service = ConversationService(db)

    messages = [
        Message(role=Role(m["role"]), content=m["content"])
        for m in request.messages
    ]

    completion_request = CompletionRequest(
        messages=messages,
        temperature=request.temperature,
        max_tokens=request.max_tokens or 2048,
        stream=request.stream,
        tools=request.tools,
    )

    if session_id:
        session = await conv_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        history = await conv_service.get_history(session_id)
        completion_request.messages = history + completion_request.messages

    if request.stream:
        stream_fn = _stream_openai_response(
            pipeline, completion_request, conv_service, session_id, project_id
        )
        return StreamingResponse(
            stream_fn,
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    try:
        result = await pipeline.execute(
            completion_request, project_id=project_id, session_id=session_id
        )

        if session_id:
            for msg in completion_request.messages:
                if msg.role.value in ["user", "system"]:
                    await conv_service.add_turn(
                        session_id=session_id,
                        role=msg.role.value,
                        content=msg.content,
                    )
            await conv_service.add_turn(
                session_id=session_id,
                role="assistant",
                content=result.response.content,
                model=result.response.model,
                provider=result.response.provider,
                tokens_used=result.response.usage.get("total_tokens"),
                latency_ms=result.response.latency_ms,
            )

        return {
            "id": result.response.id,
            "object": "chat.completion",
            "created": int(result.response.latency_ms),
            "model": result.response.model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": result.response.content,
                    },
                    "finish_reason": result.response.finish_reason or "stop",
                }
            ],
            "usage": result.response.usage,
            "system_fingerprint": result.trace_id,
            "pipeline_metadata": {
                "agent_type": result.routing_info.get("agent_type"),
                "tier_name": result.routing_info.get("tier_name"),
                "eval_scores": result.eval_scores,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


async def _stream_openai_response(
    pipeline: PipelineService,
    request: CompletionRequest,
    conv_service: ConversationService,
    session_id: str | None,
    project_id: str | None,
):
    """Stream OpenAI-compatible response."""
    try:
        stream = pipeline.execute_stream(
            request, project_id=project_id, session_id=session_id
        )
        async for event in stream:
            event_type = event["type"]
            data = event["data"]

            if event_type == "routing":
                yield f"data: {json.dumps({'type': 'routing', **data})}\n\n"
            elif event_type == "context":
                yield f"data: {json.dumps({'type': 'context', **data})}\n\n"
            elif event_type == "chunk":
                chunk_data = {
                    "id": data["id"],
                    "object": "chat.completion.chunk",
                    "created": 0,
                    "model": data["model"],
                    "choices": [
                        {
                            "index": 0,
                            "delta": {"content": data["delta"]},
                            "finish_reason": data.get("finish_reason"),
                        }
                    ],
                }
                yield f"data: {json.dumps(chunk_data)}\n\n"
            elif event_type == "eval":
                yield f"data: {json.dumps({'type': 'eval', **data})}\n\n"
            elif event_type == "done":
                yield "data: [DONE]\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"


@router.get("/models")
async def list_models(request: Request):
    """List available models in OpenAI format."""
    pipeline = _get_pipeline(request)
    providers = pipeline.provider_registry.list_providers()

    models = []
    for provider_name in providers:
        caps = await pipeline.provider_registry.get_capabilities(provider_name)
        if caps:
            models.append({
                "id": caps.model,
                "object": "model",
                "created": 0,
                "owned_by": caps.provider,
            })

    return {"object": "list", "data": models}
