import logging
from typing import Dict, List, Any
from datetime import datetime

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
        
        # Support query by other fields
        for doc in self._data.values():
            if all(doc.get(k) == v for k, v in query.items()):
                return doc
        
        return None

    async def insert_one(self, document: Dict[str, Any]):
        """Insert a document"""
        document_copy = document.copy()
        
        # Use existing _id if provided, otherwise generate one
        if "_id" not in document_copy:
            self._counter += 1
            doc_id = f"obj_{self._counter}"
            document_copy["_id"] = doc_id
        else:
            doc_id = document_copy["_id"]
        
        class InsertResult:
            def __init__(self, inserted_id):
                self.inserted_id = inserted_id

        self._data[str(doc_id)] = document_copy

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
        
        # Support query by other fields (upsert behavior)
        for obj_id, doc in list(self._data.items()):
            if all(doc.get(k) == v for k, v in query.items() if k != "_id"):
                if "$set" in update:
                    self._data[obj_id].update(update["$set"])
                
                class UpdateResult:
                    def __init__(self, matched, modified):
                        self.matched_count = matched
                        self.modified_count = modified
                
                return UpdateResult(1, 1)
        
        # Upsert: create new document if not found
        if "$set" in update:
            new_doc = query.copy()
            new_doc.update(update["$set"])
            # Generate _id if not present
            if "_id" not in new_doc:
                self._counter += 1
                new_doc["_id"] = f"obj_{self._counter}"
            self._data[str(new_doc["_id"])] = new_doc
            
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
        
        # Also support query by other fields (e.g., image_id)
        for obj_id, doc in list(self._data.items()):
            if any(doc.get(k) == v for k, v in query.items() if k != "_id"):
                del self._data[obj_id]
                class DeleteResult:
                    def __init__(self, deleted):
                        self.deleted_count = deleted
                return DeleteResult(1)

        class DeleteResult:
            def __init__(self, deleted):
                self.deleted_count = deleted

        return DeleteResult(0)
    
    async def count_documents(self, query: Dict[str, Any] = None):
        """Count documents matching query"""
        if query is None or len(query) == 0:
            return len(self._data)
        
        count = 0
        for doc in self._data.values():
            if all(doc.get(k) == v for k, v in query.items()):
                count += 1
        return count


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
    database: InMemoryDatabase = None

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