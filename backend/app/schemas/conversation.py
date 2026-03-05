from datetime import datetime

from pydantic import BaseModel


class ConversationCreate(BaseModel):
    title: str | None = None


class ConversationSummary(BaseModel):
    id: str
    title: str | None
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    last_message_preview: str | None = None

    model_config = {"from_attributes": True}


class ConversationDetail(BaseModel):
    id: str
    title: str | None
    created_at: datetime
    updated_at: datetime
    messages: list["MessageOut"]

    model_config = {"from_attributes": True}


class MessageImageOut(BaseModel):
    id: int
    filename: str
    content_type: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageOut(BaseModel):
    id: int
    conversation_id: str
    role: str
    content_text: str | None
    content_structured: str | None
    message_type: str
    created_at: datetime
    images: list[MessageImageOut] = []

    model_config = {"from_attributes": True}
