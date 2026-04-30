from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.database.connection import Database, PostgresDatabase
import logging
import json
from datetime import datetime
from app.routes.data_routes import Transaction
from app.agents.rule_parser import build_rule_parser_graph, RuleParserState
from fastapi import Request

logger = logging.getLogger(__name__)

rule_router = APIRouter()


class RuleInput(BaseModel):
    rule: str


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
            rule_id = await PostgresDatabase.insert_rule(
                rule_text=result["rule_text"],
                function_code=result["function_code"],
                explanation=result.get("explanation"),
                attributes_used=result.get("attributes_used", []),
            )
            logger.info(f"Rule saved to database with ID: {rule_id}")
            result["rule_id"] = rule_id
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
async def get_rule(rule_id: int):
    """Get a specific rule by ID"""
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
