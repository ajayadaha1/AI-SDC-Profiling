from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from .config import get_settings
from .database import Base, engine
from .routers import chat, conversations, feedback, health, predictions, snowflake_explorer

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="AI SDC Profiling API",
    description="LLM-in-the-Loop Predictive Debug System for AFHC/ANC",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(conversations.router, prefix="/api/conversations", tags=["conversations"])
app.include_router(predictions.router, prefix="/api/predictions", tags=["predictions"])
app.include_router(feedback.router, prefix="/api/feedback", tags=["feedback"])
app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(snowflake_explorer.router, prefix="/api/snowflake", tags=["snowflake"])
