import logging
from pathlib import Path

import snowflake.connector
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

from ..config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _load_private_key():
    """Load RSA private key from file for key-pair authentication."""
    key_path = Path(settings.SNOWFLAKE_PRIVATE_KEY_PATH)
    if not key_path.exists():
        raise FileNotFoundError(
            f"Snowflake private key not found at {key_path}. "
            "Generate with: openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_key.p8 -nocrypt"
        )

    with open(key_path, "rb") as f:
        private_key = serialization.load_pem_private_key(
            f.read(), password=None, backend=default_backend()
        )
    return private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


def get_connection() -> snowflake.connector.SnowflakeConnection:
    """Create a Snowflake connection using key-pair authentication."""
    private_key_bytes = _load_private_key()

    conn = snowflake.connector.connect(
        account=settings.SNOWFLAKE_ACCOUNT,
        user=settings.SNOWFLAKE_USER,
        private_key=private_key_bytes,
        role=settings.SNOWFLAKE_ROLE,
        warehouse=settings.SNOWFLAKE_WAREHOUSE,
        database=settings.SNOWFLAKE_DATABASE,
        schema=settings.SNOWFLAKE_SCHEMA,
    )
    return conn


def test_connection() -> dict:
    """Test the Snowflake connection and return status info."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_WAREHOUSE(), CURRENT_DATABASE(), CURRENT_SCHEMA()")
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return {
            "status": "connected",
            "user": row[0],
            "role": row[1],
            "warehouse": row[2],
            "database": row[3],
            "schema": row[4],
        }
    except FileNotFoundError as e:
        return {"status": "key_missing", "error": str(e)}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def list_schemas() -> list[dict]:
    """List all schemas in the current database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SHOW SCHEMAS")
    schemas = []
    for row in cursor:
        schemas.append({
            "name": row[1],
            "database": row[3] if len(row) > 3 else settings.SNOWFLAKE_DATABASE,
        })
    cursor.close()
    conn.close()
    return schemas


def list_tables(schema: str | None = None) -> list[dict]:
    """List all tables in a schema."""
    schema = schema or settings.SNOWFLAKE_SCHEMA
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"SHOW TABLES IN SCHEMA {settings.SNOWFLAKE_DATABASE}.{schema}")
    tables = []
    for row in cursor:
        tables.append({
            "name": row[1],
            "database": row[3] if len(row) > 3 else settings.SNOWFLAKE_DATABASE,
            "schema": row[4] if len(row) > 4 else schema,
            "rows": row[5] if len(row) > 5 else None,
        })
    cursor.close()
    conn.close()
    return tables


def describe_table(table_name: str, schema: str | None = None) -> list[dict]:
    """Get column info for a table."""
    schema = schema or settings.SNOWFLAKE_SCHEMA
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"DESCRIBE TABLE {settings.SNOWFLAKE_DATABASE}.{schema}.{table_name}")
    columns = []
    for row in cursor:
        columns.append({
            "name": row[0],
            "type": row[1],
            "nullable": row[3] if len(row) > 3 else None,
        })
    cursor.close()
    conn.close()
    return columns


def sample_table(table_name: str, limit: int = 5, schema: str | None = None) -> dict:
    """Get sample rows from a table."""
    schema = schema or settings.SNOWFLAKE_SCHEMA
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT * FROM {settings.SNOWFLAKE_DATABASE}.{schema}.{table_name} LIMIT {limit}"
    )
    columns = [desc[0] for desc in cursor.description]
    rows = []
    for row in cursor:
        rows.append({col: str(val) if val is not None else None for col, val in zip(columns, row)})
    cursor.close()
    conn.close()
    return {"columns": columns, "rows": rows}


def execute_query(sql: str, params: dict | None = None) -> dict:
    """Execute a read-only SQL query and return results."""
    # Safety: only allow SELECT and WITH
    normalized = sql.strip().upper()
    if not (normalized.startswith("SELECT") or normalized.startswith("WITH")):
        raise ValueError("Only SELECT/WITH queries are allowed")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(sql, params or {})
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return {
        "columns": columns,
        "row_count": len(rows),
        "rows": [
            {col: str(val) if val is not None else None for col, val in zip(columns, row)}
            for row in rows
        ],
    }
