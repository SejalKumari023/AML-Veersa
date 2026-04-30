from langgraph.graph import StateGraph
from openai import OpenAI
from typing import Dict
import re
from aml_types import Transaction
from dotenv import load_dotenv
import os

load_dotenv()
MODEL = "groq/compound"


# Agent function to convert rule text to code
def rule_to_code_agent(rule_text: str) -> str:
    """
    Converts a financial rule in text form to a Python function that applies the rule to a transaction.
    The function returns True if the rule is triggered, False otherwise.
    """
    transaction_attributes = dir(Transaction)
    llm_client = OpenAI(
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url=os.getenv("OPENROUTER_API_BASE"),
    )

    system_prompt = f"""
You are an expert Python programmer specialized in financial compliance systems.
Given a financial rule in plain English, convert it into a Python function that takes a Transaction object
and returns True if the rule is triggered, False otherwise.

The Transaction object has the following attributes: {transaction_attributes}

The generated code should follow this format:
def apply_rule(transaction: Transaction) -> bool:
    return <condition>

Ensure the code is syntactically correct and uses the Transaction attributes properly.
"""
    user_prompt = f"Convert the following rule into a Python function:\n\n{rule_text}"
    response = llm_client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=500,
        temperature=0.2,
    )
    return function_code


# LangGraph agent setup
class RuleParserAgent:
    def __init__(self):
        super().__init__()
        self.tools = {"rule_to_code": rule_to_code_agent}

    def __call__(self, state):
        rule_text = state["rule_text"]
        code = self.tools["rule_to_code"](rule_text)
        return {"code": code}


# LangGraph graph setup
def build_rule_parser_graph():
    graph = StateGraph()
    graph.add_node("parse_rule", RuleParserAgent())
    graph.set_entry_point("parse_rule")
    return graph.compile()


# Usage example
if __name__ == "__main__":
    graph = build_rule_parser_graph()
    rule_text = "amount > 10000 and currency == 'USD'"
    result = graph({"rule_text": rule_text})
    print(result["code"])
