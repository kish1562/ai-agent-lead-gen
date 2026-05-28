"""Configuration settings for the lead generation agent."""
import os
from dataclasses import dataclass


@dataclass
class Settings:
    """Application configuration loaded from environment variables."""

    # OpenAI / LLM
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    planner_model: str = os.getenv("PLANNER_MODEL", "gpt-4o")
    executor_model: str = os.getenv("EXECUTOR_MODEL", "gpt-4o-mini")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    supports_json_mode: bool = True

    # Azure AI Search
    azure_ai_search_endpoint: str = os.getenv("AZURE_AI_SEARCH_ENDPOINT", "")
    azure_ai_search_key: str = os.getenv("AZURE_AI_SEARCH_KEY", "")

    # Salesforce MCP
    salesforce_mcp_url: str = os.getenv("SALESFORCE_MCP_URL", "")
    salesforce_mcp_token: str = os.getenv("SALESFORCE_MCP_TOKEN", "")

    # Agent behavior thresholds
    min_confidence_threshold: float = 0.6
    qualification_threshold: float = 60.0
    max_retries: int = 2


settings = Settings()
