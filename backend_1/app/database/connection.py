import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncpg
import os

logger = logging.getLogger(__name__)


class InMemoryCollection:
    """Simple in-memory collection that mimics async MongoDB operations"""

    def __init__(self, name: str):
        self.name = name
        self._data: Dict[str, Dict[str, Any]] = {}
        self._counter = 0

    async def find(self, query: Dict[str, Any] = None):
        """Find documents matching query"""

        class AsyncCursor:
            def __init__(self, data):
                self.data = list(data.values())
                self.index = 0

            def __aiter__(self):
                return self

            async def __anext__(self):
                if self.index >= len(self.data):
                    raise StopAsyncIteration
                item = self.data[self.index]
                self.index += 1
                return item

        return AsyncCursor(self._data)

    async def find_one(self, query: Dict[str, Any]):
        """Find a single document"""
        if "_id" in query:
            obj_id = query["_id"]
            return self._data.get(str(obj_id))
        return None

    async def insert_one(self, document: Dict[str, Any]):
        """Insert a document"""
        self._counter += 1
        doc_id = f"obj_{self._counter}"

        class InsertResult:
            def __init__(self, inserted_id):
                self.inserted_id = inserted_id

        document_copy = document.copy()
        document_copy["_id"] = doc_id
        self._data[doc_id] = document_copy

        return InsertResult(doc_id)

    async def update_one(self, query: Dict[str, Any], update: Dict[str, Any]):
        """Update a document"""
        if "_id" in query:
            obj_id = str(query["_id"])
            if obj_id in self._data:
                if "$set" in update:
                    self._data[obj_id].update(update["$set"])

                class UpdateResult:
                    def __init__(self, matched, modified):
                        self.matched_count = matched
                        self.modified_count = modified

                return UpdateResult(1, 1)

        class UpdateResult:
            def __init__(self, matched, modified):
                self.matched_count = matched
                self.modified_count = modified

        return UpdateResult(0, 0)

    async def delete_one(self, query: Dict[str, Any]):
        """Delete a document"""
        if "_id" in query:
            obj_id = str(query["_id"])
            if obj_id in self._data:
                del self._data[obj_id]

                class DeleteResult:
                    def __init__(self, deleted):
                        self.deleted_count = deleted

                return DeleteResult(1)

        class DeleteResult:
            def __init__(self, deleted):
                self.deleted_count = deleted

        return DeleteResult(0)


class InMemoryDatabase:
    """Simple in-memory database that mimics async MongoDB"""

    def __init__(self):
        self._collections: Dict[str, InMemoryCollection] = {}

    def __getattr__(self, name: str):
        """Get or create a collection"""
        if name not in self._collections:
            self._collections[name] = InMemoryCollection(name)
        return self._collections[name]


class Database:
    """Database singleton for in-memory storage"""

    database: Optional[InMemoryDatabase] = None

    @classmethod
    def initialize(cls):
        """Initialize in-memory database"""
        try:
            cls.database = InMemoryDatabase()
            logger.info("In-memory database initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    @classmethod
    def close(cls):
        """Close database connection (no-op for in-memory)"""
        logger.info("In-memory database closed")

    @classmethod
    def get_database(cls):
        """Get database instance"""
        if cls.database is None:
            cls.initialize()
        return cls.database


class PostgresDatabase:
    """PostgreSQL database connection pool"""

    pool: Optional[asyncpg.Pool] = None

    @classmethod
    async def initialize(cls):
        """Initialize PostgreSQL connection pool"""
        try:
            # Get connection parameters from environment
            db_host = os.getenv("POSTGRES_HOST", "localhost")
            db_port = os.getenv("POSTGRES_PORT", "5432")
            db_name = os.getenv("POSTGRES_DB", "baer_aml")
            db_user = os.getenv("POSTGRES_USER", "baer_aml")
            db_password = os.getenv("POSTGRES_PASSWORD", "baer_aml")

            cls.pool = await asyncpg.create_pool(
                host=db_host,
                port=db_port,
                database=db_name,
                user=db_user,
                password=db_password,
                min_size=1,
                max_size=10,
            )
            logger.info("PostgreSQL connection pool initialized")

            # Create rules table if it doesn't exist
            await cls.create_rules_table()
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL: {e}")
            raise

    @classmethod
    async def create_rules_table(cls):
        """Create rules table if it doesn't exist"""
        if cls.pool is None:
            raise RuntimeError("Database pool not initialized")

        async with cls.pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS rules (
                    id TEXT PRIMARY KEY,
                    rule_text TEXT NOT NULL,
                    function_code TEXT NOT NULL,
                    explanation TEXT,
                    attributes_used TEXT[],
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
            logger.info("Rules table created/verified")

    @classmethod
    async def close(cls):
        """Close database connection pool"""
        if cls.pool:
            await cls.pool.close()
            logger.info("PostgreSQL connection pool closed")

    @classmethod
    def get_pool(cls) -> asyncpg.Pool:
        """Get database pool"""
        if cls.pool is None:
            raise RuntimeError(
                "Database pool not initialized. Call initialize() first."
            )
        return cls.pool

    @classmethod
    async def insert_rule(
        cls,
        rule_id: str,
        rule_text: str,
        function_code: str,
        explanation: Optional[str] = None,
        attributes_used: Optional[List[str]] = None,
    ) -> str:
        """Insert a new rule into the database"""
        if cls.pool is None:
            raise RuntimeError("Database pool not initialized")

        async with cls.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO rules (id, rule_text, function_code, explanation, attributes_used)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (id) DO UPDATE SET
                    rule_text = EXCLUDED.rule_text,
                    function_code = EXCLUDED.function_code,
                    explanation = EXCLUDED.explanation,
                    attributes_used = EXCLUDED.attributes_used,
                    updated_at = CURRENT_TIMESTAMP
                """,
                rule_id,
                rule_text,
                function_code,
                explanation,
                attributes_used or [],
            )
            logger.info(f"Rule inserted/updated with id: {rule_id}")
            return rule_id

    @classmethod
    async def get_rule(cls, rule_id: str) -> Optional[Dict[str, Any]]:
        """Get a rule by ID"""
        if cls.pool is None:
            raise RuntimeError("Database pool not initialized")

        async with cls.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, rule_text, function_code, explanation, attributes_used, created_at, updated_at
                FROM rules
                WHERE id = $1
                """,
                rule_id,
            )
            if row:
                return dict(row)
            return None

    @classmethod
    async def get_all_rules(cls) -> List[Dict[str, Any]]:
        """Get all rules"""
        if cls.pool is None:
            raise RuntimeError("Database pool not initialized")

        async with cls.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, rule_text, function_code, explanation, attributes_used, created_at, updated_at
                FROM rules
                ORDER BY created_at DESC
                """
            )
            return [dict(row) for row in rows]

    @classmethod
    async def update_rule(
        cls,
        rule_id: str,
        rule_text: Optional[str] = None,
        function_code: Optional[str] = None,
        explanation: Optional[str] = None,
        attributes_used: Optional[List[str]] = None,
    ) -> bool:
        """Update an existing rule"""
        if cls.pool is None:
            raise RuntimeError("Database pool not initialized")

        updates = []
        params = []
        param_count = 1

        if rule_text is not None:
            updates.append(f"rule_text = ${param_count}")
            params.append(rule_text)
            param_count += 1

        if function_code is not None:
            updates.append(f"function_code = ${param_count}")
            params.append(function_code)
            param_count += 1

        if explanation is not None:
            updates.append(f"explanation = ${param_count}")
            params.append(explanation)
            param_count += 1

        if attributes_used is not None:
            updates.append(f"attributes_used = ${param_count}")
            params.append(attributes_used)
            param_count += 1

        if not updates:
            return False

        updates.append(f"updated_at = CURRENT_TIMESTAMP")
        params.append(rule_id)

        query = f"""
            UPDATE rules
            SET {', '.join(updates)}
            WHERE id = ${param_count}
        """

        async with cls.pool.acquire() as conn:
            result = await conn.execute(query, *params)
            return result == "UPDATE 1"

    @classmethod
    async def delete_rule(cls, rule_id: str) -> bool:
        """Delete a rule by ID"""
        if cls.pool is None:
            raise RuntimeError("Database pool not initialized")

        async with cls.pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM rules WHERE id = $1",
                rule_id,
            )
            return result == "DELETE 1"
