"""
Unit tests for the lead generation agent components.
Run with: pytest tests/test_agent.py
"""
import pytest
from agents.executor import _calculate_lead_score
from agents.verifier import should_retry
from tools.lead_enrichment import _estimate_company_size


class TestLeadScoring:
    """Tests for lead scoring logic."""

    def test_complete_lead_high_score(self):
        lead = {
            "email": "a@b.com", "company": "Acme", "job_title": "CTO",
            "budget": "$80k", "timeline": "Q1", "industry": "tech",
            "pain_points": ["integration", "scaling"]
        }
        score = _calculate_lead_score(lead)
        assert score >= 90

    def test_minimal_lead_low_score(self):
        lead = {"email": "a@b.com", "pain_points": []}
        score = _calculate_lead_score(lead)
        assert score <= 30

    def test_empty_lead_zero_score(self):
        score = _calculate_lead_score({"pain_points": []})
        assert score == 0

    def test_score_capped_at_100(self):
        lead = {
            "email": "a@b.com", "company": "Acme", "job_title": "CTO",
            "budget": "$80k", "timeline": "Q1", "industry": "tech",
            "phone": "555-1234",
            "pain_points": ["a", "b", "c", "d", "e", "f"]
        }
        score = _calculate_lead_score(lead)
        assert score <= 100


class TestVerifierRouting:
    """Tests for the verifier routing logic."""

    def test_qualified_lead_syncs_salesforce(self):
        state = {"is_valid": True, "lead_qualified": True, "retry_count": 0, "max_retries": 2}
        assert should_retry(state) == "sync_salesforce"

    def test_valid_unqualified_responds(self):
        state = {"is_valid": True, "lead_qualified": False, "retry_count": 0, "max_retries": 2}
        assert should_retry(state) == "respond"

    def test_invalid_retries(self):
        state = {"is_valid": False, "lead_qualified": False, "retry_count": 0, "max_retries": 2}
        assert should_retry(state) == "retry"

    def test_max_retries_responds(self):
        state = {"is_valid": False, "lead_qualified": False, "retry_count": 2, "max_retries": 2}
        assert should_retry(state) == "respond"


class TestEnrichment:
    """Tests for lead enrichment heuristics."""

    def test_enterprise_detection(self):
        assert _estimate_company_size("Microsoft Corporation") == "enterprise"
        assert _estimate_company_size("Global Tech Inc") == "enterprise"

    def test_midmarket_detection(self):
        assert _estimate_company_size("Acme LLC") == "mid-market"

    def test_small_business_default(self):
        assert _estimate_company_size("Joe's Shop") == "small-business"
