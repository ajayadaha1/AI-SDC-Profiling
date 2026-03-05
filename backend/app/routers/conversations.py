from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models.conversation import Conversation, Message
from ..schemas.conversation import ConversationCreate, ConversationDetail, ConversationSummary, MessageOut

router = APIRouter()


@router.get("", response_model=list[ConversationSummary])
async def list_conversations(
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Conversation)
        .order_by(Conversation.updated_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(stmt)
    conversations = result.scalars().all()

    out = []
    for conv in conversations:
        # Get message count
        count_stmt = select(func.count()).where(Message.conversation_id == conv.id)
        count_result = await session.execute(count_stmt)
        msg_count = count_result.scalar() or 0

        # Get last message preview
        last_msg_stmt = (
            select(Message)
            .where(Message.conversation_id == conv.id, Message.role == "user")
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        last_msg_result = await session.execute(last_msg_stmt)
        last_msg = last_msg_result.scalar_one_or_none()

        preview = None
        if last_msg and last_msg.content_text:
            preview = last_msg.content_text[:100]

        out.append(
            ConversationSummary(
                id=conv.id,
                title=conv.title,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                message_count=msg_count,
                last_message_preview=preview,
            )
        )

    return out


@router.post("", response_model=ConversationSummary)
async def create_conversation(
    body: ConversationCreate,
    session: AsyncSession = Depends(get_db),
):
    conv = Conversation(title=body.title)
    session.add(conv)
    await session.commit()
    await session.refresh(conv)

    return ConversationSummary(
        id=conv.id,
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        message_count=0,
        last_message_preview=None,
    )


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: str,
    session: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Conversation)
        .options(selectinload(Conversation.messages).selectinload(Message.images))
        .where(Conversation.id == conversation_id)
    )
    result = await session.execute(stmt)
    conv = result.scalar_one_or_none()

    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return ConversationDetail(
        id=conv.id,
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        messages=[
            MessageOut(
                id=m.id,
                conversation_id=m.conversation_id,
                role=m.role,
                content_text=m.content_text,
                content_structured=m.content_structured,
                message_type=m.message_type,
                created_at=m.created_at,
                images=[],
            )
            for m in conv.messages
        ],
    )


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    session: AsyncSession = Depends(get_db),
):
    conv = await session.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    await session.delete(conv)
    await session.commit()
    return {"detail": "Conversation deleted"}
