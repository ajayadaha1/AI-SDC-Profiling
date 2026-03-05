from fastapi import APIRouter, HTTPException, Query

from ..services import snowflake_service

router = APIRouter()


@router.get("/test")
async def test_connection():
    """Test Snowflake connectivity."""
    return snowflake_service.test_connection()


@router.get("/schemas")
async def list_schemas():
    """List schemas in the database."""
    try:
        return snowflake_service.list_schemas()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tables")
async def list_tables(schema: str | None = Query(None)):
    """List tables in a schema (defaults to configured schema)."""
    try:
        return snowflake_service.list_tables(schema)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tables/{table_name}/describe")
async def describe_table(table_name: str, schema: str | None = Query(None)):
    """Get column descriptions for a table."""
    try:
        return snowflake_service.describe_table(table_name, schema)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tables/{table_name}/sample")
async def sample_table(
    table_name: str,
    limit: int = Query(5, ge=1, le=100),
    schema: str | None = Query(None),
):
    """Get sample rows from a table."""
    try:
        return snowflake_service.sample_table(table_name, limit, schema)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
