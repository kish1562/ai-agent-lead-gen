"""
LangGraph workflow definition for the lead generation agent.
Wires together planner -> executor -> verifier with conditional routing.
"""
import logging
from langgraph.graph import StateGraph, END
from agents.state import AgentState
from agents.planner import planner_node
from agents.executor import executor_node
from agents.verifier import verifier_node, should_retry
from tools.salesforce_mcp import sync_to_salesforce
from config.settings import settings

logger = logging.getLogger("AgentGraph")


def respond_node(state: AgentState) -> dict:
    """Generate the final response to the lead based on qualification outcome."""
    from openai import OpenAI
    client = OpenAI(api_key=settings.openai_api_key)

    lead = state.get("extracted_lead", {})
    qualified = state.get("lead_qualified", False)
    language = state.get("language", "en")
    context = state.get("retrieved_context", [])

    lang_instruction = "Respond in Spanish." if language == "es" else "Respond in English."

    system_prompt = f"""You are a helpful sales assistant. {lang_instruction}
Generate a warm, professional response to the lead.
{"Thank them and explain next steps since they're qualified." if qualified else "Ask a follow-up question to gather missing qualification info."}
Use this context if relevant: {' '.join(context[:2])}"""

    response = client.chat.completions.create(
        model=settings.executor_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Lead data: {lead}"}
        ],
        temperature=0.6,
    )

    return {"response": response.choices[0].message.content.strip()}


def sync_salesforce_node(state: AgentState) -> dict:
    """Sync the qualified lead to Salesforce via MCP server."""
    lead = state.get("extracted_lead", {})
    record_id = sync_to_salesforce(lead)
    logger.info(f"Synced lead to Salesforce: {record_id}")
    return {"salesforce_record_id": record_id}


def retry_node(state: AgentState) -> dict:
    """Increment retry counter before looping back to planner."""
    return {"retry_count": state.get("retry_count", 0) + 1}


def build_agent_graph() -> StateGraph:
    """
    Construct the lead generation agent workflow graph.

    Flow:
        planner -> executor -> verifier -> [retry | respond | sync_salesforce]
        retry -> planner (loop)
        sync_salesforce -> respond -> END
    """
    workflow = StateGraph(AgentState)

    # Register nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("executor", executor_node)
    workflow.add_node("verifier", verifier_node)
    workflow.add_node("retry", retry_node)
    workflow.add_node("respond", respond_node)
    workflow.add_node("sync_salesforce", sync_salesforce_node)

    # Define edges
    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "executor")
    workflow.add_edge("executor", "verifier")

    # Conditional routing from verifier
    workflow.add_conditional_edges(
        "verifier",
        should_retry,
        {
            "retry": "retry",
            "respond": "respond",
            "sync_salesforce": "sync_salesforce",
        }
    )

    workflow.add_edge("retry", "planner")
    workflow.add_edge("sync_salesforce", "respond")
    workflow.add_edge("respond", END)

    return workflow.compile()


# Compiled graph singleton
agent_graph = build_agent_graph()
