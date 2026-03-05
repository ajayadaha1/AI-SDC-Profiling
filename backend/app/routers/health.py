from fastapi import APIRouter

from ..config import get_settings

router = APIRouter()

settings = get_settings()


@router.get("")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": "0.1.0",
    }


@router.get("/ai")
async def ai_status():
    return {
        "llm": {
            "endpoint": settings.LLM_ENDPOINT,
            "model": settings.LLM_MODEL,
            "configured": bool(settings.LLM_API_KEY),
        },
        "vision": {
            "endpoint": settings.VISION_ENDPOINT,
            "model": settings.VISION_MODEL,
            "configured": bool(settings.VISION_API_KEY),
        },
        "snowflake": {
            "configured": settings.snowflake_configured,
            "key_available": settings.snowflake_key_available,
            "account": settings.SNOWFLAKE_ACCOUNT or "(not set)",
            "user": settings.SNOWFLAKE_USER or "(not set)",
            "database": f"{settings.SNOWFLAKE_DATABASE}.{settings.SNOWFLAKE_SCHEMA}",
            "warehouse": settings.SNOWFLAKE_WAREHOUSE or "(not set)",
        },
        "embedding": {
            "model": settings.EMBEDDING_MODEL,
            "dimensions": settings.EMBEDDING_DIMENSIONS,
        },
    }
