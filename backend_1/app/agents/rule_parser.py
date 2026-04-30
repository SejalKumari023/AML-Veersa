from langgraph.graph import StateGraph
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field, field_validator
from typing import Mapping, TypedDict, Dict, Any, Optional
from app.routes.data_routes import Transaction
from dotenv import load_dotenv
import os
from rich import print

load_dotenv()
MODEL = "openai/gpt-oss-120b"


class RuleParserState(TypedDict):
    rule_text: str
    function_code: Optional[str]
    attributes_used: Optional[list[str]]
    explanation: Optional[str]
    test_cases: Optional[
        list[Dict[str, Any]]
    ]  # List of dicts with 'transaction' and 'should_trigger'


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


class TransactionTestPair(BaseModel):
    """A transaction and whether it should trigger the rule"""

    transaction: Transaction
    should_trigger: bool = Field(
        description="Whether this transaction should trigger the rule"
    )


class RuleTestCase(BaseModel):
    """Structured output for test case generation"""

    transaction_test_case: list[TransactionTestPair] = Field(
        description="A list of transaction test cases with expected results"
    )


# Agent function to convert rule text to code
def rule_to_code_agent(state: RuleParserState) -> RuleCodeOutput:
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
                f"Convert the following rule into a Python function:\n\n{state['rule_text']}",
            ),
        ]
    )
    # Create chain
    chain = prompt | structured_llm

    # Invoke with structured output
    result = chain.invoke(
        {
            "transaction_attributes": transaction_attributes,
            "rule_text": state["rule_text"],
        }
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


def test_rule_on_transaction(state: RuleParserState) -> bool:
    """
    Tests the generated rule function code on a sample transaction.
    Returns whether the rule was triggered.
    """
    function_code = state["function_code"]
    # use llm to create a sample transaction that would trigger the rule
    llm = ChatOpenAI(
        model=MODEL,
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url=os.getenv("OPENROUTER_API_BASE"),
        temperature=0.7,
    )
    structured_llm = llm.with_structured_output(RuleTestCase)

    transaction_attributes = dir(Transaction)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an expert in financial transactions and compliance.
Given a rule function code that applies to a Transaction object, create a sample Transaction
that would trigger the rule (i.e., make the function return True).

The Transaction object has the following attributes: {transaction_attributes}""",
            ),
            (
                "user",
                "Create a mixture of sample Transaction object in JSON format that would trigger this rule and others that will not."
                "Get 5 transactions that would trigger the rule and 5 that would not.",
            ),
        ]
    )
    # Create chain
    chain = prompt | structured_llm

    # Invoke chain to get sample transaction
    response = chain.invoke(
        {
            "function_code": function_code,
            "transaction_attributes": transaction_attributes,
        }
    )

    if isinstance(response, dict):
        response = RuleTestCase(**response)

    if "test_cases" not in state.keys():
        # Convert TransactionTestPair objects to dictionaries
        test_cases_list = []
        for test_pair in response.transaction_test_case:
            test_cases_list.append(
                {
                    "transaction": test_pair.transaction,
                    "should_trigger": test_pair.should_trigger,
                }
            )
        state.update(test_cases=test_cases_list)

    print("Generated test cases:")
    print(state["test_cases"])

    # Prepare local namespace for exec
    local_namespace = {}
    global_namespace = {"Transaction": Transaction}
    print("Global namespace prepared for exec:")
    print(global_namespace)
    # Execute the function code to define apply_rule
    if function_code:
        print("Executing function code:")
        print(function_code)
        exec(function_code, global_namespace, local_namespace)
        print("Local namespace after exec:")
        print(local_namespace)
    else:
        raise ValueError("No function code provided")

    # Retrieve the apply_rule function
    apply_rule = local_namespace.get("apply_rule")
    if not apply_rule:
        raise ValueError("Function apply_rule not defined in the provided code.")

    # Test the rule on each generated transaction
    test_results = []
    tests_passed = 0
    if state["test_cases"]:
        for test_case in state["test_cases"]:
            transaction = test_case["transaction"]
            rule_triggered = apply_rule(transaction)
            test_results.append(rule_triggered)

        for i in range(len(state["test_cases"])):
            expected = state["test_cases"][i]["should_trigger"]
            actual = test_results[i]
            if expected == actual:
                tests_passed += 1
            print(
                f"Test case {i+1}: Expected={expected}, Actual={actual}, {'PASS' if expected == actual else 'FAIL'}"
            )
        print("Test results on generated transactions:")
        print(test_results)
        percentage_passed = (tests_passed / len(state["test_cases"])) * 100
        print(
            f"Tests passed: {tests_passed}/{len(state['test_cases'])} ({percentage_passed:.2f}%)"
        )

    return all(test_results) if test_results else False


# LangGraph agent setup
class RuleParserAgent:
    def __init__(self):
        super().__init__()
        self.tools = {"rule_to_code": rule_to_code_agent}

    def __call__(self, state):
        result = self.tools["rule_to_code"](state)
        state["function_code"] = result.function_code
        state["explanation"] = result.explanation
        state["attributes_used"] = result.attributes_used
        return {
            "function_code": result.function_code,
            "explanation": result.explanation,
            "attributes_used": result.attributes_used,
        }


class RuleTestingAgent:
    def __init__(self):
        super().__init__()
        self.tools = {"test_rule": test_rule_on_transaction}

    def __call__(self, state):
        print("RuleTestingAgent called with state:")
        print(state)
        result = self.tools["test_rule"](state)
        return {"rule_triggered": result}


# LangGraph graph setup
def build_rule_parser_graph():
    graph = StateGraph(RuleParserState)
    graph.add_node("parse_rule", RuleParserAgent())
    graph.add_node("test_rule", RuleTestingAgent())
    graph.add_edge("parse_rule", "test_rule")
    graph.set_entry_point("parse_rule")
    return graph.compile()
