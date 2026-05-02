"""
AML Monitoring Agent Tools

Each tool wraps existing database/service logic and returns a JSON string.
These are registered with the LangGraph ReAct agent in aml_agent.py.
"""

import json
import uuid
import logging
from datetime import datetime
from typing import Optional

from langchain_core.tools import tool

from app.database.connection import PostgresDatabase
from app.agents.rule_parser import (
    build_rule_parser_graph,
    parse_function_code,
    apply_rule_to_transaction,
)
from app.models import Transaction

logger = logging.getLogger(__name__)


def _serialize(obj):
    """Convert non-JSON-serialisable types (datetime, Decimal) for json.dumps."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    return str(obj)


@tool
async def search_transactions(
    customer_id: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    status: Optional[str] = None,
    limit: int = 20,
) -> str:
    """Search transactions by customer, amount range, or status. Returns a JSON list of matching transactions."""
    try:
        all_txns = await PostgresDatabase.get_all_transactions(limit=1000)
        results = []
        for txn in all_txns:
            if customer_id and txn.get("customer_id") != customer_id:
                continue
            amount = float(txn.get("amount") or 0)
            if min_amount is not None and amount < min_amount:
                continue
            if max_amount is not None and amount > max_amount:
                continue
            if status and txn.get("status", "").lower() != status.lower():
                continue
            results.append(txn)
            if len(results) >= limit:
                break
        return json.dumps(results[:limit], default=_serialize)
    except Exception as e:
        logger.error(f"search_transactions error: {e}")
        return json.dumps({"error": str(e)})


@tool
async def get_transaction(transaction_id: str) -> str:
    """Get full details of a single transaction by its ID."""
    try:
        txn = await PostgresDatabase.get_transaction(transaction_id)
        if not txn:
            return json.dumps({"error": f"Transaction {transaction_id} not found"})
        return json.dumps(txn, default=_serialize)
    except Exception as e:
        logger.error(f"get_transaction error: {e}")
        return json.dumps({"error": str(e)})


@tool
async def get_alerts(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 20,
) -> str:
    """Get AML alerts, optionally filtered by status (active/resolved) or severity (high/medium/low)."""
    try:
        all_alerts = await PostgresDatabase.get_all_alerts(limit=1000)
        results = []
        for alert in all_alerts:
            if status and alert.get("status", "").lower() != status.lower():
                continue
            if severity and alert.get("severity", "").lower() != severity.lower():
                continue
            results.append(alert)
            if len(results) >= limit:
                break
        return json.dumps(results, default=_serialize)
    except Exception as e:
        logger.error(f"get_alerts error: {e}")
        return json.dumps({"error": str(e)})


@tool
async def get_risk_summary() -> str:
    """Get aggregate risk analytics: transaction counts by risk level and alert counts."""
    try:
        summary = await PostgresDatabase.get_risk_summary()
        return json.dumps(summary, default=_serialize)
    except Exception as e:
        logger.error(f"get_risk_summary error: {e}")
        return json.dumps({"error": str(e)})


@tool
async def get_customer_profile(customer_id: str) -> str:
    """Get the full KYC/AML profile for a customer including accounts and risk rating."""
    try:
        customer = await PostgresDatabase.get_customer(customer_id)
        if not customer:
            return json.dumps({"error": f"Customer {customer_id} not found"})
        accounts = await PostgresDatabase.get_accounts_by_customer(customer_id)
        return json.dumps({"customer": customer, "accounts": accounts}, default=_serialize)
    except Exception as e:
        logger.error(f"get_customer_profile error: {e}")
        return json.dumps({"error": str(e)})


@tool
async def get_customer_relationships(customer_id: str, max_depth: int = 2) -> str:
    """Get the Neo4j relationship graph for a customer showing linked accounts and transactions."""
    try:
        customers_data = await PostgresDatabase.get_all_customers(limit=1000)
        txns_data = await PostgresDatabase.get_all_transactions(limit=1000)

        related_txns = [
            {"transaction_id": t["transaction_id"], "amount": str(t.get("amount", 0)),
             "beneficiary_name": t.get("beneficiary_name"), "originator_name": t.get("originator_name")}
            for t in txns_data
            if t.get("customer_id") == customer_id
        ]

        return json.dumps({
            "customer_id": customer_id,
            "related_transactions": related_txns[:20],
            "total_related_transactions": len(related_txns),
        }, default=_serialize)
    except Exception as e:
        logger.error(f"get_customer_relationships error: {e}")
        return json.dumps({"error": str(e)})


@tool
async def run_rules_on_transaction(transaction_id: str) -> str:
    """Run all active compliance rules against a specific transaction. Returns triggered rules and any new alerts created."""
    try:
        txn_data = await PostgresDatabase.get_transaction(transaction_id)
        if not txn_data:
            return json.dumps({"error": f"Transaction {transaction_id} not found"})

        transaction = Transaction(**txn_data)
        rules = await PostgresDatabase.get_all_rules()

        triggered = []
        alerts_created = 0
        for rule in rules:
            try:
                apply_fn = parse_function_code(rule["function_code"])
                if apply_rule_to_transaction(apply_fn, transaction):
                    alert_data = {
                        "id": str(uuid.uuid4()),
                        "transaction_id": transaction_id,
                        "alert_type": "RULE_VIOLATION",
                        "severity": "medium",
                        "message": f"Rule '{rule['id']}' triggered: {rule.get('rule_text','')[:200]}",
                        "timestamp": datetime.now(),
                        "status": "active",
                    }
                    await PostgresDatabase.insert_alert(alert_data)
                    alerts_created += 1
                    triggered.append({"rule_id": rule["id"], "explanation": rule.get("explanation", "")})
            except Exception as rule_err:
                logger.warning(f"Rule {rule['id']} error: {rule_err}")

        return json.dumps({
            "transaction_id": transaction_id,
            "rules_checked": len(rules),
            "triggered_rules": triggered,
            "alerts_created": alerts_created,
        })
    except Exception as e:
        logger.error(f"run_rules_on_transaction error: {e}")
        return json.dumps({"error": str(e)})


@tool
async def create_rule(rule_text: str, rule_id: Optional[str] = None) -> str:
    """Create a new AML compliance rule from a plain English description using the LangGraph parse→test→refine pipeline."""
    try:
        graph = build_rule_parser_graph()
        result = graph.invoke({"rule_text": rule_text, "all_tests_passed": False})

        if not result.get("function_code"):
            return json.dumps({"error": "Failed to generate rule code"})

        final_rule_id = rule_id or f"RULE-{uuid.uuid4().hex[:8].upper()}"
        await PostgresDatabase.insert_rule(
            rule_id=final_rule_id,
            rule_text=rule_text,
            function_code=result["function_code"],
            explanation=result.get("explanation"),
            attributes_used=result.get("attributes_used", []),
        )
        return json.dumps({
            "rule_id": final_rule_id,
            "explanation": result.get("explanation"),
            "all_tests_passed": result.get("all_tests_passed", False),
        })
    except Exception as e:
        logger.error(f"create_rule error: {e}")
        return json.dumps({"error": str(e)})


@tool
async def get_all_rules() -> str:
    """List all stored compliance rules with their IDs, descriptions, and explanations."""
    try:
        rules = await PostgresDatabase.get_all_rules()
        summary = [
            {
                "id": r["id"],
                "rule_text": r.get("rule_text", ""),
                "explanation": r.get("explanation", ""),
                "created_at": r["created_at"].isoformat() if r.get("created_at") else None,
            }
            for r in rules
        ]
        return json.dumps(summary, default=_serialize)
    except Exception as e:
        logger.error(f"get_all_rules error: {e}")
        return json.dumps({"error": str(e)})


@tool
async def ingest_regulatory_notice(notice_text: str, rule_id: Optional[str] = None) -> str:
    """Parse a regulatory notice (plain text) into a compliance rule using the LangGraph pipeline. Returns the created rule_id."""
    return await create_rule.ainvoke({"rule_text": notice_text, "rule_id": rule_id})
