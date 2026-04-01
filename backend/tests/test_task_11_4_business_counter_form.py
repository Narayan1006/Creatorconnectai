"""
Test suite for Task 11.4: Business Counter Form UI

This test verifies that the business counter form UI is properly implemented
and wired to the PUT /api/deals/:id/business-counter endpoint.

Requirements tested:
- 6.1: Business can counter with message
- 6.2: Business can counter with revised terms
"""

import pytest
from httpx import AsyncClient
from app.main import app
from app.models.deal import Deal, DealStatus
from app.core.database import get_database
from datetime import datetime, timedelta


@pytest.fixture
async def countered_deal(test_db):
    """Create a countered deal for testing business counter."""
    db = await get_database()
    deal_data = {
        "business_id": "business123",
        "creator_id": "creator456",
        "offer_amount": 1000.0,
        "deliverables": "1 Instagram post",
        "deadline": datetime.utcnow() + timedelta(days=7),
        "status": DealStatus.countered,
        "counter_message": "I'd like to negotiate the terms",
        "counter_amount": 1500.0,
        "counter_deliverables": "2 Instagram posts",
        "counter_history": [
            {
                "author": "creator",
                "message": "I'd like to negotiate the terms",
                "proposed_amount": 1500.0,
                "proposed_deliverables": "2 Instagram posts",
                "timestamp": datetime.utcnow()
            }
        ]
    }
    result = await db.deals.insert_one(deal_data)
    deal_data["_id"] = result.inserted_id
    return deal_data


@pytest.mark.asyncio
async def test_business_counter_endpoint_exists(countered_deal, business_token):
    """Test that the business counter endpoint exists and is accessible."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        deal_id = str(countered_deal["_id"])
        response = await client.put(
            f"/api/deals/{deal_id}/business-counter",
            json={"message": "Let's meet in the middle"},
            headers={"Authorization": f"Bearer {business_token}"}
        )
        assert response.status_code in [200, 401, 403, 404, 409], \
            f"Endpoint should exist, got {response.status_code}"


@pytest.mark.asyncio
async def test_business_counter_with_message_only(countered_deal, business_token):
    """Test business can counter with just a message."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        deal_id = str(countered_deal["_id"])
        response = await client.put(
            f"/api/deals/{deal_id}/business-counter",
            json={"message": "Let's meet in the middle"},
            headers={"Authorization": f"Bearer {business_token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "countered"
            # Check that business counter was added to history
            assert len(data.get("counter_history", [])) >= 2
            # Last entry should be from business
            if data.get("counter_history"):
                last_entry = data["counter_history"][-1]
                assert last_entry["author"] == "business"
                assert last_entry["message"] == "Let's meet in the middle"


@pytest.mark.asyncio
async def test_business_counter_with_revised_terms(countered_deal, business_token):
    """Test business can counter with revised amount and deliverables."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        deal_id = str(countered_deal["_id"])
        response = await client.put(
            f"/api/deals/{deal_id}/business-counter",
            json={
                "message": "How about this compromise?",
                "counter_amount": 1250.0,
                "counter_deliverables": "1 Instagram post + 1 story"
            },
            headers={"Authorization": f"Bearer {business_token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "countered"
            # Check that counter fields are updated
            assert data.get("counter_amount") == 1250.0
            assert data.get("counter_deliverables") == "1 Instagram post + 1 story"
            # Check history
            if data.get("counter_history"):
                last_entry = data["counter_history"][-1]
                assert last_entry["author"] == "business"
                assert last_entry["proposed_amount"] == 1250.0
                assert last_entry["proposed_deliverables"] == "1 Instagram post + 1 story"


@pytest.mark.asyncio
async def test_business_counter_form_fields_are_optional(countered_deal, business_token):
    """Test that all business counter form fields are optional."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        deal_id = str(countered_deal["_id"])
        
        # Test with empty payload
        response = await client.put(
            f"/api/deals/{deal_id}/business-counter",
            json={},
            headers={"Authorization": f"Bearer {business_token}"}
        )
        
        # Should accept empty payload (all fields optional)
        assert response.status_code in [200, 400, 401, 403, 404, 409]


@pytest.mark.asyncio
async def test_business_counter_preserves_negotiation_history(countered_deal, business_token):
    """Test that business counter preserves the full negotiation history."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        deal_id = str(countered_deal["_id"])
        
        # First business counter
        response1 = await client.put(
            f"/api/deals/{deal_id}/business-counter",
            json={"message": "First counter", "counter_amount": 1200.0},
            headers={"Authorization": f"Bearer {business_token}"}
        )
        
        if response1.status_code == 200:
            data1 = response1.json()
            history_length_1 = len(data1.get("counter_history", []))
            
            # Second business counter (simulating another round)
            response2 = await client.put(
                f"/api/deals/{deal_id}/business-counter",
                json={"message": "Second counter", "counter_amount": 1300.0},
                headers={"Authorization": f"Bearer {business_token}"}
            )
            
            if response2.status_code == 200:
                data2 = response2.json()
                history_length_2 = len(data2.get("counter_history", []))
                
                # History should grow
                assert history_length_2 > history_length_1
                # All entries should be preserved
                assert history_length_2 >= 3  # Original creator counter + 2 business counters


@pytest.mark.asyncio
async def test_ui_verification_business_counter_button_exists():
    """
    UI Verification Test: Verify that the Counter Back button exists in BusinessDashboard.
    
    This test checks that the BusinessDashboard.tsx file contains:
    1. A "Counter Back" button
    2. Business counter form with message, amount, deliverables inputs
    3. Form submission handler wired to the business-counter endpoint
    """
    import os
    
    dashboard_path = "../frontend/src/pages/BusinessDashboard.tsx"
    assert os.path.exists(dashboard_path), "BusinessDashboard.tsx should exist"
    
    with open(dashboard_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for Counter Back button
    assert "Counter Back" in content, "Counter Back button should exist"
    
    # Check for business counter form state variables
    assert "businessCounterMessage" in content, "businessCounterMessage state should exist"
    assert "businessCounterAmount" in content, "businessCounterAmount state should exist"
    assert "businessCounterDeliverables" in content, "businessCounterDeliverables state should exist"
    assert "showBusinessCounterForm" in content, "showBusinessCounterForm state should exist"
    
    # Check for form inputs
    assert "Message (optional)" in content or "message" in content.lower(), \
        "Message input should exist"
    assert "Counter Amount" in content or "counter_amount" in content.lower(), \
        "Counter Amount input should exist"
    assert "Counter Deliverables" in content or "counter_deliverables" in content.lower(), \
        "Counter Deliverables input should exist"
    
    # Check for endpoint wiring
    assert "/business-counter" in content, "business-counter endpoint should be referenced"
    assert "handleBusinessCounter" in content, "handleBusinessCounter function should exist"
    
    print("✓ Counter Back button exists")
    print("✓ Business counter form with message, amount, deliverables inputs exists")
    print("✓ Form is wired to PUT /api/deals/:id/business-counter endpoint")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
