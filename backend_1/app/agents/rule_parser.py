from langgraph.graph import StateGraph
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field, field_validator
from typing import Dict, Optional
from app.routes.data_routes import Transaction
from dotenv import load_dotenv
import os

load_dotenv()
MODEL = "openai/gpt-oss-120b"


# Structured output schema
class RuleCodeOutput(BaseModel):
    """Structured output for rule-to-code conversion"""

    function_code: str = Field(
        description="The Python function code that implements the rule"
    )
    explanation: str = Field(description="Brief explanation of how the rule works")
    attributes_used: list[str] = Field(
        description="List of Transaction attributes used in the rule"
    )
    rule_text: str = Field(description="The original rule text that was converted")

    @field_validator("function_code")
    def validate_function_code(cls, v):
        """Ensure function code starts with def apply_rule"""
        if not v.strip().startswith("def apply_rule"):
            raise ValueError('Function must start with "def apply_rule"')
        return v


# Agent function to convert rule text to code
def rule_to_code_agent(rule_text: str) -> RuleCodeOutput:
    """
    Converts a financial rule in text form to a Python function that applies the rule to a transaction.
    The function returns True if the rule is triggered, False otherwise.

    Uses structured output to ensure consistent formatting.
    """
    transaction_attributes = dir(Transaction)

    # Initialize LangChain chat model with structured output
    llm = ChatOpenAI(
        model=MODEL,
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url=os.getenv("OPENROUTER_API_BASE"),
        temperature=0.7,
    )

    # Create structured output parser
    structured_llm = llm.with_structured_output(RuleCodeOutput)

    # Create prompt template
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f"""You are an expert Python programmer specialized in financial compliance systems.
Given a financial rule in plain English, convert it into a Python function that takes a Transaction object
and returns True if the rule is triggered, False otherwise.

The Transaction object has the following attributes: {transaction_attributes}

The generated code should follow this format:
def apply_rule(transaction: Transaction) -> bool:
    return <condition>

Ensure the code is syntactically correct and uses the Transaction attributes properly.
Provide a brief explanation and list the attributes used.""",
            ),
            (
                "user",
                f"Convert the following rule into a Python function:\n\n{rule_text}",
            ),
        ]
    )
    print("Prompt created for rule_to_code_agent.")
    print(prompt)
    # Create chain
    chain = prompt | structured_llm

    # Invoke with structured output
    result = chain.invoke(
        {"transaction_attributes": transaction_attributes, "rule_text": rule_text}
    )

    # Ensure result is RuleCodeOutput
    if isinstance(result, dict):
        return RuleCodeOutput(**result)
    elif isinstance(result, RuleCodeOutput):
        return result
    elif isinstance(result, BaseModel):
        return RuleCodeOutput.parse_obj(result)
    else:
        raise TypeError("Unexpected result type from chain.invoke")


# LangGraph agent setup
class RuleParserAgent:
    def __init__(self):
        super().__init__()
        self.tools = {"rule_to_code": rule_to_code_agent}

    def __call__(self, state):
        rule_text = state["rule_text"]
        result = self.tools["rule_to_code"](rule_text)
        return {
            "code": result.function_code,
            "explanation": result.explanation,
            "attributes_used": result.attributes_used,
        }


# # LangGraph graph setup
# def build_rule_parser_graph():
#     graph = StateGraph()
#     graph.add_node("parse_rule", RuleParserAgent())
#     graph.set_entry_point("parse_rule")
#     return graph.compile()
