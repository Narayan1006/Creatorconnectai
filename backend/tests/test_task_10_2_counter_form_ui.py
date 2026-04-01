"""
Integration tests for Task 10.2: Counter form UI to pending deals.

Tests verify that the counter endpoint accepts the payload format sent by the
frontend counter form with optional message, counter_amount, and counter_deliverables.
"""

import pytest
from datetime import datetime, timezone, timedelta


@pytest.mark.asyncio
async def test_counter_endpoint_with_all_fields(integration_client, business_headers, creator_headers, dummy_creators):
    """Test PUT /api/deals/:id/counter with all optional fields (message, counter_amount, counter_deliverables)."""
    client, stores = integration_client
    
    # Create a pending deal
    deal_payload = {
        "business_id": "biz123",
        "creator_id": str(dummy_creators[0]["_id"]),
        "offer_amount": 500.0,
        "deliverables": "1 Instagram post",
        "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    }
    create_resp = client.post("/api/deals", json=deal_payload, headers=business_headers)
    assert create_resp.status_code == 201
    deal_id = create_resp.json()["_id"]
    
    # Counter with all fields (frontend format)
    counter_payload = {
        "message": "I'd like to propose a higher rate",
        "counter_amount": 750.0,
        "counter_deliverables": "1 Instagram post + 3 stories"
    }
    counter_resp = client.put(f"/api/deals/{deal_id}/counter", json=counter_payload, headers=creator_headers)
    assert counter_resp.status_code == 200
    
    data = counter_resp.json()
    assert data["status"] == "countered"
    assert data["counter_message"] == "I'd like to propose a higher rate"
    assert data["counter_amount"] == 750.0
    assert data["counter_deliverables"] == "1 Instagram post + 3 stories"
    assert data["offer_amount"] == 500.0  # Original amount preserved
    assert data["deliverables"] == "1 Instagram post"  # Original deliverables preserved


@pytest.mark.asyncio
async def test_counter_endpoint_with_only_message(integration_client, business_headers, creator_headers, dummy_creators):
    """Test PUT /api/deals/:id/counter with only message field."""
    client, stores = integration_client
    
    # Create a pending deal
    deal_payload = {
        "business_id": "biz123",
        "creator_id": str(dummy_creators[0]["_id"]),
        "offer_amount": 500.0,
        "deliverables": "1 Instagram post",
        "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    }
    create_resp = client.post("/api/deals", json=deal_payload, headers=business_headers)
    assert create_resp.status_code == 201
    deal_id = create_resp.json()["_id"]
    
    # Counter with only message
    counter_payload = {
        "message": "Can we discuss the timeline?"
    }
    counter_resp = client.put(f"/api/deals/{deal_id}/counter", json=counter_payload, headers=creator_headers)
    assert counter_resp.status_code == 200
    
    data = counter_resp.json()
    assert data["status"] == "countered"
    assert data["counter_message"] == "Can we discuss the timeline?"
    assert data["counter_amount"] is None
    assert data["counter_deliverables"] is None


@pytest.mark.asyncio
async def test_counter_endpoint_with_only_amount(integration_client, business_headers, creator_headers, dummy_creators):
    """Test PUT /api/deals/:id/counter with only counter_amount field."""
    client, stores = integration_client
    
    # Create a pending deal
    deal_payload = {
        "business_id": "biz123",
        "creator_id": str(dummy_creators[0]["_id"]),
        "offer_amount": 500.0,
        "deliverables": "1 Instagram post",
        "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    }
    create_resp = client.post("/api/deals", json=deal_payload, headers=business_headers)
    assert create_resp.status_code == 201
    deal_id = create_resp.json()["_id"]
    
    # Counter with only amount
    counter_payload = {
        "counter_amount": 800.0
    }
    counter_resp = client.put(f"/api/deals/{deal_id}/counter", json=counter_payload, headers=creator_headers)
    assert counter_resp.status_code == 200
    
    data = counter_resp.json()
    assert data["status"] == "countered"
    assert data["counter_message"] is None
    assert data["counter_amount"] == 800.0
    assert data["counter_deliverables"] is None


@pytest.mark.asyncio
async def test_counter_endpoint_validation_negative_amount(integration_client, business_headers, creator_headers, dummy_creators):
    """Test PUT /api/deals/:id/counter rejects negative counter_amount."""
    client, stores = integration_client
    
    # Create a pending deal
    deal_payload = {
        "business_id": "biz123",
        "creator_id": str(dummy_creators[0]["_id"]),
        "offer_amount": 500.0,
        "deliverables": "1 Instagram post",
        "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    }
    create_resp = client.post("/api/deals", json=deal_payload, headers=business_headers)
    assert create_resp.status_code == 201
    deal_id = create_resp.json()["_id"]
    
    # Counter with negative amount
    counter_payload = {
        "counter_amount": -100.0
    }
    counter_resp = client.put(f"/api/deals/{deal_id}/counter", json=counter_payload, headers=creator_headers)
    assert counter_resp.status_code == 422
    assert "counter_amount must be positive" in str(counter_resp.json())


@pytest.mark.asyncio
async def test_counter_endpoint_validation_zero_amount(integration_client, business_headers, creator_headers, dummy_creators):
    """Test PUT /api/deals/:id/counter rejects zero counter_amount."""
    client, stores = integration_client
    
    # Create a pending deal
    deal_payload = {
        "business_id": "biz123",
        "creator_id": str(dummy_creators[0]["_id"]),
        "offer_amount": 500.0,
        "deliverables": "1 Instagram post",
        "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    }
    create_resp = client.post("/api/deals", json=deal_payload, headers=business_headers)
    assert create_resp.status_code == 201
    deal_id = create_resp.json()["_id"]
    
    # Counter with zero amount
    counter_payload = {
        "counter_amount": 0.0
    }
    counter_resp = client.put(f"/api/deals/{deal_id}/counter", json=counter_payload, headers=creator_headers)
    assert counter_resp.status_code == 422
    assert "counter_amount must be positive" in str(counter_resp.json())


@pytest.mark.asyncio
async def test_counter_endpoint_empty_payload(integration_client, business_headers, creator_headers, dummy_creators):
    """Test PUT /api/deals/:id/counter accepts empty payload (all fields optional)."""
    client, stores = integration_client
    
    # Create a pending deal
    deal_payload = {
        "business_id": "biz123",
        "creator_id": str(dummy_creators[0]["_id"]),
        "offer_amount": 500.0,
        "deliverables": "1 Instagram post",
        "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    }
    create_resp = client.post("/api/deals", json=deal_payload, headers=business_headers)
    assert create_resp.status_code == 201
    deal_id = create_resp.json()["_id"]
    
    # Counter with empty payload
    counter_payload = {}
    counter_resp = client.put(f"/api/deals/{deal_id}/counter", json=counter_payload, headers=creator_headers)
    assert counter_resp.status_code == 200
    
    data = counter_resp.json()
    assert data["status"] == "countered"
    assert data["counter_message"] is None
    assert data["counter_amount"] is None
    assert data["counter_deliverables"] is None
