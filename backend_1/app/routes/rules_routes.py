from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.database.connection import Database
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
        graph = build_rule_parser_graph()
        state = RuleParserState(**{"rule_text": rule_input.rule})
        result = graph.invoke(state)
        print("Rule to code result:", result)
        return {"result": result}
    except Exception as e:
        logger.error(f"Error processing rule: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
