from pydantic import BaseModel


class ChatRequest(BaseModel):
    conversation_id: str
    text: str
    structured_fields: dict | None = None


class SSEEvent(BaseModel):
    type: str  # parsing_started, parsing_complete, search_started, search_complete, ranking_started, prediction, error, done
    data: dict | None = None
