import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import asyncpg

logger = logging.getLogger(__name__)


class InsertResult:
    def __init__(self, inserted_id: str):
        self.inserted_id = inserted_id


class UpdateResult:
    def __init__(self, matched: int, modified: int):
        self.matched_count = matched
        self.modified_count = modified


class DeleteResult:
    def __init__(self, deleted: int):
        self.deleted_count = deleted


class AsyncCursor:
    def __init__(self, data: List[Dict[str, Any]]):
        self.data = data
        self.index = 0

    def sort(self, field: str, direction: int = 1):
        self.data.sort(
            key=lambda x: x.get(field, ""),
            reverse=(direction == -1),
        )
        return self

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.index >= len(self.data):
            raise StopAsyncIteration
        item = self.data[self.index]
        self.index += 1
        return item


def _json_default(obj: Any):
    if isinstance(obj, datetime):
        return obj.isoformat()
    return str(obj)


def _decode_record(row: asyncpg.Record) -> Dict[str, Any]:
    payload = row.get("payload") if "payload" in row else None
    if isinstance(payload, str):
        doc = json.loads(payload)
    elif isinstance(payload, dict):
        doc = payload
    else:
        doc = {}
    doc["_id"] = row["id"]
    return doc


class PgCollection:
    def __init__(self, table_name: str):
        self.table_name = table_name

    async def find(self, query: Dict[str, Any] = None):
        async with Database.pool.acquire() as conn:
            rows = await conn.fetch(
                f"SELECT id, payload FROM {self.table_name} ORDER BY updated_at DESC"
            )
        docs = [_decode_record(row) for row in rows]
        if query:
            docs = [
                doc for doc in docs if all(doc.get(k) == v for k, v in query.items())
            ]
        return AsyncCursor(docs)

    async def find_one(self, query: Dict[str, Any]):
        if "_id" in query:
            async with Database.pool.acquire() as conn:
                row = await conn.fetchrow(
                    f"SELECT id, payload FROM {self.table_name} WHERE id = $1",
                    str(query["_id"]),
                )
            return _decode_record(row) if row else None

        cursor = await self.find(query=query)
        async for item in cursor:
            return item
        return None

    async def insert_one(self, document: Dict[str, Any]):
        doc = document.copy()
        doc_id = str(doc.pop("_id", "")) or ""

        async with Database.pool.acquire() as conn:
            if not doc_id:
                row = await conn.fetchrow(
                    f"""
                    INSERT INTO {self.table_name} (payload)
                    VALUES ($1::jsonb)
                    RETURNING id
                    """,
                    json.dumps(doc, default=_json_default),
                )
                doc_id = row["id"]
            else:
                await conn.execute(
                    f"""
                    INSERT INTO {self.table_name} (id, payload)
                    VALUES ($1, $2::jsonb)
                    ON CONFLICT (id) DO UPDATE SET
                      payload = EXCLUDED.payload,
                      updated_at = CURRENT_TIMESTAMP
                    """,
                    doc_id,
                    json.dumps(doc, default=_json_default),
                )
        return InsertResult(doc_id)

    async def update_one(self, query: Dict[str, Any], update: Dict[str, Any]):
        current = await self.find_one(query)
        if not current:
            if "$set" in update:
                new_doc = query.copy()
                new_doc.update(update["$set"])
                result = await self.insert_one(new_doc)
                return UpdateResult(1, 1 if result.inserted_id else 0)
            return UpdateResult(0, 0)

        if "$set" in update:
            current.update(update["$set"])
            doc_id = str(current.get("_id"))
            current.pop("_id", None)
            async with Database.pool.acquire() as conn:
                await conn.execute(
                    f"""
                    UPDATE {self.table_name}
                    SET payload = $2::jsonb, updated_at = CURRENT_TIMESTAMP
                    WHERE id = $1
                    """,
                    doc_id,
                    json.dumps(current, default=_json_default),
                )
            return UpdateResult(1, 1)
        return UpdateResult(0, 0)

    async def delete_one(self, query: Dict[str, Any]):
        current = await self.find_one(query)
        if not current:
            return DeleteResult(0)

        doc_id = str(current.get("_id"))
        async with Database.pool.acquire() as conn:
            result = await conn.execute(
                f"DELETE FROM {self.table_name} WHERE id = $1",
                doc_id,
            )
        deleted = 1 if result == "DELETE 1" else 0
        return DeleteResult(deleted)

    async def count_documents(self, query: Dict[str, Any] = None):
        if not query:
            async with Database.pool.acquire() as conn:
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {self.table_name}")
            return int(count or 0)

        cursor = await self.find(query=query)
        count = 0
        async for _ in cursor:
            count += 1
        return count


class PgDatabase:
    def __init__(self):
        self.document_analysis = PgCollection("document_analysis")
        self.image_analysis = PgCollection("image_analysis")
        self.image_hashes = PgCollection("image_hashes")


class Database:
    """Database singleton backed by PostgreSQL (Supabase-compatible)."""

    pool: Optional[asyncpg.Pool] = None
    database: Optional[PgDatabase] = None

    @classmethod
    async def initialize_async(cls):
        if cls.pool is not None:
            return

        db_host = os.getenv("POSTGRES_HOST", "localhost")
        db_port = int(os.getenv("POSTGRES_PORT", "5432"))
        db_name = os.getenv("POSTGRES_DB", "postgres")
        db_user = os.getenv("POSTGRES_USER", "postgres")
        db_password = os.getenv("POSTGRES_PASSWORD", "")
        db_url = os.getenv("DATABASE_URL", "").strip()

        if db_url:
            cls.pool = await asyncpg.create_pool(dsn=db_url, min_size=1, max_size=10)
        else:
            cls.pool = await asyncpg.create_pool(
                host=db_host,
                port=db_port,
                database=db_name,
                user=db_user,
                password=db_password,
                min_size=1,
                max_size=10,
            )

        async with cls.pool.acquire() as conn:
            await conn.execute(
                """
                CREATE EXTENSION IF NOT EXISTS pgcrypto;
                CREATE TABLE IF NOT EXISTS document_analysis (
                  id TEXT PRIMARY KEY DEFAULT ('obj_' || replace(gen_random_uuid()::text, '-', '')),
                  payload JSONB NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS image_analysis (
                  id TEXT PRIMARY KEY DEFAULT ('obj_' || replace(gen_random_uuid()::text, '-', '')),
                  payload JSONB NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS image_hashes (
                  id TEXT PRIMARY KEY DEFAULT ('obj_' || replace(gen_random_uuid()::text, '-', '')),
                  payload JSONB NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

        cls.database = PgDatabase()
        logger.info("Backend 2 PostgreSQL storage initialized")

    @classmethod
    def initialize(cls):
        """Sync wrapper used by existing app startup code."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Startup in FastAPI context usually runs in loop; schedule task and wait for it.
                fut = asyncio.run_coroutine_threadsafe(
                    cls.initialize_async(), loop
                )
                fut.result(timeout=30)
            else:
                loop.run_until_complete(cls.initialize_async())
        except RuntimeError:
            asyncio.run(cls.initialize_async())

    @classmethod
    async def close_async(cls):
        if cls.pool:
            await cls.pool.close()
            cls.pool = None
            cls.database = None

    @classmethod
    def close(cls):
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                fut = asyncio.run_coroutine_threadsafe(cls.close_async(), loop)
                fut.result(timeout=10)
            else:
                loop.run_until_complete(cls.close_async())
        except RuntimeError:
            asyncio.run(cls.close_async())

    @classmethod
    def get_database(cls):
        if cls.database is None:
            cls.initialize()
        return cls.database
