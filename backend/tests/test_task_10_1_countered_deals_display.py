"""
Test for Task 10.1: Modify deal filtering to include countered status

This test verifies that:
- Dashboard query/filter fetches deals with status=countered
- Countered deals are included in the API response
- Requirements: 3.1, 3.7
"""
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch

import pytest


def _future_deadline() -> str:
    dt = datetime.now(timezone.utc) + timedelta(days=30)
    return dt.isoformat()


class TestCounteredDealsDisplay:
    """Test that countered deals are included in dashboard queries."""

    def test_countered_deal_is_returned_by_api(
        self, integration_client, business_headers, creator_headers, dummy_creators
    ):
        """Test that a countered deal can be retrieved and has correct status.
        
        Validates Requirements 3.1, 3.7
        """
        client, _ = integration_client
        creator_id = str(dummy_creators[0]["_id"])

        # Create a deal
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
            },
            headers=creator_headers,
        )
        assert counter_resp.status_code == 200
        countered_deal = counter_resp.json()
        
        # Verify the deal has countered status
        assert countered_deal["status"] == "countered", "Deal should have countered status"
        assert countered_deal["counter_message"] == "I can do this for $1500"
        assert countered_deal["counter_amount"] == 1500.0
        
        # Verify the deal can be retrieved with countered status
        # (This simulates what the dashboard would fetch)
        assert countered_deal["_id"] == deal_id
        assert countered_deal["status"] == "countered"

    def test_business_can_see_countered_deal(
        self, integration_client, business_headers, creator_headers, dummy_creators
    ):
        """Test that business dashboard can see countered deals.
        
        Validates Requirements 3.2
        """
        client, _ = integration_client
        creator_id = str(dummy_creators[2]["_id"])

        # Create and counter a deal
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
                    "deliverables": "1 post",
                    "deadline": _future_deadline(),
                },
                headers=business_headers,
            )
        deal_id = create_resp.json()["_id"]

        counter_resp = client.put(
            f"/api/deals/{deal_id}/counter",
            json={"message": "Counter from creator"},
            headers=creator_headers,
        )
        assert counter_resp.status_code == 200

        # Business fetches their deals
        get_deals_resp = client.get(
            "/api/deals",
            headers=business_headers,
        )
        assert get_deals_resp.status_code == 200
        deals = get_deals_resp.json()

        # Verify countered deal is visible to business
        countered_deals = [d for d in deals if d["status"] == "countered"]
        assert len(countered_deals) > 0, "Business should see countered deals"
        
        countered_deal = next((d for d in deals if d["_id"] == deal_id), None)
        assert countered_deal is not None
        assert countered_deal["status"] == "countered"
        assert countered_deal["counter_message"] == "Counter from creator"

    def test_multiple_deal_statuses_coexist(
        self, integration_client, business_headers, creator_headers, dummy_creators
    ):
        """Test that deals with different statuses can coexist.
        
        Validates Requirements 3.1
        """
        client, _ = integration_client
        
        # Create three deals with different creators
        deal_data = []
        for i in range(3):
            creator_id = str(dummy_creators[i]["_id"])
            with patch(
                "app.routers.deals.generate_ad_idea",
                new=AsyncMock(return_value="Test ad idea"),
            ):
                create_resp = client.post(
                    "/api/deals",
                    json={
                        "business_id": "biz_001",
                        "creator_id": creator_id,
                        "offer_amount": 1000.0 + (i * 100),
                        "deliverables": f"Deal {i}",
                        "deadline": _future_deadline(),
                    },
                    headers=business_headers,
                )
            assert create_resp.status_code == 201
            deal_data.append({
                "id": create_resp.json()["_id"],
                "creator_id": creator_id,
                "expected_status": "pending"
            })

        # Leave first deal as pending
        # Counter second deal
        counter_resp = client.put(
            f"/api/deals/{deal_data[1]['id']}/counter",
            json={"message": "Counter offer"},
            headers=creator_headers,
        )
        assert counter_resp.status_code == 200
        assert counter_resp.json()["status"] == "countered"
        deal_data[1]["expected_status"] = "countered"

        # Accept third deal
        with patch(
            "app.routers.deals.generate_ad_idea",
            new=AsyncMock(return_value="Test ad idea"),
        ):
            accept_resp = client.put(
                f"/api/deals/{deal_data[2]['id']}/accept",
                headers=creator_headers,
            )
        assert accept_resp.status_code == 200
        assert accept_resp.json()["status"] == "accepted"
        deal_data[2]["expected_status"] = "accepted"

        # Verify all deals have correct statuses
        for deal_info in deal_data:
            # Fetch the deal directly to verify its status
            # (In real app, dashboard would fetch all deals and filter)
            get_deals_resp = client.get(
                "/api/deals",
                headers=business_headers,
            )
            assert get_deals_resp.status_code == 200
            deals = get_deals_resp.json()
            
            deal = next((d for d in deals if d["_id"] == deal_info["id"]), None)
            assert deal is not None, f"Deal {deal_info['id']} should exist"
            assert deal["status"] == deal_info["expected_status"], \
                f"Deal {deal_info['id']} should have status {deal_info['expected_status']}"

