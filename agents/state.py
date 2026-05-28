"""
State schema for the lead generation agent workflow.
Defines the shared state passed between LangGraph nodes.
"""
from typing import TypedDict, List, Optional, Annotated
from operator import add


class LeadData(TypedDict):
    """Structured lead information extracted from conversations."""
    name: Optional[str]
    email: Optional[str]
    company: Optional[str]
    job_title: Optional[str]
    phone: Optional[str]
    industry: Optional[str]
    budget: Optional[str]
    timeline: Optional[str]
    pain_points: List[str]


class AgentState(TypedDict):
    """
    Shared state for the planner-executor-verifier workflow.

    Flows through the graph: planner -> executor -> verifier -> (loop or end)
    """
    # Input
    user_message: str
    conversation_history: Annotated[List[dict], add]
    language: str  # "en" or "es"

    # Planner output
    plan: List[str]
    current_step: int

    # Executor output
    extracted_lead: LeadData
    tool_results: Annotated[List[dict], add]
    retrieved_context: List[str]

    # Verifier output
    is_valid: bool
    confidence_score: float
    validation_notes: List[str]

    # Final output
    response: str
    lead_qualified: bool
    salesforce_record_id: Optional[str]

    # Control flow
    retry_count: int
    max_retries: int
