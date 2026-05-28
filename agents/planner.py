"""
Planner Node — decomposes the lead qualification task into actionable steps.
"""
import json
import logging
from openai import OpenAI
from agents.state import AgentState
from config.settings import settings

logger = logging.getLogger("PlannerNode")

client = OpenAI(api_key=settings.openai_api_key)


PLANNER_SYSTEM_PROMPT = """You are a lead qualification planner. Given a user message from a
web-form or conversation, decompose the qualification process into clear, ordered steps.

Output a JSON array of steps. Each step should be one of:
- "extract_contact_info": Pull name, email, company, title
- "identify_intent": Determine the lead's needs and pain points
- "retrieve_context": Search knowledge base for relevant context
- "assess_budget_timeline": Evaluate budget and timeline signals
- "enrich_lead": Augment with external data
- "score_lead": Calculate qualification score

Return ONLY valid JSON, no other text. Example:
["extract_contact_info", "identify_intent", "retrieve_context", "score_lead"]
"""


def planner_node(state: AgentState) -> dict:
    """
    Analyzes the incoming message and produces an execution plan.

    Returns updated state with the plan and reset step counter.
    """
    logger.info("Planner: decomposing task")

    user_message = state["user_message"]
    history = state.get("conversation_history", [])

    context = "\n".join([f"{m['role']}: {m['content']}" for m in history[-5:]])

    response = client.chat.completions.create(
        model=settings.planner_model,
        messages=[
            {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
            {"role": "user", "content": f"Conversation:\n{context}\n\nLatest message: {user_message}"}
        ],
        temperature=0.2,
        response_format={"type": "json_object"} if settings.supports_json_mode else None
    )

    raw = response.choices[0].message.content.strip()

    try:
        # Handle both array and {"steps": [...]} formats
        parsed = json.loads(raw)
        plan = parsed if isinstance(parsed, list) else parsed.get("steps", [])
    except json.JSONDecodeError:
        logger.warning("Planner returned invalid JSON, using default plan")
        plan = ["extract_contact_info", "identify_intent", "retrieve_context", "score_lead"]

    logger.info(f"Planner produced {len(plan)} steps: {plan}")

    return {
        "plan": plan,
        "current_step": 0,
        "retry_count": state.get("retry_count", 0),
    }
