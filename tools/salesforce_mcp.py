"""
Salesforce MCP Integration — creates and updates leads via MCP server.
Uses the Model Context Protocol to interact with Salesforce as a tool endpoint.
"""
import logging
import requests
from typing import Optional
from agents.state import LeadData
from config.settings import settings

logger = logging.getLogger("SalesforceMCP")


class SalesforceMCPClient:
    """Client for interacting with Salesforce through an MCP server endpoint."""

    def __init__(self):
        self.mcp_url = settings.salesforce_mcp_url
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {settings.salesforce_mcp_token}",
            "Content-Type": "application/json",
        })

    def create_lead(self, lead: LeadData) -> Optional[str]:
        """
        Create a new lead in Salesforce via MCP tool call.

        Returns the Salesforce record ID, or None on failure.
        """
        payload = {
            "tool": "salesforce_create_lead",
            "arguments": {
                "FirstName": (lead.get("name") or "").split(" ")[0],
                "LastName": (lead.get("name") or "Unknown").split(" ")[-1],
                "Email": lead.get("email"),
                "Company": lead.get("company") or "Unknown",
                "Title": lead.get("job_title"),
                "Phone": lead.get("phone"),
                "Industry": lead.get("industry"),
                "Description": "; ".join(lead.get("pain_points", [])),
                "LeadSource": "Web Form - AI Agent",
            }
        }

        try:
            response = self.session.post(
                f"{self.mcp_url}/tools/call",
                json=payload,
                timeout=15
            )
            response.raise_for_status()
            result = response.json()
            record_id = result.get("result", {}).get("id")
            logger.info(f"Created Salesforce lead: {record_id}")
            return record_id
        except requests.RequestException as e:
            logger.error(f"Failed to create Salesforce lead: {e}")
            return None

    def update_lead(self, record_id: str, updates: dict) -> bool:
        """Update an existing Salesforce lead via MCP."""
        payload = {
            "tool": "salesforce_update_lead",
            "arguments": {"Id": record_id, **updates}
        }
        try:
            response = self.session.post(
                f"{self.mcp_url}/tools/call",
                json=payload,
                timeout=15
            )
            response.raise_for_status()
            logger.info(f"Updated Salesforce lead: {record_id}")
            return True
        except requests.RequestException as e:
            logger.error(f"Failed to update lead {record_id}: {e}")
            return False


# Module-level client
_client = None


def sync_to_salesforce(lead: LeadData) -> Optional[str]:
    """Convenience function to sync a lead to Salesforce."""
    global _client
    if _client is None:
        _client = SalesforceMCPClient()
    return _client.create_lead(lead)
