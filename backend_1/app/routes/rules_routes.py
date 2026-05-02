from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.database.connection import Database, PostgresDatabase
from app.models import Transaction, RuleInput
from app.agents.rule_parser import (
    apply_rule_to_transaction,
    build_rule_parser_graph,
    RuleParserState,
    parse_function_code,
)
import logging
import json
from datetime import datetime
from fastapi import Request
import uuid


logger = logging.getLogger(__name__)

rule_router = APIRouter()


@rule_router.post("/")
async def post_rule(rule_input: RuleInput):
    """Create new rule from text input (accepts large text via JSON body)"""
    try:
        # Run the rule parser graph
        graph = build_rule_parser_graph()
        state = RuleParserState(**{"rule_text": rule_input.rule})
        result = graph.invoke(state)
        logger.info("Rule to code result: %s", result)

        # Save to PostgreSQL if all tests passed
        if result.get("all_tests_passed"):
            # Generate rule_id if not provided (use timestamp-based ID)
            if rule_input.rule_id:
                rule_id = rule_input.rule_id
            else:
                # Generate a simple timestamp-based ID
                from time import time

                rule_id = f"RULE-{int(time() * 1000)}"

            saved_rule_id = await PostgresDatabase.insert_rule(
                rule_id=rule_id,
                rule_text=result["rule_text"],
                function_code=result["function_code"],
                explanation=result.get("explanation"),
                attributes_used=result.get("attributes_used", []),
            )
            logger.info(f"Rule saved to database with ID: {saved_rule_id}")
            result["rule_id"] = saved_rule_id
        else:
            logger.warning("Rule did not pass all tests, not saving to database")

        return {"result": result}
    except Exception as e:
        logger.error(f"Error processing rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@rule_router.get("/")
async def get_all_rules():
    """Get all rules from database"""
    try:
        rules = await PostgresDatabase.get_all_rules()
        return {"rules": rules}
    except Exception as e:
        logger.error(f"Error retrieving rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@rule_router.get("/{rule_id}")
async def get_rule(rule_id: str):
    """Get a specific rule by ID (supports regulatory identifiers like MAS-Notice-626)"""
    try:
        rule = await PostgresDatabase.get_rule(rule_id)
        if rule is None:
            raise HTTPException(status_code=404, detail="Rule not found")
        return {"rule": rule}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving rule {rule_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class RuleUpdateInput(BaseModel):
    rule_text: Optional[str] = None
    function_code: Optional[str] = None
    explanation: Optional[str] = None
    attributes_used: Optional[List[str]] = None


@rule_router.put("/{rule_id}")
async def update_rule(rule_id: str, update: RuleUpdateInput):
    """Update an existing rule"""
    try:
        exists = await PostgresDatabase.get_rule(rule_id)
        if exists is None:
            raise HTTPException(status_code=404, detail="Rule not found")

        updated = await PostgresDatabase.update_rule(
            rule_id=rule_id,
            rule_text=update.rule_text,
            function_code=update.function_code,
            explanation=update.explanation,
            attributes_used=update.attributes_used,
        )
        if not updated:
            raise HTTPException(status_code=400, detail="No fields to update")

        rule = await PostgresDatabase.get_rule(rule_id)
        return {"rule": rule}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating rule {rule_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
