"""
Verifier Node — validates the executor's output and decides whether to
finalize the response or loop back for refinement.
"""
import logging
from agents.state import AgentState
from config.settings import settings

logger = logging.getLogger("VerifierNode")


def verifier_node(state: AgentState) -> dict:
    """
    Validates extracted lead data quality and qualification confidence.

    Sets is_valid flag and confidence_score that control workflow routing.
    """
    logger.info("Verifier: validating executor output")

    lead = state.get("extracted_lead", {})
    tool_results = state.get("tool_results", [])

    validation_notes = []
    confidence = 0.0

    # Check 1: Contact info present
    has_contact = bool(lead.get("email") or lead.get("phone"))
    if has_contact:
        confidence += 0.3
    else:
        validation_notes.append("Missing contact information (email/phone)")

    # Check 2: Company identified
    if lead.get("company"):
        confidence += 0.2
    else:
        validation_notes.append("Company not identified")

    # Check 3: Intent/pain points captured
    if lead.get("pain_points"):
        confidence += 0.25
    else:
        validation_notes.append("No clear pain points or intent identified")

    # Check 4: Qualification signals (budget/timeline)
    if lead.get("budget") or lead.get("timeline"):
        confidence += 0.25
    else:
        validation_notes.append("No budget or timeline signals")

    # Get lead score from tool results
    lead_score = 0.0
    for result in tool_results:
        if result.get("step") == "score_lead":
            lead_score = result.get("score", 0)

    is_valid = confidence >= settings.min_confidence_threshold
    lead_qualified = lead_score >= settings.qualification_threshold

    logger.info(f"Verifier: confidence={confidence:.2f}, valid={is_valid}, qualified={lead_qualified}")

    return {
        "is_valid": is_valid,
        "confidence_score": round(confidence, 2),
        "validation_notes": validation_notes,
        "lead_qualified": lead_qualified,
    }


def should_retry(state: AgentState) -> str:
    """
    Routing function: decides whether to retry, finalize, or sync to CRM.

    Returns the name of the next node.
    """
    is_valid = state.get("is_valid", False)
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 2)
    lead_qualified = state.get("lead_qualified", False)

    if is_valid and lead_qualified:
        return "sync_salesforce"
    elif is_valid and not lead_qualified:
        return "respond"
    elif retry_count < max_retries:
        logger.info(f"Retrying (attempt {retry_count + 1}/{max_retries})")
        return "retry"
    else:
        logger.info("Max retries reached, finalizing with current data")
        return "respond"
