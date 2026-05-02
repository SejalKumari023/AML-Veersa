from langgraph.graph import StateGraph, END
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from typing import Mapping, TypedDict, Dict, Any, Optional
from app.models.transaction import Transaction
from dotenv import load_dotenv
import os
from rich import print

load_dotenv()
MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


class RuleParserState(TypedDict):
    rule_text: str
    function_code: Optional[str]
    attributes_used: Optional[list[str]]
    explanation: Optional[str]
    test_cases: Optional[
        list[Dict[str, Any]]
    ]  # List of dicts with 'transaction' and 'should_trigger'
    all_tests_passed: bool


# Structured output schema
class RuleCodeOutput(BaseModel):
    """Structured output for rule-to-code conversion"""

    model_config = ConfigDict(populate_by_name=True)

    function_code: str = Field(
        description="The Python function code that implements the rule",
        alias="function",
    )
    explanation: str = Field(description="Brief explanation of how the rule works")
    attributes_used: list[str] = Field(
        description="List of Transaction attributes used in the rule"
    )
    rule_text: str = Field(description="The original rule text that was converted", default="")

    @model_validator(mode="before")
    @classmethod
    def normalize_keys(cls, data):
        """Accept 'function' or 'function_code' as the code field."""
        if isinstance(data, dict):
            if "function_code" in data and "function" not in data:
                data = {**data, "function": data.pop("function_code")}
        return data

    @field_validator("function_code", mode="after")
    @classmethod
    def validate_function_code(cls, v):
        if not v.strip().startswith("def apply_rule"):
            raise ValueError('Function must start with "def apply_rule"')
        return v


class TransactionTestPair(BaseModel):
    """A transaction and whether it should trigger the rule"""

    transaction: Transaction
    should_trigger: bool = Field(
        description="Whether this transaction should trigger the rule"
    )

    @model_validator(mode="before")
    @classmethod
    def fill_transaction_defaults(cls, data):
        """Fill required Transaction fields with defaults when LLM omits them."""
        if isinstance(data, dict) and "transaction" in data:
            t = data["transaction"]
            if isinstance(t, dict):
                defaults = {
                    "transaction_id": "TEST-001",
                    "booking_jurisdiction": "CH",
                    "amount": 0.0,
                    "currency": "USD",
                    "customer_id": "CUST-001",
                    "timestamp": "2024-01-01T00:00:00",
                }
                for k, v in defaults.items():
                    t.setdefault(k, v)
        return data


class RuleTestCase(BaseModel):
    """Structured output for test case generation"""

    model_config = ConfigDict(populate_by_name=True)

    transaction_test_case: list[TransactionTestPair] = Field(
        description="A list of transaction test cases with expected results",
        alias="transactions",
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_keys(cls, data):
        if isinstance(data, dict):
            # Accept various field names the LLM might use
            for src in ("test_cases", "transaction_test_cases", "cases"):
                if src in data and "transactions" not in data:
                    data = {**data, "transactions": data.pop(src)}
                    break
            if "transaction_test_case" in data and "transactions" not in data:
                data = {**data, "transactions": data.pop("transaction_test_case")}
        return data


# Helper functions
def parse_function_code(function_code: str):
    """
    Parse and execute function code to extract the apply_rule function.

    Args:
        function_code: String containing the Python function definition

    Returns:
        The apply_rule function object

    Raises:
        ValueError: If function_code is empty or apply_rule is not defined
    """
    if not function_code:
        raise ValueError("No function code provided")

    # Prepare namespaces
    local_namespace = {}
    global_namespace = {"Transaction": Transaction}

    # Execute the function code to define apply_rule
    exec(function_code, global_namespace, local_namespace)

    # Retrieve the apply_rule function
    apply_rule = local_namespace.get("apply_rule")
    if not apply_rule:
        raise ValueError("Function apply_rule not defined in the provided code.")

    return apply_rule


def apply_rule_to_transaction(apply_rule_func, transaction: Transaction) -> bool:
    """
    Apply a rule function to a transaction.

    Args:
        apply_rule_func: The apply_rule function to execute
        transaction: Transaction object to test

    Returns:
        Boolean indicating whether the rule was triggered
    """
    try:
        return apply_rule_func(transaction)
    except Exception as e:
        print(f"Error applying rule to transaction: {e}")
        raise


# Agent function to convert rule text to code
def rule_to_code_agent(state: RuleParserState) -> Dict[str, Any]:
    """
    Converts a financial rule in text form to a Python function that applies the rule to a transaction.
    The function returns True if the rule is triggered, False otherwise.

    Uses structured output to ensure consistent formatting.
    """
    transaction_attributes = dir(Transaction)

    # Initialize LangChain chat model with structured output
    llm = ChatOpenAI(
        model=MODEL,
        api_key=os.getenv("GROQ_API_KEY"),
        base_url=os.getenv("GROQ_API_BASE"),
        temperature=0.1,
    )

    # Create structured output parser
    structured_llm = llm.with_structured_output(RuleCodeOutput, method="json_mode")

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
Provide a brief explanation and list the attributes used.

Your JSON response MUST use exactly these field names: "function" (the Python code string), "explanation" (brief description string), "attributes_used" (array of attribute name strings), "rule_text" (the original rule text string).""",
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
    # Ensure result is RuleCodeOutput and convert to dict
    if isinstance(result, dict):
        parsed_result = RuleCodeOutput.model_validate(result)
    elif isinstance(result, RuleCodeOutput):
        parsed_result = result
    elif isinstance(result, BaseModel):
        parsed_result = RuleCodeOutput.model_validate(result.model_dump())
    else:
        raise TypeError("Unexpected result type from chain.invoke")

    return {
        "function_code": parsed_result.function_code,
        "explanation": parsed_result.explanation,
        "attributes_used": parsed_result.attributes_used,
    }


def test_rule_on_transaction(state: RuleParserState) -> Dict[str, Any]:
    """
    Tests the generated rule function code on a sample transaction.
    Returns whether the rule was triggered.
    """
    function_code = state["function_code"]
    if not function_code:
        raise ValueError("No function code provided in state")
    # use llm to create a sample transaction that would trigger the rule
    llm = ChatOpenAI(
        model=MODEL,
        api_key=os.getenv("GROQ_API_KEY"),
        base_url=os.getenv("GROQ_API_BASE"),
        temperature=0.1,
    )
    structured_llm = llm.with_structured_output(RuleTestCase, method="json_mode")

    transaction_attributes = dir(Transaction)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an expert in financial transactions and compliance.
Given a rule function code that applies to a Transaction object, create sample Transactions
to test the rule. Include transactions that trigger the rule (return True) and ones that do not.

The Transaction object has the following attributes: {transaction_attributes}

Your JSON response MUST use exactly this structure: a "transactions" array where each element has
a "transaction" object (with transaction fields) and a "should_trigger" boolean.""",
            ),
            (
                "user",
                "Function code: {function_code}\n\nCreate 5 transactions that trigger the rule (should_trigger: true) and 5 that do not (should_trigger: false).",
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
        response = RuleTestCase.model_validate(response)

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

    # Parse the function code to get the apply_rule function

    apply_rule = parse_function_code(function_code)

    # Test the rule on each generated transaction
    tests_passed = 0
    total_tests = 0

    if state["test_cases"]:
        for i, test_case in enumerate(state["test_cases"], start=1):
            transaction = test_case["transaction"]
            expected = test_case["should_trigger"]

            # Apply the rule to the transaction
            try:
                actual = apply_rule_to_transaction(apply_rule, transaction)
            except Exception as e:
                print(f"Error applying rule in test case {i}: {e}")
                actual = False  # Treat as not triggered on error

            # Check if test passed
            passed = expected == actual
            if passed:
                tests_passed += 1
            total_tests += 1

            # Print test result
            print(
                f"Test case {i}: Expected={expected}, Actual={actual}, "
                f"{'✓ PASS' if passed else '✗ FAIL'}"
            )

        # Print summary
        percentage_passed = (tests_passed / total_tests) * 100
        print(f"\n{'='*50}")
        print(
            f"Test Summary: {tests_passed}/{total_tests} passed ({percentage_passed:.2f}%)"
        )
        print(f"{'='*50}\n")

    all_tests_passed = tests_passed == total_tests if total_tests > 0 else False
    print("Tests completed")
    print(f"All tests passed: {all_tests_passed}")

    return {"all_tests_passed": all_tests_passed, "test_cases": state.get("test_cases")}


def refine_rule_code(state: RuleParserState) -> Dict[str, Any]:
    """
    Refines the generated rule function code based on test results.
    """
    llm = ChatOpenAI(
        model=MODEL,
        api_key=os.getenv("GROQ_API_KEY"),
        base_url=os.getenv("GROQ_API_BASE"),
        temperature=0.1,
    )

    # use ruleCodeOutput as structured output
    structured_llm = llm.with_structured_output(RuleCodeOutput, method="json_mode")
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an expert Python programmer specialized in financial compliance systems.
Given a Python function that applies a financial rule to a Transaction object, and the results of test cases,
refine the function code to ensure it passes all test cases. The rule is based on the following description: {rule_text}.
Find out why it may be failing test cases and fix it.

Your JSON response MUST use exactly these field names: "function" (the Python code string), "explanation" (brief description string), "attributes_used" (array of attribute name strings), "rule_text" (the original rule text string).""",
            ),
            (
                "user",
                "Refine the following function code based on the test results:\n\n{function_code}\n\nTest Results: {test_results}",
            ),
        ]
    )
    # Create chain
    chain = prompt | structured_llm

    # Invoke chain to refine function code
    result = chain.invoke(
        {
            "function_code": state.get("function_code"),
            "test_results": state.get("test_cases", []),
            "rule_text": state.get("rule_text"),
        }
    )
    # Return partial state update
    if isinstance(result, dict):
        refined_result = RuleCodeOutput.model_validate(result)
    elif isinstance(result, RuleCodeOutput):
        refined_result = result
    elif isinstance(result, BaseModel):
        refined_result = RuleCodeOutput.model_validate(result.model_dump())
    else:
        raise TypeError("Unexpected result type from chain.invoke")

    return {
        "function_code": refined_result.function_code,
        "explanation": refined_result.explanation,
        "attributes_used": refined_result.attributes_used,
    }


# LangGraph agent setup
class RuleParserAgent:
    def __init__(self):
        super().__init__()
        self.tools = {"rule_to_code": rule_to_code_agent}

    def __call__(self, state):
        print("RuleParserAgent called")
        result = self.tools["rule_to_code"](state)
        return result


class RuleTestingAgent:
    def __init__(self):
        super().__init__()
        self.tools = {"test_rule": test_rule_on_transaction}

    def __call__(self, state):
        print("RuleTestingAgent called")
        result = self.tools["test_rule"](state)
        return result


class RuleRefinerAgent:
    def __init__(self):
        super().__init__()
        self.tools = {"refine_rule": refine_rule_code}

    def __call__(self, state):
        print("RuleRefinerAgent called")
        print(state)
        result = self.tools["refine_rule"](state)
        return result


# LangGraph graph setup
def build_rule_parser_graph():
    def should_continue(state: RuleParserState) -> str:
        """Determine if we should continue refining or end"""
        print("Evaluating should_continue condition")
        print(f"All tests passed: {state.get('all_tests_passed', False)}")
        if state.get("all_tests_passed", False):
            return "end"
        else:
            return "refine_rule"

    graph = StateGraph(RuleParserState)
    graph.add_node("parse_rule", RuleParserAgent())
    graph.add_node("test_rule", RuleTestingAgent())
    graph.add_node("refine_rule", RuleRefinerAgent())
    graph.add_edge("parse_rule", "test_rule")
    graph.add_conditional_edges(
        "test_rule", should_continue, {"end": END, "refine_rule": "refine_rule"}
    )
    graph.add_edge("refine_rule", "test_rule")  # Loop back to test after refining
    graph.set_entry_point("parse_rule")
    return graph.compile()
