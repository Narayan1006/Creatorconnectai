"""
End-to-end integration test for CreatorConnectAI.

Full flow:
  POST /api/match          → returns creators from seeded FAISS
  POST /api/deals          → creates deal with status=pending
  PUT  /api/deals/:id/accept → transitions to accepted, generates ad_idea
  POST /api/deals/:id/submit → submits content URL
  GET  /api/deals/:id/payment → returns payment record (or 409 if not yet verified)

Mocks:
  - generate_ad_idea → returns fixed string (avoids LLM call)
  - VerificationService._fetch_content_text → returns fixed text (avoids HTTP call)
"""
import sys
import types
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Stubs are applied in conftest.py before any app import.
# We import conftest fixtures via pytest's fixture mechanism.


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _future_deadline() -> str:
    dt = datetime.now(timezone.utc) + timedelta(days=30)
    return dt.isoformat()


# ---------------------------------------------------------------------------
# Task 18.2 — Full E2E flow
# ---------------------------------------------------------------------------

class TestEndToEndFlow:
    """
    Integration test: match → deal → accept → submit → verify → payment.
    """

    def test_match_returns_creators(self, integration_client, business_headers):
        """POST /api/match returns a list of creators from the seeded FAISS index."""
        client, _ = integration_client
        response = client.post(
            "/api/match",
            json={
                "product_description": "Wireless noise-cancelling headphones for professionals",
                "target_audience": "Tech-savvy remote workers",
                "budget": 5000,
                "top_k": 5,
            },
            headers=business_headers,
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert "results" in data
        assert isinstance(data["results"], list)
        assert len(data["results"]) <= 5
        # Each result has a creator and a match_score
        for item in data["results"]:
            assert "creator" in item
            assert "match_score" in item
            assert 0.0 <= item["match_score"] <= 1.0
            # Embedding must not be exposed
            assert "embedding" not in item["creator"]

    def test_create_deal_status_pending(self, integration_client, business_headers, dummy_creators):
        """POST /api/deals creates a deal with status=pending."""
        client, _ = integration_client
        creator_id = str(dummy_creators[0]["_id"])
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
        assert data["status"] == "pending"
        assert data["offer_amount"] == 2500.0
        assert data["creator_id"] == creator_id

    def test_accept_deal_transitions_to_accepted(
        self, integration_client, business_headers, creator_headers, dummy_creators
    ):
        """PUT /api/deals/:id/accept transitions deal to accepted and sets ad_idea."""
        client, _ = integration_client
        creator_id = str(dummy_creators[1]["_id"])

        # Create deal
        create_resp = client.post(
            "/api/deals",
            json={
                "business_id": "biz_001",
                "creator_id": creator_id,
                "offer_amount": 1000.0,
                "deliverables": "YouTube review video",
                "deadline": _future_deadline(),
            },
            headers=business_headers,
        )
        assert create_resp.status_code == 201, create_resp.text
        deal_id = create_resp.json()["_id"] or create_resp.json().get("id")
        # Handle both _id and id keys
        if not deal_id:
            deal_id = create_resp.json().get("_id")

        # Accept deal — mock LLM to avoid real API call
        with patch(
            "app.routers.deals.generate_ad_idea",
            new=AsyncMock(return_value="Showcase the product authentically to your audience."),
        ):
            accept_resp = client.put(
                f"/api/deals/{deal_id}/accept",
                headers=creator_headers,
            )

        assert accept_resp.status_code == 200, accept_resp.text
        accepted = accept_resp.json()
        assert accepted["status"] == "accepted"
        assert accepted["ad_idea"] == "Showcase the product authentically to your audience."

    def test_submit_content_transitions_to_content_submitted(
        self, integration_client, business_headers, creator_headers, dummy_creators
    ):
        """POST /api/deals/:id/submit transitions deal to content_submitted."""
        client, _ = integration_client
        creator_id = str(dummy_creators[2]["_id"])

        # Create deal
        create_resp = client.post(
            "/api/deals",
            json={
                "business_id": "biz_001",
                "creator_id": creator_id,
                "offer_amount": 750.0,
                "deliverables": "TikTok video",
                "deadline": _future_deadline(),
            },
            headers=business_headers,
        )
        assert create_resp.status_code == 201
        deal_id = create_resp.json()["_id"]

        # Accept
        with patch(
            "app.routers.deals.generate_ad_idea",
            new=AsyncMock(return_value="Creative ad concept for TikTok."),
        ):
            accept_resp = client.put(f"/api/deals/{deal_id}/accept", headers=creator_headers)
        assert accept_resp.status_code == 200

        # Submit content
        submit_resp = client.post(
            f"/api/deals/{deal_id}/submit",
            json={"content_url": "https://cdn.example.com/test-video.mp4"},
            headers=creator_headers,
        )
        assert submit_resp.status_code == 200, submit_resp.text
        submitted = submit_resp.json()
        assert submitted["status"] == "content_submitted"
        assert submitted["content_url"] == "https://cdn.example.com/test-video.mp4"

    def test_payment_returns_409_before_verification(
        self, integration_client, business_headers, creator_headers, dummy_creators
    ):
        """GET /api/deals/:id/payment returns 409 when deal is not yet verified."""
        client, _ = integration_client
        creator_id = str(dummy_creators[3]["_id"])

        # Create deal
        create_resp = client.post(
            "/api/deals",
            json={
                "business_id": "biz_001",
                "creator_id": creator_id,
                "offer_amount": 500.0,
                "deliverables": "Blog post",
                "deadline": _future_deadline(),
            },
            headers=business_headers,
        )
        assert create_resp.status_code == 201
        deal_id = create_resp.json()["_id"]

        # Payment check before verification → 409
        payment_resp = client.get(f"/api/deals/{deal_id}/payment", headers=business_headers)
        assert payment_resp.status_code == 409, payment_resp.text

    def test_full_flow_match_deal_accept_submit_verify_payment(
        self, integration_client, business_headers, creator_headers, dummy_creators
    ):
        """
        Full E2E: match → create deal → accept → submit content → verify → check payment.

        Mocks:
          - generate_ad_idea → fixed string
          - VerificationService._fetch_content_text → returns text that will pass verification
        """
        client, stores = integration_client
        creator_id = str(dummy_creators[4]["_id"])

        # Step 1: Match
        match_resp = client.post(
            "/api/match",
            json={
                "product_description": "Premium fitness tracker for athletes",
                "target_audience": "Active sports enthusiasts",
                "budget": 3000,
                "top_k": 3,
            },
            headers=business_headers,
        )
        assert match_resp.status_code == 200
        assert len(match_resp.json()["results"]) <= 3

        # Step 2: Create deal
        create_resp = client.post(
            "/api/deals",
            json={
                "business_id": "biz_e2e",
                "creator_id": creator_id,
                "offer_amount": 1500.0,
                "deliverables": "Instagram Reel showcasing fitness tracker",
                "deadline": _future_deadline(),
            },
            headers=business_headers,
        )
        assert create_resp.status_code == 201
        deal_id = create_resp.json()["_id"]
        assert create_resp.json()["status"] == "pending"

        # Step 3: Accept deal (mock LLM)
        ad_idea_text = "Show the fitness tracker during your morning workout routine."
        with patch(
            "app.routers.deals.generate_ad_idea",
            new=AsyncMock(return_value=ad_idea_text),
        ):
            accept_resp = client.put(f"/api/deals/{deal_id}/accept", headers=creator_headers)
        assert accept_resp.status_code == 200
        assert accept_resp.json()["status"] == "accepted"
        assert accept_resp.json()["ad_idea"] == ad_idea_text

        # Step 4: Submit content
        content_url = "https://cdn.example.com/fitness-reel.mp4"
        submit_resp = client.post(
            f"/api/deals/{deal_id}/submit",
            json={"content_url": content_url},
            headers=creator_headers,
        )
        assert submit_resp.status_code == 200
        assert submit_resp.json()["status"] == "content_submitted"

        # Step 5: Verify content — mock _fetch_content_text to return matching text
        # and mock embedding to produce identical vectors so cosine similarity = 1.0
        from app.services.verification_service import VerificationService

        async def _mock_fetch(self, url):
            return ad_idea_text  # same text → cosine similarity = 1.0

        with patch.object(VerificationService, "_fetch_content_text", _mock_fetch):
            # Trigger verification by calling the verification service directly
            # The submit endpoint only transitions to content_submitted; verification
            # is a separate step. We simulate it by calling the service directly.
            import asyncio
            from app.services.verification_service import VerificationService
            from app.services.deal_service import DealService
            from app.services.payment_service import PaymentService

            db = stores  # we need the actual db mock
            # Rebuild services using the same db mock from the client
            # Access the db mock via the dependency override
            from app.main import app
            from app.core.database import get_database
            db_instance = app.dependency_overrides[get_database]()

            deal_svc = DealService(db_instance)
            payment_svc = PaymentService(db_instance)

            # Use a fixed embedding so cosine similarity = 1.0 (identical vectors)
            from unittest.mock import MagicMock
            emb_svc = MagicMock()
            emb_svc.embed.return_value = [1.0, 0.0, 0.0, 0.0]

            ver_svc = VerificationService(
                embedding_service=emb_svc,
                deal_service=deal_svc,
                payment_service=payment_svc,
            )

            result = asyncio.run(
                ver_svc.verify(deal_id, ad_idea_text, content_url)
            )

        assert result.passed is True
        assert result.match_score >= 0.75
        assert result.feedback  # non-empty

        # Step 6: Check payment status — should now be available
        payment_resp = client.get(f"/api/deals/{deal_id}/payment", headers=business_headers)
        assert payment_resp.status_code == 200, payment_resp.text
        payment_data = payment_resp.json()
        assert payment_data["status"] == "ready_for_payment"
        assert payment_data["deal_id"] == deal_id
        assert payment_data["blockchain_tx_hash"] is not None
        assert payment_data["blockchain_tx_hash"].startswith("0x")


# ---------------------------------------------------------------------------
# Additional targeted integration tests
# ---------------------------------------------------------------------------

class TestDealStateTransitions:
    """Verify HTTP 409 on invalid state transitions."""

    def test_double_accept_returns_409(
        self, integration_client, business_headers, creator_headers, dummy_creators
    ):
        """Accepting an already-accepted deal returns HTTP 409."""
        client, _ = integration_client
        creator_id = str(dummy_creators[5]["_id"])

        create_resp = client.post(
            "/api/deals",
            json={
                "business_id": "biz_001",
                "creator_id": creator_id,
                "offer_amount": 200.0,
                "deliverables": "Story post",
                "deadline": _future_deadline(),
            },
            headers=business_headers,
        )
        deal_id = create_resp.json()["_id"]

        with patch(
            "app.routers.deals.generate_ad_idea",
            new=AsyncMock(return_value="Ad idea."),
        ):
            client.put(f"/api/deals/{deal_id}/accept", headers=creator_headers)
            # Second accept → 409
            resp = client.put(f"/api/deals/{deal_id}/accept", headers=creator_headers)

        assert resp.status_code == 409
        detail = resp.json()["detail"]
        assert detail["current_status"] == "accepted"

    def test_invalid_content_url_domain_returns_422(
        self, integration_client, creator_headers, business_headers, dummy_creators
    ):
        """Submitting content from an untrusted domain returns HTTP 422."""
        client, _ = integration_client
        creator_id = str(dummy_creators[6]["_id"])

        create_resp = client.post(
            "/api/deals",
            json={
                "business_id": "biz_001",
                "creator_id": creator_id,
                "offer_amount": 300.0,
                "deliverables": "Post",
                "deadline": _future_deadline(),
            },
            headers=business_headers,
        )
        deal_id = create_resp.json()["_id"]

        with patch(
            "app.routers.deals.generate_ad_idea",
            new=AsyncMock(return_value="Ad idea."),
        ):
            client.put(f"/api/deals/{deal_id}/accept", headers=creator_headers)

        # Untrusted domain
        submit_resp = client.post(
            f"/api/deals/{deal_id}/submit",
            json={"content_url": "https://evil.com/malware.mp4"},
            headers=creator_headers,
        )
        assert submit_resp.status_code == 422
