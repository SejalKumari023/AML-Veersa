import asyncio
import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from supabase import Client, create_client

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# In-memory fallback (legacy, kept for Database.initialize() callers)
# ---------------------------------------------------------------------------

class InMemoryCollection:
    def __init__(self, name: str):
        self.name = name
        self._data: Dict[str, Dict[str, Any]] = {}
        self._counter = 0

    async def find(self, query: Dict[str, Any] = None):
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
        if "_id" in query:
            return self._data.get(str(query["_id"]))
        return None

    async def insert_one(self, document: Dict[str, Any]):
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
        class UpdateResult:
            def __init__(self, matched, modified):
                self.matched_count = matched
                self.modified_count = modified

        if "_id" in query:
            obj_id = str(query["_id"])
            if obj_id in self._data:
                if "$set" in update:
                    self._data[obj_id].update(update["$set"])
                return UpdateResult(1, 1)
        return UpdateResult(0, 0)

    async def delete_one(self, query: Dict[str, Any]):
        class DeleteResult:
            def __init__(self, deleted):
                self.deleted_count = deleted

        if "_id" in query:
            obj_id = str(query["_id"])
            if obj_id in self._data:
                del self._data[obj_id]
                return DeleteResult(1)
        return DeleteResult(0)


class InMemoryDatabase:
    def __init__(self):
        self._collections: Dict[str, InMemoryCollection] = {}

    def __getattr__(self, name: str):
        if name not in self._collections:
            self._collections[name] = InMemoryCollection(name)
        return self._collections[name]


class Database:
    database: Optional[InMemoryDatabase] = None

    @classmethod
    def initialize(cls):
        cls.database = InMemoryDatabase()
        logger.info("In-memory database initialized")

    @classmethod
    def close(cls):
        logger.info("In-memory database closed")

    @classmethod
    def get_database(cls):
        if cls.database is None:
            cls.initialize()
        return cls.database


# ---------------------------------------------------------------------------
# Supabase-backed persistent store
# ---------------------------------------------------------------------------

def _run(fn):
    """Run a synchronous supabase call and return the result."""
    return fn()


class PostgresDatabase:
    """PostgreSQL via Supabase REST API (HTTPS port 443 — no port 5432 needed)."""

    _client: Optional[Client] = None

    @classmethod
    async def initialize(cls):
        url = os.getenv("SUPABASE_URL", "").strip()
        key = os.getenv("SUPABASE_KEY", "").strip()
        if not url or not key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_KEY environment variables are required")
        cls._client = create_client(url, key)
        logger.info("Supabase client initialized successfully")

    @classmethod
    async def create_rules_table(cls):
        # Tables are pre-created in Supabase — no-op.
        pass

    @classmethod
    async def close(cls):
        cls._client = None
        logger.info("Supabase client closed")

    @classmethod
    def get_pool(cls):
        return cls._client

    @classmethod
    def _c(cls) -> Client:
        if cls._client is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return cls._client

    # ------------------------------------------------------------------
    # Rules
    # ------------------------------------------------------------------

    @classmethod
    async def insert_rule(
        cls,
        rule_id: str,
        rule_text: str,
        function_code: str,
        explanation: Optional[str] = None,
        attributes_used: Optional[List[str]] = None,
    ) -> str:
        c = cls._c()
        data = {
            "id": rule_id,
            "rule_text": rule_text,
            "function_code": function_code,
            "explanation": explanation,
            "attributes_used": attributes_used or [],
        }
        await asyncio.to_thread(
            lambda: c.table("rules").upsert(data, on_conflict="id").execute()
        )
        logger.info(f"Rule upserted: {rule_id}")
        return rule_id

    @classmethod
    async def get_rule(cls, rule_id: str) -> Optional[Dict[str, Any]]:
        c = cls._c()
        res = await asyncio.to_thread(
            lambda: c.table("rules").select("*").eq("id", rule_id).execute()
        )
        return res.data[0] if res.data else None

    @classmethod
    async def get_all_rules(cls) -> List[Dict[str, Any]]:
        c = cls._c()
        res = await asyncio.to_thread(
            lambda: c.table("rules").select("*").order("created_at", desc=True).execute()
        )
        return res.data or []

    @classmethod
    async def update_rule(
        cls,
        rule_id: str,
        rule_text: Optional[str] = None,
        function_code: Optional[str] = None,
        explanation: Optional[str] = None,
        attributes_used: Optional[List[str]] = None,
    ) -> bool:
        updates: Dict[str, Any] = {}
        if rule_text is not None:
            updates["rule_text"] = rule_text
        if function_code is not None:
            updates["function_code"] = function_code
        if explanation is not None:
            updates["explanation"] = explanation
        if attributes_used is not None:
            updates["attributes_used"] = attributes_used
        if not updates:
            return False
        c = cls._c()
        res = await asyncio.to_thread(
            lambda: c.table("rules").update(updates).eq("id", rule_id).execute()
        )
        return bool(res.data)

    @classmethod
    async def delete_rule(cls, rule_id: str) -> bool:
        c = cls._c()
        res = await asyncio.to_thread(
            lambda: c.table("rules").delete().eq("id", rule_id).execute()
        )
        return bool(res.data)

    # ------------------------------------------------------------------
    # Transactions
    # ------------------------------------------------------------------

    @classmethod
    async def insert_transaction(cls, transaction_data: Dict[str, Any]) -> str:
        c = cls._c()
        # Coerce datetime objects to ISO strings for PostgREST
        data = _coerce_datetimes(transaction_data)
        tid = data.get("transaction_id", "")
        await asyncio.to_thread(
            lambda: c.table("transactions").upsert(data, on_conflict="transaction_id").execute()
        )
        logger.info(f"Transaction upserted: {tid}")
        return tid

    @classmethod
    async def get_transaction(cls, transaction_id: str) -> Optional[Dict[str, Any]]:
        c = cls._c()
        res = await asyncio.to_thread(
            lambda: c.table("transactions").select("*").eq("transaction_id", transaction_id).execute()
        )
        return res.data[0] if res.data else None

    @classmethod
    async def get_all_transactions(
        cls, limit: int = 1000, offset: int = 0
    ) -> List[Dict[str, Any]]:
        c = cls._c()
        res = await asyncio.to_thread(
            lambda: c.table("transactions")
            .select("*")
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        return res.data or []

    @classmethod
    async def delete_transaction(cls, transaction_id: str) -> bool:
        c = cls._c()
        res = await asyncio.to_thread(
            lambda: c.table("transactions").delete().eq("transaction_id", transaction_id).execute()
        )
        return bool(res.data)

    # ------------------------------------------------------------------
    # Alerts
    # ------------------------------------------------------------------

    @classmethod
    async def insert_alert(cls, alert_data: Dict[str, Any]) -> str:
        c = cls._c()
        data = _coerce_datetimes(alert_data)
        if not data.get("id"):
            data["id"] = f"alert_{uuid.uuid4().hex[:12]}"
        aid = data["id"]
        await asyncio.to_thread(
            lambda: c.table("alerts").upsert(data, on_conflict="id").execute()
        )
        logger.info(f"Alert upserted: {aid}")
        return aid

    @classmethod
    async def get_alert(cls, alert_id: str) -> Optional[Dict[str, Any]]:
        c = cls._c()
        res = await asyncio.to_thread(
            lambda: c.table("alerts").select("*").eq("id", alert_id).execute()
        )
        return res.data[0] if res.data else None

    @classmethod
    async def get_all_alerts(
        cls, limit: int = 1000, offset: int = 0
    ) -> List[Dict[str, Any]]:
        c = cls._c()
        res = await asyncio.to_thread(
            lambda: c.table("alerts")
            .select("*")
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        return res.data or []

    @classmethod
    async def delete_alert(cls, alert_id: str) -> bool:
        c = cls._c()
        res = await asyncio.to_thread(
            lambda: c.table("alerts").delete().eq("id", alert_id).execute()
        )
        return bool(res.data)

    # ------------------------------------------------------------------
    # Risk summary
    # ------------------------------------------------------------------

    @classmethod
    async def get_risk_summary(cls) -> Dict[str, Any]:
        c = cls._c()
        txns_res = await asyncio.to_thread(
            lambda: c.table("transactions").select("risk_score").execute()
        )
        txns = txns_res.data or []
        total = len(txns)
        scores = [float(r["risk_score"]) for r in txns if r.get("risk_score") is not None]
        high = sum(1 for s in scores if s >= 70)
        medium = sum(1 for s in scores if 40 <= s < 70)
        low = sum(1 for s in scores if s < 40)

        alerts_res = await asyncio.to_thread(
            lambda: c.table("alerts").select("status").execute()
        )
        alerts = alerts_res.data or []
        active = sum(1 for a in alerts if a.get("status") == "active")
        resolved = sum(1 for a in alerts if a.get("status") == "resolved")

        return {
            "total_transactions": total,
            "high_risk_transactions": high,
            "medium_risk_transactions": medium,
            "low_risk_transactions": low,
            "active_alerts": active,
            "resolved_alerts": resolved,
        }

    # ------------------------------------------------------------------
    # Customers
    # ------------------------------------------------------------------

    @classmethod
    async def insert_customer(cls, customer_data: Dict[str, Any]) -> str:
        c = cls._c()
        data = _coerce_datetimes(customer_data)
        if not data.get("id"):
            data["id"] = str(uuid.uuid4())
        cid = data["id"]
        await asyncio.to_thread(
            lambda: c.table("customers").upsert(data, on_conflict="customer_id").execute()
        )
        return cid

    @classmethod
    async def get_customer(cls, customer_id: str) -> Optional[Dict[str, Any]]:
        c = cls._c()
        res = await asyncio.to_thread(
            lambda: c.table("customers").select("*").eq("customer_id", customer_id).execute()
        )
        return res.data[0] if res.data else None

    @classmethod
    async def get_customer_by_id(cls, id: str) -> Optional[Dict[str, Any]]:
        c = cls._c()
        res = await asyncio.to_thread(
            lambda: c.table("customers").select("*").eq("id", id).execute()
        )
        return res.data[0] if res.data else None

    @classmethod
    async def get_all_customers(
        cls, limit: int = 1000, offset: int = 0
    ) -> List[Dict[str, Any]]:
        c = cls._c()
        res = await asyncio.to_thread(
            lambda: c.table("customers")
            .select("*")
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        return res.data or []

    @classmethod
    async def delete_customer(cls, customer_id: str) -> bool:
        c = cls._c()
        res = await asyncio.to_thread(
            lambda: c.table("customers").delete().eq("customer_id", customer_id).execute()
        )
        return bool(res.data)

    # ------------------------------------------------------------------
    # Accounts
    # ------------------------------------------------------------------

    @classmethod
    async def insert_account(cls, account_data: Dict[str, Any]) -> str:
        c = cls._c()
        data = _coerce_datetimes(account_data)
        if not data.get("id"):
            data["id"] = str(uuid.uuid4())
        aid = data["id"]
        await asyncio.to_thread(
            lambda: c.table("accounts").upsert(data, on_conflict="account_number").execute()
        )
        return aid

    @classmethod
    async def get_account(cls, account_number: str) -> Optional[Dict[str, Any]]:
        c = cls._c()
        res = await asyncio.to_thread(
            lambda: c.table("accounts").select("*").eq("account_number", account_number).execute()
        )
        return res.data[0] if res.data else None

    @classmethod
    async def get_account_by_id(cls, id: str) -> Optional[Dict[str, Any]]:
        c = cls._c()
        res = await asyncio.to_thread(
            lambda: c.table("accounts").select("*").eq("id", id).execute()
        )
        return res.data[0] if res.data else None

    @classmethod
    async def get_accounts_by_customer(cls, customer_id: str) -> List[Dict[str, Any]]:
        c = cls._c()
        res = await asyncio.to_thread(
            lambda: c.table("accounts")
            .select("*")
            .eq("customer_id", customer_id)
            .order("created_at", desc=True)
            .execute()
        )
        return res.data or []

    @classmethod
    async def get_all_accounts(
        cls, limit: int = 1000, offset: int = 0
    ) -> List[Dict[str, Any]]:
        c = cls._c()
        res = await asyncio.to_thread(
            lambda: c.table("accounts")
            .select("*")
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        return res.data or []

    @classmethod
    async def delete_account(cls, account_number: str) -> bool:
        c = cls._c()
        res = await asyncio.to_thread(
            lambda: c.table("accounts").delete().eq("account_number", account_number).execute()
        )
        return bool(res.data)

    # ------------------------------------------------------------------
    # Prompts
    # ------------------------------------------------------------------

    @classmethod
    async def get_all_prompts(cls) -> List[Dict[str, Any]]:
        c = cls._c()
        res = await asyncio.to_thread(
            lambda: c.table("prompts").select("name, description, content").order("name").execute()
        )
        return res.data or []

    @classmethod
    async def get_prompt(cls, name: str) -> Optional[Dict[str, Any]]:
        c = cls._c()
        res = await asyncio.to_thread(
            lambda: c.table("prompts").select("name, description, content").eq("name", name).execute()
        )
        return res.data[0] if res.data else None

    @classmethod
    async def upsert_prompt(cls, name: str, content: str, description: str = "") -> Dict[str, Any]:
        c = cls._c()
        data = {"name": name, "description": description, "content": content}
        res = await asyncio.to_thread(
            lambda: c.table("prompts").upsert(data, on_conflict="name").execute()
        )
        return res.data[0] if res.data else data

    @classmethod
    async def seed_default_prompts(cls) -> None:
        c = cls._c()
        defaults = [
            (
                "aml_system",
                "System prompt for the AML monitoring ReAct agent",
                """You are an expert AML (Anti-Money Laundering) monitoring agent for a financial institution.
You have access to the following tools to investigate transactions, customers, and compliance rules:
- search_transactions: Search and filter transactions by various criteria
- get_transaction: Get full details of a specific transaction
- get_alerts: Retrieve AML alerts (filter by severity/status)
- get_risk_summary: Get aggregate risk analytics across all transactions
- get_customer_profile: Fetch customer KYC/AML profile
- get_customer_relationships: Explore transaction relationship graph for a customer
- run_rules_on_transaction: Execute all compliance rules against a transaction
- create_rule: Generate a new AML rule from a plain English description
- get_all_rules: List all stored compliance rules
- ingest_regulatory_notice: Parse regulatory text into a compliance rule

Always reason step by step. Use Thought/Action/Observation format internally.
When you have enough information, provide a clear, concise final answer with specific findings and recommendations.
Focus on accuracy and compliance best practices.""",
            ),
            (
                "aml_react_instruction",
                "ReAct loop format instruction injected per turn",
                """Follow this reasoning format:
Thought: <your reasoning about what to do next>
Action: <tool name and why you chose it>
Observation: <what you learned from the tool result>
... (repeat as needed)
Final Answer: <clear summary of findings>""",
            ),
            (
                "aml_routing_hint",
                "Context injected by the frontend orchestrator before routing",
                "The user is working in the AML monitoring system. Focus on transaction analysis, alerts, and compliance rules.",
            ),
            (
                "rule_parser_system",
                "System prompt for the existing rule_parser LangGraph nodes",
                """You are an expert Python programmer specialized in financial compliance systems.
Given a financial rule in plain English, convert it into a Python function that takes a Transaction object
and returns True if the rule is triggered, False otherwise.
The generated code must follow this format:
def apply_rule(transaction: Transaction) -> bool:
    return <condition>
Ensure the code is syntactically correct and uses Transaction attributes properly.""",
            ),
        ]

        for name, description, content in defaults:
            await asyncio.to_thread(
                lambda n=name, d=description, ct=content: c.table("prompts").upsert(
                    {"name": n, "description": d, "content": ct},
                    ignore_duplicates=True,
                ).execute()
            )
        logger.info("Default prompts seeded")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _coerce_datetimes(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert datetime objects to ISO strings for PostgREST compatibility."""
    out = {}
    for k, v in data.items():
        if isinstance(v, datetime):
            out[k] = v.isoformat()
        else:
            out[k] = v
    return out
