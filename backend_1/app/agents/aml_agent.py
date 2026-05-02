"""
AML Monitoring ReAct Agent

LangGraph state machine:
  agent_node → should_continue → tool_node (loop) | END
"""

import json
import operator
import os
import logging
from typing import Annotated, Any, Dict, List, Optional, TypedDict

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from app.database.connection import PostgresDatabase
from app.agents.aml_tools import (
    create_rule,
    get_alerts,
    get_all_rules,
    get_customer_profile,
    get_customer_relationships,
    get_risk_summary,
    get_transaction,
    ingest_regulatory_notice,
    run_rules_on_transaction,
    search_transactions,
)

logger = logging.getLogger(__name__)

TOOLS = [
    search_transactions,
    get_transaction,
    get_alerts,
    get_risk_summary,
    get_customer_profile,
    get_customer_relationships,
    run_rules_on_transaction,
    create_rule,
    get_all_rules,
    ingest_regulatory_notice,
]

_DEFAULT_SYSTEM_PROMPT = """You are an expert AML (Anti-Money Laundering) monitoring agent for a financial institution.
You have access to tools to investigate transactions, customers, and compliance rules.
Reason step by step. When you have enough information, give a clear concise final answer."""

MAX_ITERATIONS = 10


class AMLAgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    thought_process: str
    tool_calls_log: List[Dict[str, Any]]


def _get_llm() -> ChatOpenAI:
    llm = ChatOpenAI(
        model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
        api_key=os.getenv("GROQ_API_KEY"),
        base_url=os.getenv("GROQ_API_BASE"),
        temperature=0.1,
    )
    return llm.bind_tools(TOOLS)


async def _load_system_prompt() -> str:
    try:
        row = await PostgresDatabase.get_prompt("aml_system")
        if row and row.get("content"):
            return row["content"]
    except Exception:
        pass
    return _DEFAULT_SYSTEM_PROMPT


async def agent_node(state: AMLAgentState) -> Dict[str, Any]:
    system_prompt = await _load_system_prompt()
    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    llm = _get_llm()
    response = await llm.ainvoke(messages)

    thought = ""
    if isinstance(response, AIMessage):
        if response.content:
            thought += f"💭 Thought: {str(response.content)[:400]}\n"
        if getattr(response, "tool_calls", None):
            for tc in response.tool_calls:
                args_str = json.dumps(tc.get("args", {}), default=str)[:150]
                thought += f"🔧 Action: {tc['name']}({args_str})\n"

    return {
        "messages": [response],
        "thought_process": state.get("thought_process", "") + thought,
    }


async def tool_node_wrapper(state: AMLAgentState) -> Dict[str, Any]:
    tn = ToolNode(TOOLS)
    result = await tn.ainvoke(state)

    last_ai: Optional[AIMessage] = None
    for msg in reversed(state["messages"]):
        if isinstance(msg, AIMessage):
            last_ai = msg
            break

    ai_tool_calls: Dict[str, Dict] = {}
    if last_ai and hasattr(last_ai, "tool_calls"):
        for tc in last_ai.tool_calls:
            ai_tool_calls[tc["id"]] = {"tool_name": tc["name"], "input": tc.get("args", {})}

    new_logs = []
    observations = ""
    for msg in result.get("messages", []):
        if isinstance(msg, ToolMessage):
            call_info = ai_tool_calls.get(msg.tool_call_id, {})
            output_str = msg.content[:1000] if isinstance(msg.content, str) else str(msg.content)[:1000]
            new_logs.append({
                "tool_name": call_info.get("tool_name", msg.name),
                "input": call_info.get("input", {}),
                "output": output_str,
            })
            observations += f"👁️ Observation [{call_info.get('tool_name', msg.name)}]: {output_str[:300]}\n\n"

    return {
        "messages": result.get("messages", []),
        "tool_calls_log": state.get("tool_calls_log", []) + new_logs,
        "thought_process": state.get("thought_process", "") + observations,
    }


def should_continue(state: AMLAgentState) -> str:
    if len(state["messages"]) > MAX_ITERATIONS * 2:
        return "end"
    last = state["messages"][-1]
    if isinstance(last, AIMessage) and getattr(last, "tool_calls", None):
        return "tools"
    return "end"


def build_aml_agent_graph():
    graph = StateGraph(AMLAgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node_wrapper)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", "end": END})
    graph.add_edge("tools", "agent")
    return graph.compile()


async def run_aml_agent(
    message: str,
    conversation_history: List[Dict[str, str]],
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Entry point called by the /api/agent route."""
    messages: List[BaseMessage] = []
    for turn in conversation_history:
        if turn["role"] == "user":
            messages.append(HumanMessage(content=turn["content"]))
        else:
            messages.append(AIMessage(content=turn["content"]))
    messages.append(HumanMessage(content=message))

    graph = build_aml_agent_graph()
    result = await graph.ainvoke({
        "messages": messages,
        "thought_process": "",
        "tool_calls_log": [],
    })

    # Find last AIMessage with non-empty text content
    response_text = ""
    for msg in reversed(result["messages"]):
        if isinstance(msg, AIMessage) and msg.content and not getattr(msg, "tool_calls", None):
            response_text = msg.content if isinstance(msg.content, str) else str(msg.content)
            break

    if not response_text:
        # All AI messages were tool-call-only; do one final summarization call
        system_prompt = await _load_system_prompt()
        summary_messages = [SystemMessage(content=system_prompt)] + result["messages"] + [
            HumanMessage(content="Based on the information gathered above, provide a concise summary answer to the user's original question.")
        ]
        llm_no_tools = ChatOpenAI(
            model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
            api_key=os.getenv("GROQ_API_KEY"),
            base_url=os.getenv("GROQ_API_BASE"),
            temperature=0.1,
        )
        summary_response = await llm_no_tools.ainvoke(summary_messages)
        response_text = summary_response.content if isinstance(summary_response.content, str) else str(summary_response.content)

    return {
        "response": response_text,
        "tool_calls": result.get("tool_calls_log", []),
        "thought_process": result.get("thought_process", "").strip(),
    }
