"""
Lead Enrichment — augments lead data with external company information.
"""
import logging
from typing import Dict

logger = logging.getLogger("LeadEnrichment")


def enrich_lead_data(company_name: str) -> Dict:
    """
    Enrich a lead with external company data (firmographics).

    In production, integrates with Clearbit, ZoomInfo, or similar APIs.
    Returns enrichment fields to merge into the lead record.
    """
    logger.info(f"Enriching lead for company: {company_name}")

    # Placeholder enrichment — production calls external data provider
    enrichment = {
        "company_size_estimate": _estimate_company_size(company_name),
        "enrichment_source": "internal_heuristic",
    }

    return enrichment


def _estimate_company_size(company_name: str) -> str:
    """Heuristic company size estimate based on name signals."""
    name_lower = company_name.lower()
    if any(kw in name_lower for kw in ["inc", "corp", "corporation", "global", "international"]):
        return "enterprise"
    elif any(kw in name_lower for kw in ["llc", "ltd", "group"]):
        return "mid-market"
    return "small-business"
