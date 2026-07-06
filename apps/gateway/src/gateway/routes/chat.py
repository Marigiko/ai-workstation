"""Chat endpoint using PipelineService."""

import json

from conversation import ConversationService
from conversation.database import get_session
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pipeline import PipelineService
from sqlalchemy.ext.asyncio import AsyncSession

from contracts import CompletionRequest

router = APIRouter(tags=["chat"])


def _get_pipeline(request: Request) -> PipelineService:
    if not hasattr(request.app.state, "pipeline"):
        from gateway.main import _create_pipeline
        request.app.state.pipeline = _create_pipeline()
    return request.app.state.pipeline


@router.post("/chat")
async def chat(
    request: CompletionRequest,
    http_request: Request,
    session_id: str | None = None,
    project_id: str | None = None,
    db: AsyncSession = Depends(get_session),
):
    """Chat completion endpoint using the full pipeline.

    Chains: context -> memory -> routing -> LLM -> evaluation -> observability.
    Supports both regular and streaming responses.
    If session_id is provided, conversation history is loaded and saved.
    """
    pipeline = _get_pipeline(http_request)
    conv_service = ConversationService(db)

    if session_id:
        session = await conv_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        history = await conv_service.get_history(session_id)
        request.messages = history + request.messages

    if request.stream:
        return StreamingResponse(
            _stream_response(pipeline, request, conv_service, session_id, project_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    try:
        result = await pipeline.execute(request, project_id=project_id, session_id=session_id)

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
                content=result.response.content,
                model=result.response.model,
                provider=result.response.provider,
                tokens_used=result.response.usage.get("total_tokens"),
                latency_ms=result.response.latency_ms,
            )

        return result.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


async def _stream_response(
    pipeline: PipelineService,
    request: CompletionRequest,
    conv_service: ConversationService,
    session_id: str | None,
    project_id: str | None,
):
    """Generate streaming response with full pipeline metadata."""
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
                yield f"data: {json.dumps(data)}\n\n"
            elif event_type == "eval":
                yield f"data: {json.dumps({'type': 'eval', **data})}\n\n"
            elif event_type == "done":
                if session_id:
                    pass
                yield "data: [DONE]\n\n"

    except Exception as e:
        error_data = {"error": str(e)}
        yield f"data: {json.dumps(error_data)}\n\n"
