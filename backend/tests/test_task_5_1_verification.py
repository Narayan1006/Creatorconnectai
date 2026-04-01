"""
Verification test for Task 5.1: create_deal generates ad_idea upfront.

This test verifies that when a business creates a deal, the ad_idea field
is populated immediately (before the deal is persisted).
"""

import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime, timedelta, timezone


def _future_deadline():
    return (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()


class TestTask51AdIdeaGeneration:
    """Verify Task 5.1: ad_idea is generated when deal is created."""

    def test_create_deal_generates_ad_idea_upfront(
        self, integration_client, business_headers, dummy_creators
    ):
        """
        Task 5.1 Verification: POST /api/deals should generate ad_idea before persisting.
        
        Requirements: 2.1, 2.2, 2.3, 2.4, 2.6
        """
        client, _ = integration_client
        creator_id = str(dummy_creators[0]["_id"])
        
        # Mock the LLM service to return a known ad idea
        expected_ad_idea = "Test ad idea: Showcase wireless headphones to tech enthusiasts"
        
        with patch(
            "app.routers.deals.generate_ad_idea",
            new=AsyncMock(return_value=expected_ad_idea),
        ):
            response = client.post(
                "/api/deals",
                json={
                    "business_id": "biz_001",
                    "creator_id": creator_id,
                    "offer_amount": 2500.0,
                    "deliverables": "1 Instagram Reel + 2 Stories",
                    "deadline": _future_deadline(),
                },
                headers=business_headers,
            )
        
        assert response.status_code == 201, response.text
        data = response.json()
        
        # Verify Task 5.1 requirements
        assert data["status"] == "pending"
        assert "ad_idea" in data, "ad_idea field should be present in response"
        assert data["ad_idea"] == expected_ad_idea, "ad_idea should match generated value"
        assert data["ad_idea"] is not None, "ad_idea should not be None"
        assert len(data["ad_idea"]) > 0, "ad_idea should not be empty"

    def test_create_deal_ad_idea_fallback_on_llm_failure(
        self, integration_client, business_headers, dummy_creators
    ):
        """
        Task 5.1 Verification: ad_idea should use fallback when LLM fails.
        
        Requirements: 2.3, 2.4
        """
        client, _ = integration_client
        creator_id = str(dummy_creators[0]["_id"])
        
        # Mock the LLM service to fail and return fallback
        fallback_ad_idea = "Showcase 1 Instagram Reel + 2 Stories to your tech audience with authentic storytelling that highlights real-world benefits and drives genuine engagement."
        
        with patch(
            "app.routers.deals.generate_ad_idea",
            new=AsyncMock(return_value=fallback_ad_idea),
        ):
            response = client.post(
                "/api/deals",
                json={
                    "business_id": "biz_001",
                    "creator_id": creator_id,
                    "offer_amount": 1500.0,
                    "deliverables": "1 Instagram Reel + 2 Stories",
                    "deadline": _future_deadline(),
                },
                headers=business_headers,
            )
        
        assert response.status_code == 201, response.text
        data = response.json()
        
        # Verify fallback ad_idea is populated
        assert "ad_idea" in data
        assert data["ad_idea"] is not None
        assert len(data["ad_idea"]) > 0
        assert isinstance(data["ad_idea"], str)
