"""
Integration tests for counter-related API endpoints.

Tests Task 9: Add API endpoints to deals router
- PUT /api/deals/:id/accept-counter
- PUT /api/deals/:id/reject-counter
- PUT /api/deals/:id/business-counter
"""
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch

import pytest


def _future_deadline() -> str:
    dt = datetime.now(timezone.utc) + timedelta(days=30)
    return dt.isoformat()


class TestCounterEndpoints:
    """Test the counter-related API endpoints."""

    def test_accept_counter_success(
        self, integration_client, business_headers, creator_headers, dummy_creators
    ):
        """Test accepting a countered deal via PUT /api/deals/:id/accept-counter."""
        client, _ = integration_client
        creator_id = str(dummy_creators[0]["_id"])

        # Create deal
        with patch(
            "app.routers.deals.generate_ad_idea",
            new=AsyncMock(return_value="Test ad idea"),
        ):
            create_resp = client.post(
                "/api/deals",
                json={
                    "business_id": "biz_001",
                    "creator_id": creator_id,
                    "offer_amount": 1000.0,
                    "deliverables": "1 Instagram post",
                    "deadline": _future_deadline(),
                },
                headers=business_headers,
            )
        assert create_resp.status_code == 201
        deal_id = create_resp.json()["_id"]

        # Counter the deal
        counter_resp = client.put(
            f"/api/deals/{deal_id}/counter",
            json={
                "message": "I can do this for $1500",
                "counter_amount": 1500.0,
                "counter_deliverables": "1 Instagram post + 2 stories",
            },
            headers=creator_headers,
        )
        assert counter_resp.status_code == 200
        assert counter_resp.json()["status"] == "countered"

        # Accept the counter
        accept_resp = client.put(
            f"/api/deals/{deal_id}/accept-counter",
            headers=business_headers,
        )
        assert accept_resp.status_code == 200
        data = accept_resp.json()
        assert data["status"] == "accepted"
        assert data["offer_amount"] == 1500.0
        assert data["deliverables"] == "1 Instagram post + 2 stories"

    def test_reject_counter_success(
        self, integration_client, business_headers, creator_headers, dummy_creators
    ):
        """Test rejecting a countered deal via PUT /api/deals/:id/reject-counter."""
        client, _ = integration_client
        creator_id = str(dummy_creators[1]["_id"])

        # Create deal
        with patch(
            "app.routers.deals.generate_ad_idea",
            new=AsyncMock(return_value="Test ad idea"),
        ):
            create_resp = client.post(
                "/api/deals",
                json={
                    "business_id": "biz_001",
                    "creator_id": creator_id,
                    "offer_amount": 500.0,
                    "deliverables": "1 TikTok video",
                    "deadline": _future_deadline(),
                },
                headers=business_headers,
            )
        assert create_resp.status_code == 201
        deal_id = create_resp.json()["_id"]

        # Counter the deal
        counter_resp = client.put(
            f"/api/deals/{deal_id}/counter",
            json={"message": "Too low, need $800"},
            headers=creator_headers,
        )
        assert counter_resp.status_code == 200

        # Reject the counter
        reject_resp = client.put(
            f"/api/deals/{deal_id}/reject-counter",
            headers=business_headers,
        )
        assert reject_resp.status_code == 200
        data = reject_resp.json()
        assert data["status"] == "rejected"

    def test_business_counter_success(
        self, integration_client, business_headers, creator_headers, dummy_creators
    ):
        """Test business countering via PUT /api/deals/:id/business-counter."""
        client, _ = integration_client
        creator_id = str(dummy_creators[2]["_id"])

        # Create deal
        with patch(
            "app.routers.deals.generate_ad_idea",
            new=AsyncMock(return_value="Test ad idea"),
        ):
            create_resp = client.post(
                "/api/deals",
                json={
                    "business_id": "biz_001",
                    "creator_id": creator_id,
                    "offer_amount": 1000.0,
                    "deliverables": "1 YouTube video",
                    "deadline": _future_deadline(),
                },
                headers=business_headers,
            )
        assert create_resp.status_code == 201
        deal_id = create_resp.json()["_id"]

        # Creator counters
        counter_resp = client.put(
            f"/api/deals/{deal_id}/counter",
            json={
                "message": "I need $1500",
                "counter_amount": 1500.0,
            },
            headers=creator_headers,
        )
        assert counter_resp.status_code == 200

        # Business counters back
        business_counter_resp = client.put(
            f"/api/deals/{deal_id}/business-counter",
            json={
                "message": "How about $1200?",
                "counter_amount": 1200.0,
            },
            headers=business_headers,
        )
        assert business_counter_resp.status_code == 200
        data = business_counter_resp.json()
        assert data["status"] == "countered"
        assert data["counter_amount"] == 1200.0
        assert len(data["counter_history"]) == 2
        assert data["counter_history"][0]["author"] == "creator"
        assert data["counter_history"][1]["author"] == "business"

    def test_accept_counter_invalid_status_returns_409(
        self, integration_client, business_headers, dummy_creators
    ):
        """Test accepting counter on pending deal returns 409."""
        client, _ = integration_client
        creator_id = str(dummy_creators[3]["_id"])

        # Create deal (status=pending)
        with patch(
            "app.routers.deals.generate_ad_idea",
            new=AsyncMock(return_value="Test ad idea"),
        ):
            create_resp = client.post(
                "/api/deals",
                json={
                    "business_id": "biz_001",
                    "creator_id": creator_id,
                    "offer_amount": 500.0,
                    "deliverables": "1 post",
                    "deadline": _future_deadline(),
                },
                headers=business_headers,
            )
        deal_id = create_resp.json()["_id"]

        # Try to accept counter on pending deal → 409
        accept_resp = client.put(
            f"/api/deals/{deal_id}/accept-counter",
            headers=business_headers,
        )
        assert accept_resp.status_code == 409
        detail = accept_resp.json()["detail"]
        assert detail["current_status"] == "pending"

    def test_reject_counter_invalid_status_returns_409(
        self, integration_client, business_headers, dummy_creators
    ):
        """Test rejecting counter on pending deal returns 409."""
        client, _ = integration_client
        creator_id = str(dummy_creators[4]["_id"])

        # Create deal (status=pending)
        with patch(
            "app.routers.deals.generate_ad_idea",
            new=AsyncMock(return_value="Test ad idea"),
        ):
            create_resp = client.post(
                "/api/deals",
                json={
                    "business_id": "biz_001",
                    "creator_id": creator_id,
                    "offer_amount": 500.0,
                    "deliverables": "1 post",
                    "deadline": _future_deadline(),
                },
                headers=business_headers,
            )
        deal_id = create_resp.json()["_id"]

        # Try to reject counter on pending deal → 409
        reject_resp = client.put(
            f"/api/deals/{deal_id}/reject-counter",
            headers=business_headers,
        )
        assert reject_resp.status_code == 409
        detail = reject_resp.json()["detail"]
        assert detail["current_status"] == "pending"

    def test_business_counter_invalid_status_returns_409(
        self, integration_client, business_headers, dummy_creators
    ):
        """Test business counter on pending deal returns 409."""
        client, _ = integration_client
        creator_id = str(dummy_creators[5]["_id"])

        # Create deal (status=pending)
        with patch(
            "app.routers.deals.generate_ad_idea",
            new=AsyncMock(return_value="Test ad idea"),
        ):
            create_resp = client.post(
                "/api/deals",
                json={
                    "business_id": "biz_001",
                    "creator_id": creator_id,
                    "offer_amount": 500.0,
                    "deliverables": "1 post",
                    "deadline": _future_deadline(),
                },
                headers=business_headers,
            )
        deal_id = create_resp.json()["_id"]

        # Try to business counter on pending deal → 409
        business_counter_resp = client.put(
            f"/api/deals/{deal_id}/business-counter",
            json={"message": "Counter offer"},
            headers=business_headers,
        )
        assert business_counter_resp.status_code == 409
        detail = business_counter_resp.json()["detail"]
        assert detail["current_status"] == "pending"

    def test_accept_counter_not_found_returns_404(
        self, integration_client, business_headers
    ):
        """Test accepting counter on non-existent deal returns 404."""
        client, _ = integration_client

        accept_resp = client.put(
            "/api/deals/nonexistent_id/accept-counter",
            headers=business_headers,
        )
        assert accept_resp.status_code == 404

    def test_reject_counter_not_found_returns_404(
        self, integration_client, business_headers
    ):
        """Test rejecting counter on non-existent deal returns 404."""
        client, _ = integration_client

        reject_resp = client.put(
            "/api/deals/nonexistent_id/reject-counter",
            headers=business_headers,
        )
        assert reject_resp.status_code == 404

    def test_business_counter_not_found_returns_404(
        self, integration_client, business_headers
    ):
        """Test business counter on non-existent deal returns 404."""
        client, _ = integration_client

        business_counter_resp = client.put(
            "/api/deals/nonexistent_id/business-counter",
            json={"message": "Counter offer"},
            headers=business_headers,
        )
        assert business_counter_resp.status_code == 404
