import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from supabase import Client, create_client

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lightweight cursor shim (keeps callers that do `async for item in cursor`)
# ---------------------------------------------------------------------------

class AsyncCursor:
    def __init__(self, data: List[Dict[str, Any]]):
        self.data = data
        self.index = 0

    def sort(self, field: str, direction: int = 1):
        self.data.sort(key=lambda x: x.get(field, ""), reverse=(direction == -1))
        return self

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.index >= len(self.data):
            raise StopAsyncIteration
        item = self.data[self.index]
        self.index += 1
        return item


# ---------------------------------------------------------------------------
# Result shims kept for callers that inspect .inserted_id / .matched_count
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# PgCollection — thin PostgREST-backed collection
# ---------------------------------------------------------------------------

class PgCollection:
    def __init__(self, table_name: str):
        self.table_name = table_name

    def _client(self) -> Client:
        return Database._client  # type: ignore[attr-defined]

    async def find(self, query: Dict[str, Any] = None):
        c = self._client()
        res = await asyncio.to_thread(
            lambda: c.table(self.table_name)
            .select("*")
            .order("updated_at", desc=True)
            .execute()
        )
        docs = _decode_rows(res.data or [])
        if query:
            docs = [d for d in docs if all(d.get(k) == v for k, v in query.items())]
        return AsyncCursor(docs)

    async def find_one(self, query: Dict[str, Any]):
        if "_id" in query:
            c = self._client()
            res = await asyncio.to_thread(
                lambda: c.table(self.table_name)
                .select("*")
                .eq("id", str(query["_id"]))
                .execute()
            )
            rows = res.data or []
            return _decode_rows(rows)[0] if rows else None

        cursor = await self.find(query=query)
        async for item in cursor:
            return item
        return None

    async def insert_one(self, document: Dict[str, Any]):
        c = self._client()
        doc = document.copy()
        existing_id = str(doc.pop("_id", "")) or ""
        payload = json.dumps(doc, default=_json_default)

        if existing_id:
            await asyncio.to_thread(
                lambda: c.table(self.table_name).upsert(
                    {"id": existing_id, "payload": payload}, on_conflict="id"
                ).execute()
            )
            doc_id = existing_id
        else:
            res = await asyncio.to_thread(
                lambda: c.table(self.table_name).insert({"payload": payload}).execute()
            )
            doc_id = (res.data or [{}])[0].get("id", "")
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
            doc_id = str(current.pop("_id", ""))
            payload = json.dumps(current, default=_json_default)
            c = self._client()
            await asyncio.to_thread(
                lambda: c.table(self.table_name)
                .update({"payload": payload})
                .eq("id", doc_id)
                .execute()
            )
            return UpdateResult(1, 1)
        return UpdateResult(0, 0)

    async def delete_one(self, query: Dict[str, Any]):
        current = await self.find_one(query)
        if not current:
            return DeleteResult(0)
        doc_id = str(current.get("_id", ""))
        c = self._client()
        res = await asyncio.to_thread(
            lambda: c.table(self.table_name).delete().eq("id", doc_id).execute()
        )
        deleted = 1 if res.data else 0
        return DeleteResult(deleted)

    async def count_documents(self, query: Dict[str, Any] = None):
        cursor = await self.find(query=query)
        count = 0
        async for _ in cursor:
            count += 1
        return count


# ---------------------------------------------------------------------------
# PgDatabase — named collection accessors
# ---------------------------------------------------------------------------

class PgDatabase:
    def __init__(self):
        self.document_analysis = PgCollection("document_analysis")
        self.image_analysis = PgCollection("image_analysis")
        self.image_hashes = PgCollection("image_hashes")


# ---------------------------------------------------------------------------
# Database singleton
# ---------------------------------------------------------------------------

class Database:
    _client: Optional[Client] = None
    database: Optional[PgDatabase] = None

    @classmethod
    async def initialize_async(cls):
        if cls._client is not None:
            return

        url = os.getenv("SUPABASE_URL", "").strip()
        key = os.getenv("SUPABASE_KEY", "").strip()
        if not url or not key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_KEY environment variables are required")

        cls._client = create_client(url, key)

        # Smoke-test
        await asyncio.to_thread(
            lambda: cls._client.table("document_analysis").select("id").limit(1).execute()
        )

        cls.database = PgDatabase()
        logger.info("Backend 2 Supabase storage initialized")

    @classmethod
    def initialize(cls):
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                fut = asyncio.run_coroutine_threadsafe(cls.initialize_async(), loop)
                fut.result(timeout=30)
            else:
                loop.run_until_complete(cls.initialize_async())
        except RuntimeError:
            asyncio.run(cls.initialize_async())

    @classmethod
    async def close_async(cls):
        cls._client = None
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
            raise RuntimeError(
                "Database not initialized — ensure SUPABASE_URL and SUPABASE_KEY env vars are set in Render."
            )
        return cls.database


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _json_default(obj: Any):
    if isinstance(obj, datetime):
        return obj.isoformat()
    return str(obj)


def _decode_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert Supabase rows (with id + payload columns) into document dicts."""
    docs = []
    for row in rows:
        payload = row.get("payload")
        if isinstance(payload, str):
            try:
                doc = json.loads(payload)
            except Exception:
                doc = {}
        elif isinstance(payload, dict):
            doc = payload.copy()
        else:
            doc = {}
        doc["_id"] = row.get("id", "")
        docs.append(doc)
    return docs
