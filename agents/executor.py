"""
Executor Node — executes each step in the plan using available tools.
"""
import json
import logging
from openai import OpenAI
from agents.state import AgentState, LeadData
from tools.rag_retriever import RAGRetriever
from tools.lead_enrichment import enrich_lead_data
from config.settings import settings

logger = logging.getLogger("ExecutorNode")

client = OpenAI(api_key=settings.openai_api_key)
rag = RAGRetriever()


EXTRACTION_PROMPT = """Extract structured lead information from the conversation.
Return a JSON object with these fields (use null if not found):
{
  "name": str, "email": str, "company": str, "job_title": str,
  "phone": str, "industry": str, "budget": str, "timeline": str,
  "pain_points": [str]
}
Return ONLY valid JSON."""


def executor_node(state: AgentState) -> dict:
    """
    Executes the planned steps: extraction, retrieval, enrichment, scoring.

    Returns updated state with extracted lead data, tool results, and context.
    """
    logger.info("Executor: running plan steps")

    plan = state["plan"]
    user_message = state["user_message"]
    history = state.get("conversation_history", [])
    conversation = "\n".join([f"{m['role']}: {m['content']}" for m in history])
    conversation += f"\nuser: {user_message}"

    extracted_lead = state.get("extracted_lead", {})
    tool_results = []
    retrieved_context = []

    for step in plan:
        logger.info(f"Executing step: {step}")

        if step == "extract_contact_info" or step == "identify_intent":
            extracted_lead = _extract_lead_info(conversation)
            tool_results.append({"step": step, "status": "completed"})

        elif step == "retrieve_context":
            query = extracted_lead.get("industry") or user_message
            retrieved_context = rag.retrieve(query, top_k=3)
            tool_results.append({
                "step": step,
                "status": "completed",
                "results_count": len(retrieved_context)
            })

        elif step == "enrich_lead":
            if extracted_lead.get("company"):
                enrichment = enrich_lead_data(extracted_lead["company"])
                extracted_lead.update(enrichment)
                tool_results.append({"step": step, "status": "completed"})

        elif step == "score_lead":
            score = _calculate_lead_score(extracted_lead)
            tool_results.append({"step": step, "status": "completed", "score": score})

    return {
        "extracted_lead": extracted_lead,
        "tool_results": tool_results,
        "retrieved_context": retrieved_context,
    }


def _extract_lead_info(conversation: str) -> LeadData:
    """Use LLM to extract structured lead data from conversation text."""
    response = client.chat.completions.create(
        model=settings.executor_model,
        messages=[
            {"role": "system", "content": EXTRACTION_PROMPT},
            {"role": "user", "content": conversation}
        ],
        temperature=0.1,
        response_format={"type": "json_object"} if settings.supports_json_mode else None
    )

    try:
        return json.loads(response.choices[0].message.content.strip())
    except json.JSONDecodeError:
        logger.warning("Extraction returned invalid JSON")
        return {"pain_points": []}


def _calculate_lead_score(lead: LeadData) -> float:
    """Score a lead 0-100 based on completeness and qualification signals."""
    score = 0.0
    weights = {
        "email": 20, "company": 15, "job_title": 15,
        "budget": 20, "timeline": 15, "industry": 10
    }
    for field, weight in weights.items():
        if lead.get(field):
            score += weight

    if lead.get("pain_points"):
        score += min(len(lead["pain_points"]) * 2.5, 5)

    return round(min(score, 100), 1)
