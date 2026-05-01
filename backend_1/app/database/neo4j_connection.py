"""Neo4j graph database connection and ingestion logic."""

import os
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from neo4j import GraphDatabase, Driver, Session
from app.models.transaction import Transaction

logger = logging.getLogger(__name__)


class Neo4jDatabase:
    """Neo4j database connection manager and graph operations."""

    def __init__(self):
        """Initialize Neo4j connection parameters from environment."""
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "aml_neo4j")
        self._driver: Optional[Driver] = None

    async def initialize(self):
        """Initialize Neo4j driver and create constraints."""
        try:
            self._driver = GraphDatabase.driver(
                self.uri, auth=(self.user, self.password)
            )
            # Test connection
            self._driver.verify_connectivity()
            logger.info("Neo4j connection established")

            # Create constraints and indexes
            await self.ensure_constraints()
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j: {e}")
            raise

    async def close(self):
        """Close Neo4j driver connection."""
        if self._driver:
            self._driver.close()
            logger.info("Neo4j connection closed")

    def get_driver(self) -> Driver:
        """Get the Neo4j driver instance."""
        if not self._driver:
            raise RuntimeError("Neo4j driver not initialized")
        return self._driver

    async def ensure_constraints(self):
        """Create uniqueness constraints for graph nodes."""
        constraints = [
            "CREATE CONSTRAINT transaction_id IF NOT EXISTS FOR (t:Transaction) REQUIRE t.transaction_id IS UNIQUE",
            "CREATE CONSTRAINT account_number IF NOT EXISTS FOR (a:Account) REQUIRE a.account_number IS UNIQUE",
            "CREATE CONSTRAINT customer_id IF NOT EXISTS FOR (c:Customer) REQUIRE c.customer_id IS UNIQUE",
            "CREATE CONSTRAINT institution_swift IF NOT EXISTS FOR (i:Institution) REQUIRE i.swift_code IS UNIQUE",
            "CREATE CONSTRAINT jurisdiction_code IF NOT EXISTS FOR (j:Jurisdiction) REQUIRE j.jurisdiction_code IS UNIQUE",
            "CREATE CONSTRAINT country_code IF NOT EXISTS FOR (c:Country) REQUIRE c.country_code IS UNIQUE",
            "CREATE CONSTRAINT currency_code IF NOT EXISTS FOR (c:Currency) REQUIRE c.currency_code IS UNIQUE",
            "CREATE CONSTRAINT channel_name IF NOT EXISTS FOR (c:Channel) REQUIRE c.channel_name IS UNIQUE",
            "CREATE CONSTRAINT product_name IF NOT EXISTS FOR (p:Product) REQUIRE p.product_name IS UNIQUE",
        ]

        with self._driver.session() as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                    logger.debug(f"Created constraint: {constraint}")
                except Exception as e:
                    logger.debug(f"Constraint may already exist: {e}")

    async def ingest_transaction(
        self, transaction_data: Union[Dict[str, Any], Transaction]
    ) -> None:
        """
        Ingest a transaction into the Neo4j graph database.

        Args:
            transaction_data: Either a Transaction model instance or a dict that can be converted to one

        Creates nodes for:
        - Transaction
        - Accounts (originator, beneficiary)
        - Customers (if available)
        - Institutions (originator, beneficiary)
        - Jurisdictions (originator, beneficiary)
        - Countries
        - Currency
        - Channel
        - Product
        - Counterparty (if applicable)

        Creates relationships between these entities.
        """
        # Convert to Transaction model if dict
        if isinstance(transaction_data, dict):
            try:
                txn = Transaction(**transaction_data)
            except Exception as e:
                logger.error(f"Failed to validate transaction data: {e}")
                return
        else:
            txn = transaction_data

        with self._driver.session() as session:
            # Main ingestion query
            query = """
            // Create or merge transaction node
            MERGE (t:Transaction {transaction_id: $transaction_id})
            SET t.amount = $amount,
                t.narrative = $narrative,
                t.transaction_type = $transaction_type,
                t.ingestion_date = datetime()
            
            // Set transaction_date only if provided (handle null)
            FOREACH (_ IN CASE WHEN $transaction_date IS NOT NULL THEN [1] ELSE [] END |
                SET t.transaction_date = datetime($transaction_date)
            )
            
            // Create or merge originator account
            MERGE (orig_acct:Account {account_number: $originator_account})
            SET orig_acct.name = coalesce($originator_account_name, orig_acct.name),
                orig_acct.country = coalesce($originator_country, orig_acct.country)
            
            // Create or merge beneficiary account
            MERGE (ben_acct:Account {account_number: $beneficiary_account})
            SET ben_acct.name = coalesce($beneficiary_account_name, ben_acct.name),
                ben_acct.country = coalesce($beneficiary_country, ben_acct.country)
            
            // Create relationships from transaction to accounts
            MERGE (t)-[:ORIGINATED_FROM]->(orig_acct)
            MERGE (t)-[:BENEFITS]->(ben_acct)
            
            // Create or merge originator institution
            FOREACH (_ IN CASE WHEN $originator_institution IS NOT NULL THEN [1] ELSE [] END |
                MERGE (orig_inst:Institution {swift_code: $originator_institution})
                SET orig_inst.name = coalesce($originator_institution_name, orig_inst.name)
                MERGE (orig_acct)-[:HELD_AT]->(orig_inst)
            )
            
            // Create or merge beneficiary institution
            FOREACH (_ IN CASE WHEN $beneficiary_institution IS NOT NULL THEN [1] ELSE [] END |
                MERGE (ben_inst:Institution {swift_code: $beneficiary_institution})
                SET ben_inst.name = coalesce($beneficiary_institution_name, ben_inst.name)
                MERGE (ben_acct)-[:HELD_AT]->(ben_inst)
            )
            
            // Create or merge originator jurisdiction
            FOREACH (_ IN CASE WHEN $originator_jurisdiction IS NOT NULL THEN [1] ELSE [] END |
                MERGE (orig_jur:Jurisdiction {jurisdiction_code: $originator_jurisdiction})
                MERGE (t)-[:BOOKED_IN]->(orig_jur)
            )
            
            // Create or merge beneficiary jurisdiction
            FOREACH (_ IN CASE WHEN $beneficiary_jurisdiction IS NOT NULL THEN [1] ELSE [] END |
                MERGE (ben_jur:Jurisdiction {jurisdiction_code: $beneficiary_jurisdiction})
                MERGE (t)-[:SETTLES_IN]->(ben_jur)
            )
            
            // Create or merge originator country
            FOREACH (_ IN CASE WHEN $originator_country IS NOT NULL THEN [1] ELSE [] END |
                MERGE (orig_country:Country {country_code: $originator_country})
                MERGE (orig_acct)-[:LOCATED_IN]->(orig_country)
            )
            
            // Create or merge beneficiary country
            FOREACH (_ IN CASE WHEN $beneficiary_country IS NOT NULL THEN [1] ELSE [] END |
                MERGE (ben_country:Country {country_code: $beneficiary_country})
                MERGE (ben_acct)-[:LOCATED_IN]->(ben_country)
            )
            
            // Create or merge currency
            FOREACH (_ IN CASE WHEN $currency IS NOT NULL THEN [1] ELSE [] END |
                MERGE (curr:Currency {currency_code: $currency})
                MERGE (t)-[:DENOMINATED_IN]->(curr)
            )
            
            // Create or merge channel
            FOREACH (_ IN CASE WHEN $channel IS NOT NULL THEN [1] ELSE [] END |
                MERGE (ch:Channel {channel_name: $channel})
                MERGE (t)-[:THROUGH_CHANNEL]->(ch)
            )
            
            // Create or merge product
            FOREACH (_ IN CASE WHEN $product IS NOT NULL THEN [1] ELSE [] END |
                MERGE (prod:Product {product_name: $product})
                MERGE (t)-[:OF_PRODUCT]->(prod)
            )
            
            // Create or merge originator customer (if available)
            FOREACH (_ IN CASE WHEN $originator_customer_id IS NOT NULL THEN [1] ELSE [] END |
                MERGE (orig_cust:Customer {customer_id: $originator_customer_id})
                SET orig_cust.customer_type = coalesce($originator_customer_type, orig_cust.customer_type),
                    orig_cust.risk_rating = coalesce($originator_customer_risk_rating, orig_cust.risk_rating)
                MERGE (orig_acct)-[:OWNED_BY]->(orig_cust)
                MERGE (t)-[:PARTY_TO {role: 'originator'}]->(orig_cust)
            )
            
            // Create or merge beneficiary customer (if available)
            FOREACH (_ IN CASE WHEN $beneficiary_customer_id IS NOT NULL THEN [1] ELSE [] END |
                MERGE (ben_cust:Customer {customer_id: $beneficiary_customer_id})
                SET ben_cust.customer_type = coalesce($beneficiary_customer_type, ben_cust.customer_type),
                    ben_cust.risk_rating = coalesce($beneficiary_customer_risk_rating, ben_cust.risk_rating)
                MERGE (ben_acct)-[:OWNED_BY]->(ben_cust)
                MERGE (t)-[:PARTY_TO {role: 'beneficiary'}]->(ben_cust)
            )
            
            // Create counterparty if it's a counterparty transaction
            FOREACH (_ IN CASE WHEN $counterparty_name IS NOT NULL THEN [1] ELSE [] END |
                MERGE (cp:Counterparty {name: $counterparty_name})
                SET cp.country = coalesce($counterparty_country, cp.country)
                MERGE (t)-[:INVOLVES_COUNTERPARTY]->(cp)
            )
            """

            # Helper function to format datetime for Neo4j
            def format_datetime(dt_value: Optional[datetime]) -> Optional[str]:
                if dt_value is None:
                    return None
                return dt_value.isoformat()

            # Prepare parameters from Transaction model
            # Use booking_datetime as the main transaction date
            transaction_date = txn.booking_datetime or txn.value_date or txn.timestamp

            params = {
                "transaction_id": txn.transaction_id,
                "amount": float(txn.amount),
                "transaction_date": format_datetime(transaction_date),
                "narrative": txn.narrative,
                "transaction_type": txn.product_type,  # Using product_type as transaction_type
                "originator_account": txn.originator_account,
                "originator_account_name": txn.originator_name,
                "originator_country": txn.originator_country,
                "beneficiary_account": txn.beneficiary_account,
                "beneficiary_account_name": txn.beneficiary_name,
                "beneficiary_country": txn.beneficiary_country,
                "originator_institution": txn.ordering_institution_bic,
                "originator_institution_name": None,  # Not in Transaction model
                "beneficiary_institution": txn.beneficiary_institution_bic,
                "beneficiary_institution_name": None,  # Not in Transaction model
                "originator_jurisdiction": txn.booking_jurisdiction,
                "beneficiary_jurisdiction": None,  # Could be derived from beneficiary_country
                "currency": txn.currency,
                "channel": txn.channel,
                "product": txn.product_type,
                "counterparty_name": txn.fx_counterparty,  # Using FX counterparty
                "counterparty_country": None,  # Not in Transaction model
                # Customer fields - using the transaction's customer as originator
                "originator_customer_id": txn.customer_id,
                "originator_customer_type": txn.customer_type,
                "originator_customer_risk_rating": txn.customer_risk_rating,
                "beneficiary_customer_id": None,  # Not in Transaction model
                "beneficiary_customer_type": None,
                "beneficiary_customer_risk_rating": None,
            }

            try:
                session.run(query, params)
                logger.debug(f"Ingested transaction {txn.transaction_id} into Neo4j")
            except Exception as e:
                logger.error(f"Failed to ingest transaction into Neo4j: {e}")
                # Don't raise - we don't want Neo4j failures to block transaction creation

    async def get_transaction_relationships(
        self, transaction_id: str
    ) -> Dict[str, Any]:
        """
        Query all relationships for a specific transaction.

        Returns a dictionary with all connected nodes and relationships.
        """
        with self._driver.session() as session:
            query = """
            MATCH (t:Transaction {transaction_id: $transaction_id})
            OPTIONAL MATCH (t)-[r1:ORIGINATED_FROM]->(orig_acct:Account)
            OPTIONAL MATCH (t)-[r2:BENEFITS]->(ben_acct:Account)
            OPTIONAL MATCH (orig_acct)-[:HELD_AT]->(orig_inst:Institution)
            OPTIONAL MATCH (ben_acct)-[:HELD_AT]->(ben_inst:Institution)
            OPTIONAL MATCH (t)-[:BOOKED_IN]->(orig_jur:Jurisdiction)
            OPTIONAL MATCH (t)-[:SETTLES_IN]->(ben_jur:Jurisdiction)
            OPTIONAL MATCH (orig_acct)-[:OWNED_BY]->(orig_cust:Customer)
            OPTIONAL MATCH (ben_acct)-[:OWNED_BY]->(ben_cust:Customer)
            OPTIONAL MATCH (t)-[:DENOMINATED_IN]->(curr:Currency)
            OPTIONAL MATCH (t)-[:THROUGH_CHANNEL]->(ch:Channel)
            OPTIONAL MATCH (t)-[:OF_PRODUCT]->(prod:Product)
            OPTIONAL MATCH (t)-[:INVOLVES_COUNTERPARTY]->(cp:Counterparty)
            RETURN t, orig_acct, ben_acct, orig_inst, ben_inst, 
                   orig_jur, ben_jur, orig_cust, ben_cust, 
                   curr, ch, prod, cp
            """

            result = session.run(query, {"transaction_id": transaction_id})
            record = result.single()

            if not record:
                return {}

            return {
                "transaction": dict(record["t"]) if record["t"] else None,
                "originator_account": (
                    dict(record["orig_acct"]) if record["orig_acct"] else None
                ),
                "beneficiary_account": (
                    dict(record["ben_acct"]) if record["ben_acct"] else None
                ),
                "originator_institution": (
                    dict(record["orig_inst"]) if record["orig_inst"] else None
                ),
                "beneficiary_institution": (
                    dict(record["ben_inst"]) if record["ben_inst"] else None
                ),
                "originator_jurisdiction": (
                    dict(record["orig_jur"]) if record["orig_jur"] else None
                ),
                "beneficiary_jurisdiction": (
                    dict(record["ben_jur"]) if record["ben_jur"] else None
                ),
                "originator_customer": (
                    dict(record["orig_cust"]) if record["orig_cust"] else None
                ),
                "beneficiary_customer": (
                    dict(record["ben_cust"]) if record["ben_cust"] else None
                ),
                "currency": dict(record["curr"]) if record["curr"] else None,
                "channel": dict(record["ch"]) if record["ch"] else None,
                "product": dict(record["prod"]) if record["prod"] else None,
                "counterparty": dict(record["cp"]) if record["cp"] else None,
            }

    async def get_account_transactions(
        self, account_number: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get all transactions involving a specific account.
        """
        with self._driver.session() as session:
            query = """
            MATCH (a:Account {account_number: $account_number})
            MATCH (t:Transaction)-[r]-(a)
            RETURN t, type(r) as relationship_type
            ORDER BY t.transaction_date DESC
            LIMIT $limit
            """

            result = session.run(
                query, {"account_number": account_number, "limit": limit}
            )
            transactions = []

            for record in result:
                transaction = dict(record["t"])
                transaction["relationship_type"] = record["relationship_type"]
                transactions.append(transaction)

            return transactions

    async def get_customer_network(
        self, customer_id: str, depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get the network of relationships for a customer up to a certain depth.
        Useful for identifying connected customers and counterparties.
        """
        with self._driver.session() as session:
            query = (
                """
            MATCH path = (c:Customer {customer_id: $customer_id})-[*1..%d]-(connected)
            RETURN path
            LIMIT 100
            """
                % depth
            )

            result = session.run(query, {"customer_id": customer_id})
            paths = []

            for record in result:
                path = record["path"]
                paths.append(
                    {
                        "nodes": [dict(node) for node in path.nodes],
                        "relationships": [
                            {"type": rel.type, "properties": dict(rel)}
                            for rel in path.relationships
                        ],
                    }
                )

            return {"customer_id": customer_id, "network_paths": paths}

    async def get_related_customers(
        self, customer_id: Optional[str] = None, max_depth: int = 5, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Find all customers related through transactions, including indirect relationships.

        Args:
            customer_id: Optional specific customer to start from. If None, finds all customer relationships.
            max_depth: Maximum depth of *transaction hops* to traverse (default 5).
            limit: Maximum number of relationship paths to return (default 100)

        Returns:
            List of relationship paths.
        """
        # Use synchronous session context manager (Neo4j driver doesn't support async context)
        with self._driver.session() as session:
            if customer_id:
                # Find relationships for a specific customer using the pattern:
                # Customer -[]- Account <-[]- Transaction -[]-> Account -[]- Customer
                query = """
                MATCH path = (c1:Customer {customer_id: $customer_id})-[]-(a1:Account)<-[]-(t:Transaction)-[]->(a2:Account)-[]-(c2:Customer)
                WHERE c1 <> c2
                
                WITH c1, c2, collect(DISTINCT t) as transactions, collect(DISTINCT a1) + collect(DISTINCT a2) as all_accounts
                WITH c1, c2, transactions, all_accounts, size(transactions) as depth
                
                RETURN c1, c2, transactions, all_accounts as accounts, depth
                ORDER BY depth DESC
                LIMIT $limit
                """
                params = {
                    "customer_id": customer_id,
                    "limit": limit,
                }
            else:
                # Find all customer relationships using the same pattern
                query = """
                MATCH path = (c1:Customer)-[]-(a1:Account)<-[]-(t:Transaction)-[]->(a2:Account)-[]-(c2:Customer)
                WHERE id(c1) < id(c2)
                
                WITH c1, c2, collect(DISTINCT t) as transactions, collect(DISTINCT a1) + collect(DISTINCT a2) as all_accounts
                WITH c1, c2, transactions, all_accounts, size(transactions) as depth
                
                RETURN c1, c2, transactions, all_accounts as accounts, depth
                ORDER BY depth DESC
                LIMIT $limit
                """
                params = {"limit": limit}

            # Use synchronous session.run() - Neo4j Python driver doesn't have async run
            result = session.run(query, params)

            relationships = []
            # Iterate synchronously through results
            for record in result:
                # Access node properties directly (they're already dicts in neo4j 5.x)
                customer1 = dict(record["c1"])
                customer2 = dict(record["c2"])
                transactions = [dict(t) for t in record["transactions"]]
                accounts = [dict(a) for a in record["accounts"]]
                depth = record["depth"]

                relationships.append(
                    {
                        "customer1": {
                            "customer_id": customer1.get("customer_id"),
                            "customer_type": customer1.get("customer_type"),
                            "risk_rating": customer1.get("risk_rating"),
                        },
                        "customer2": {
                            "customer_id": customer2.get("customer_id"),
                            "customer_type": customer2.get("customer_type"),
                            "risk_rating": customer2.get("risk_rating"),
                        },
                        "depth": depth,
                        "relationship_strength": "direct" if depth == 1 else "indirect",
                        "linking_transactions": [
                            {
                                "transaction_id": t.get("transaction_id"),
                                "amount": t.get("amount"),
                                "currency": t.get("currency"),
                                "transaction_date": t.get("transaction_date"),
                                "narrative": t.get("narrative"),
                            }
                            for t in transactions
                        ],
                        "accounts_involved": [
                            {
                                "account_number": a.get("account_number"),
                                "name": a.get("name"),
                                "country": a.get("country"),
                            }
                            for a in accounts
                        ],
                    }
                )

            return relationships
