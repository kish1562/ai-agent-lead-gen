"""
Entry point for the AI Lead Generation Agent.
Demonstrates running the LangGraph workflow on a sample lead conversation.
"""
import logging
from agents.graph import agent_graph
from config.settings import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
)
logger = logging.getLogger("Main")


def process_lead(user_message: str, language: str = "en", history: list = None) -> dict:
    """
    Run a lead message through the full agent workflow.

    Args:
        user_message: The incoming lead message or web-form submission
        language: "en" or "es"
        history: Prior conversation messages

    Returns:
        Final agent state with response and qualification outcome
    """
    initial_state = {
        "user_message": user_message,
        "conversation_history": history or [],
        "language": language,
        "plan": [],
        "current_step": 0,
        "extracted_lead": {},
        "tool_results": [],
        "retrieved_context": [],
        "is_valid": False,
        "confidence_score": 0.0,
        "validation_notes": [],
        "response": "",
        "lead_qualified": False,
        "salesforce_record_id": None,
        "retry_count": 0,
        "max_retries": settings.max_retries,
    }

    logger.info("Starting agent workflow")
    final_state = agent_graph.invoke(initial_state)

    return final_state


if __name__ == "__main__":
    # Demo: a sample inbound lead
    sample_message = (
        "Hi, I'm Sarah Chen, VP of Engineering at DataCorp Inc. "
        "We're looking for a data pipeline solution and have a budget of $80k. "
        "We need something deployed within the next quarter. "
        "Our main challenge is integrating legacy systems with modern cloud platforms. "
        "Reach me at sarah.chen@datacorp.com"
    )

    result = process_lead(sample_message, language="en")

    print("\n" + "=" * 60)
    print("AGENT RESULT")
    print("=" * 60)
    print(f"Lead Qualified:    {result['lead_qualified']}")
    print(f"Confidence Score:  {result['confidence_score']}")
    print(f"Salesforce ID:     {result.get('salesforce_record_id', 'N/A')}")
    print(f"\nExtracted Lead:    {result['extracted_lead']}")
    print(f"\nResponse:\n{result['response']}")
    print("=" * 60)
