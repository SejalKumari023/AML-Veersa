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

            # Create transactions table
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS transactions (
                    transaction_id TEXT PRIMARY KEY,
                    booking_jurisdiction TEXT,
                    regulator TEXT,
                    booking_datetime TIMESTAMP,
                    value_date TIMESTAMP,
                    amount DECIMAL(15, 2) NOT NULL,
                    currency TEXT NOT NULL,
                    channel TEXT,
                    product_type TEXT,
                    originator_name TEXT,
                    originator_account TEXT,
                    originator_country TEXT,
                    beneficiary_name TEXT,
                    beneficiary_account TEXT,
                    beneficiary_country TEXT,
                    swift_mt TEXT,
                    ordering_institution_bic TEXT,
                    beneficiary_institution_bic TEXT,
                    swift_f50_present BOOLEAN,
                    swift_f59_present BOOLEAN,
                    swift_f70_purpose TEXT,
                    swift_f71_charges TEXT,
                    travel_rule_complete BOOLEAN,
                    fx_indicator BOOLEAN,
                    fx_base_ccy TEXT,
                    fx_quote_ccy TEXT,
                    fx_applied_rate DECIMAL(15, 6),
                    fx_market_rate DECIMAL(15, 6),
                    fx_spread_bps DECIMAL(10, 2),
                    fx_counterparty TEXT,
                    customer_id TEXT NOT NULL,
                    customer_type TEXT,
                    customer_risk_rating TEXT,
                    customer_is_pep BOOLEAN,
                    kyc_last_completed TIMESTAMP,
                    kyc_due_date TIMESTAMP,
                    edd_required BOOLEAN,
                    edd_performed BOOLEAN,
                    sow_documented BOOLEAN,
                    purpose_code TEXT,
                    narrative TEXT,
                    is_advised BOOLEAN,
                    product_complex BOOLEAN,
                    client_risk_profile TEXT,
                    suitability_assessed BOOLEAN,
                    suitability_result TEXT,
                    product_has_va_exposure BOOLEAN,
                    va_disclosure_provided BOOLEAN,
                    cash_id_verified BOOLEAN,
                    daily_cash_total_customer DECIMAL(15, 2),
                    daily_cash_txn_count INTEGER,
                    sanctions_screening TEXT,
                    suspicion_determined_datetime TIMESTAMP,
                    str_filed_datetime TIMESTAMP,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'pending',
                    risk_score DECIMAL(5, 2),
                    flags TEXT[],
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            logger.info("Transactions table created/verified")

            # Create alerts table
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    transaction_id TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    status TEXT DEFAULT 'active',
                    assigned_to TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id)
                )
                """
            )
            logger.info("Alerts table created/verified")

            # Create customers table
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS customers (
                    id TEXT PRIMARY KEY,
                    customer_id TEXT UNIQUE NOT NULL,
                    customer_type TEXT NOT NULL,
                    customer_risk_rating TEXT NOT NULL,
                    customer_is_pep BOOLEAN NOT NULL,
                    kyc_last_completed DATE,
                    kyc_due_date DATE,
                    edd_required BOOLEAN DEFAULT FALSE,
                    edd_performed BOOLEAN DEFAULT FALSE,
                    sow_documented BOOLEAN DEFAULT FALSE,
                    client_risk_profile TEXT DEFAULT 'Balanced',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            logger.info("Customers table created/verified")

            # Create accounts table
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS accounts (
                    id TEXT PRIMARY KEY,
                    account_number TEXT UNIQUE NOT NULL,
                    customer_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    country TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
                )
                """
            )
            logger.info("Accounts table created/verified")

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

    # Transaction methods
    @classmethod
    async def insert_transaction(cls, transaction_data: Dict[str, Any]) -> str:
        """Insert a new transaction into the database"""
        if cls.pool is None:
            raise RuntimeError("Database pool not initialized")

        async with cls.pool.acquire() as conn:
            # Build the INSERT query dynamically based on provided fields
            columns = list(transaction_data.keys())
            placeholders = [f"${i+1}" for i in range(len(columns))]
            values = [transaction_data[col] for col in columns]
            query = f"""
                INSERT INTO transactions ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                ON CONFLICT (transaction_id) DO UPDATE SET
                    {', '.join([f"{col} = EXCLUDED.{col}" for col in columns if col != 'transaction_id'])},
                    updated_at = CURRENT_TIMESTAMP
                RETURNING transaction_id
            """

            row = await conn.fetchrow(query, *values)
            logger.info(f"Transaction inserted/updated: {row['transaction_id']}")
            return row["transaction_id"]

    @classmethod
    async def get_transaction(cls, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Get a transaction by ID"""
        if cls.pool is None:
            raise RuntimeError("Database pool not initialized")

        async with cls.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM transactions WHERE transaction_id = $1",
                transaction_id,
            )
            if row:
                return dict(row)
            return None

    @classmethod
    async def get_all_transactions(
        cls, limit: int = 1000, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get all transactions with pagination"""
        if cls.pool is None:
            raise RuntimeError("Database pool not initialized")

        async with cls.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM transactions
                ORDER BY timestamp DESC
                LIMIT $1 OFFSET $2
                """,
                limit,
                offset,
            )
            return [dict(row) for row in rows]

    @classmethod
    async def delete_transaction(cls, transaction_id: str) -> bool:
        """Delete a transaction by ID"""
        if cls.pool is None:
            raise RuntimeError("Database pool not initialized")

        async with cls.pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM transactions WHERE transaction_id = $1",
                transaction_id,
            )
            return result == "DELETE 1"

    # Alert methods
    @classmethod
    async def insert_alert(cls, alert_data: Dict[str, Any]) -> str:
        """Insert a new alert into the database"""
        if cls.pool is None:
            raise RuntimeError("Database pool not initialized")

        async with cls.pool.acquire() as conn:
            columns = list(alert_data.keys())
            placeholders = [f"${i+1}" for i in range(len(columns))]
            values = [alert_data[col] for col in columns]

            query = f"""
                INSERT INTO alerts ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                RETURNING id
            """

            row = await conn.fetchrow(query, *values)
            logger.info(f"Alert inserted: {row['id']}")
            return row["id"]

    @classmethod
    async def get_alert(cls, alert_id: str) -> Optional[Dict[str, Any]]:
        """Get an alert by ID"""
        if cls.pool is None:
            raise RuntimeError("Database pool not initialized")

        async with cls.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM alerts WHERE id = $1",
                alert_id,
            )
            if row:
                return dict(row)
            return None

    @classmethod
    async def get_all_alerts(
        cls, limit: int = 1000, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get all alerts with pagination"""
        if cls.pool is None:
            raise RuntimeError("Database pool not initialized")

        async with cls.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM alerts
                ORDER BY timestamp DESC
                LIMIT $1 OFFSET $2
                """,
                limit,
                offset,
            )
            return [dict(row) for row in rows]

    @classmethod
    async def delete_alert(cls, alert_id: str) -> bool:
        """Delete an alert by ID"""
        if cls.pool is None:
            raise RuntimeError("Database pool not initialized")

        async with cls.pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM alerts WHERE id = $1",
                alert_id,
            )
            return result == "DELETE 1"

    @classmethod
    async def get_risk_summary(cls) -> Dict[str, Any]:
        """Get risk analytics summary"""
        if cls.pool is None:
            raise RuntimeError("Database pool not initialized")

        async with cls.pool.acquire() as conn:
            # Get transaction counts by risk level
            total_transactions = await conn.fetchval(
                "SELECT COUNT(*) FROM transactions"
            )

            high_risk = await conn.fetchval(
                "SELECT COUNT(*) FROM transactions WHERE risk_score >= 70"
            )

            medium_risk = await conn.fetchval(
                "SELECT COUNT(*) FROM transactions WHERE risk_score >= 40 AND risk_score < 70"
            )

            low_risk = await conn.fetchval(
                "SELECT COUNT(*) FROM transactions WHERE risk_score < 40"
            )

            # Get alert counts by status
            active_alerts = await conn.fetchval(
                "SELECT COUNT(*) FROM alerts WHERE status = 'active'"
            )

            resolved_alerts = await conn.fetchval(
                "SELECT COUNT(*) FROM alerts WHERE status = 'resolved'"
            )

            return {
                "total_transactions": total_transactions or 0,
                "high_risk_transactions": high_risk or 0,
                "medium_risk_transactions": medium_risk or 0,
                "low_risk_transactions": low_risk or 0,
                "active_alerts": active_alerts or 0,
                "resolved_alerts": resolved_alerts or 0,
            }

    # Customer methods
    @classmethod
    async def insert_customer(cls, customer_data: Dict[str, Any]) -> str:
        """Insert a new customer into the database"""
        if cls.pool is None:
            raise RuntimeError("Database pool not initialized")

        async with cls.pool.acquire() as conn:
            import uuid

            customer_id = customer_data.get("id") or str(uuid.uuid4())
            columns = list(customer_data.keys())
            if "id" not in columns:
                columns.insert(0, "id")
                customer_data["id"] = customer_id

            placeholders = [f"${i+1}" for i in range(len(columns))]
            values = [customer_data[col] for col in columns]

            query = f"""
                INSERT INTO customers ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                ON CONFLICT (customer_id) DO UPDATE SET
                    {', '.join([f"{col} = EXCLUDED.{col}" for col in columns if col not in ['id', 'customer_id']])},
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """

            row = await conn.fetchrow(query, *values)
            logger.info(f"Customer inserted/updated: {row['id']}")
            return row["id"]

    @classmethod
    async def get_customer(cls, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get a customer by customer_id"""
        if cls.pool is None:
            raise RuntimeError("Database pool not initialized")

        async with cls.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM customers WHERE customer_id = $1",
                customer_id,
            )
            if row:
                return dict(row)
            return None

    @classmethod
    async def get_customer_by_id(cls, id: str) -> Optional[Dict[str, Any]]:
        """Get a customer by internal id"""
        if cls.pool is None:
            raise RuntimeError("Database pool not initialized")

        async with cls.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM customers WHERE id = $1",
                id,
            )
            if row:
                return dict(row)
            return None

    @classmethod
    async def get_all_customers(
        cls, limit: int = 1000, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get all customers with pagination"""
        if cls.pool is None:
            raise RuntimeError("Database pool not initialized")

        async with cls.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM customers
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
                """,
                limit,
                offset,
            )
            return [dict(row) for row in rows]

    @classmethod
    async def delete_customer(cls, customer_id: str) -> bool:
        """Delete a customer by customer_id"""
        if cls.pool is None:
            raise RuntimeError("Database pool not initialized")

        async with cls.pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM customers WHERE customer_id = $1",
                customer_id,
            )
            return result == "DELETE 1"

    # Account methods
    @classmethod
    async def insert_account(cls, account_data: Dict[str, Any]) -> str:
        """Insert a new account into the database"""
        if cls.pool is None:
            raise RuntimeError("Database pool not initialized")

        async with cls.pool.acquire() as conn:
            import uuid

            account_id = account_data.get("id") or str(uuid.uuid4())
            columns = list(account_data.keys())
            if "id" not in columns:
                columns.insert(0, "id")
                account_data["id"] = account_id

            placeholders = [f"${i+1}" for i in range(len(columns))]
            values = [account_data[col] for col in columns]

            query = f"""
                INSERT INTO accounts ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                ON CONFLICT (account_number) DO UPDATE SET
                    {', '.join([f"{col} = EXCLUDED.{col}" for col in columns if col not in ['id', 'account_number']])},
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """

            row = await conn.fetchrow(query, *values)
            logger.info(f"Account inserted/updated: {row['id']}")
            return row["id"]

    @classmethod
    async def get_account(cls, account_number: str) -> Optional[Dict[str, Any]]:
        """Get an account by account_number"""
        if cls.pool is None:
            raise RuntimeError("Database pool not initialized")

        async with cls.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM accounts WHERE account_number = $1",
                account_number,
            )
            if row:
                return dict(row)
            return None

    @classmethod
    async def get_account_by_id(cls, id: str) -> Optional[Dict[str, Any]]:
        """Get an account by internal id"""
        if cls.pool is None:
            raise RuntimeError("Database pool not initialized")

        async with cls.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM accounts WHERE id = $1",
                id,
            )
            if row:
                return dict(row)
            return None

    @classmethod
    async def get_accounts_by_customer(cls, customer_id: str) -> List[Dict[str, Any]]:
        """Get all accounts for a customer"""
        if cls.pool is None:
            raise RuntimeError("Database pool not initialized")

        async with cls.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM accounts WHERE customer_id = $1 ORDER BY created_at DESC",
                customer_id,
            )
            return [dict(row) for row in rows]

    @classmethod
    async def get_all_accounts(
        cls, limit: int = 1000, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get all accounts with pagination"""
        if cls.pool is None:
            raise RuntimeError("Database pool not initialized")

        async with cls.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM accounts
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
                """,
                limit,
                offset,
            )
            return [dict(row) for row in rows]

    @classmethod
    async def delete_account(cls, account_number: str) -> bool:
        """Delete an account by account_number"""
        if cls.pool is None:
            raise RuntimeError("Database pool not initialized")

        async with cls.pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM accounts WHERE account_number = $1",
                account_number,
            )
            return result == "DELETE 1"
