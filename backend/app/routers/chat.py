import json
import logging

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.conversation import Conversation, Message
from ..services.pipeline import run_pipeline

logger = logging.getLogger(__name__)

router = APIRouter()


async def _pipeline_sse_generator(
    conversation_id: str,
    text: str,
    images: list[UploadFile],
    session: AsyncSession,
):
    """Run the real prediction pipeline and yield SSE events, persisting messages."""

    # Validate conversation exists
    conv = await session.get(Conversation, conversation_id)
    if not conv:
        yield f"event: error\ndata: {json.dumps({'message': 'Conversation not found'})}\n\n"
        return

    # Save user message
    user_msg = Message(
        conversation_id=conversation_id,
        role="user",
        content_text=text,
        message_type="text",
    )
    session.add(user_msg)
    await session.commit()

    # Update conversation title from first message if still default
    if conv.title in ("New Analysis", ""):
        conv.title = text[:80] + ("..." if len(text) > 80 else "")
        await session.commit()

    # Read image files (for future vision processing)
    image_files = []
    for img in images:
        content = await img.read()
        image_files.append({"filename": img.filename, "content": content, "content_type": img.content_type})

    # Run the pipeline, forwarding SSE events
    assistant_text = None
    prediction_data = None
    parsing_data = None
    search_data = None

    async for sse_event in run_pipeline(text, conversation_id, image_files):
        yield sse_event

        # Capture output for persistence
        if sse_event.startswith("event: chat_response\n"):
            try:
                data_line = sse_event.split("data: ", 1)[1].strip()
                parsed = json.loads(data_line)
                assistant_text = parsed.get("message", "")
            except (IndexError, json.JSONDecodeError):
                pass
        elif sse_event.startswith("event: parsing_complete\n"):
            try:
                data_line = sse_event.split("data: ", 1)[1].strip()
                parsing_data = json.loads(data_line)
            except (IndexError, json.JSONDecodeError):
                pass
        elif sse_event.startswith("event: search_complete\n"):
            try:
                data_line = sse_event.split("data: ", 1)[1].strip()
                search_data = json.loads(data_line)
            except (IndexError, json.JSONDecodeError):
                pass
        elif sse_event.startswith("event: prediction\n"):
            try:
                data_line = sse_event.split("data: ", 1)[1].strip()
                prediction_data = json.loads(data_line)
            except (IndexError, json.JSONDecodeError):
                pass

    # Save assistant response
    if assistant_text:
        assistant_msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content_text=assistant_text,
            content_structured=None,
            message_type="text",
        )
        session.add(assistant_msg)
        await session.commit()
    elif prediction_data:
        # Embed thinking data alongside prediction for reload persistence
        structured = dict(prediction_data)
        if parsing_data:
            structured["_thinking_parsed_profile"] = parsing_data
        if search_data:
            structured["_thinking_search_result"] = search_data
        assistant_msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content_text=None,
            content_structured=json.dumps(structured),
            message_type="prediction",
        )
        session.add(assistant_msg)
        await session.commit()


@router.post("")
async def chat(
    conversation_id: str = Form(...),
    text: str = Form(...),
    images: list[UploadFile] = File(default=[]),
    session: AsyncSession = Depends(get_db),
):
    return StreamingResponse(
        _pipeline_sse_generator(conversation_id, text, images, session),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
