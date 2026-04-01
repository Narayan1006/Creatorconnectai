"""
OpenAPI contract validation tests.

Verifies:
- /openapi.json is accessible and valid
- Key endpoints exist in the schema
- Response schemas contain expected fields
"""
import sys
import types
from unittest.mock import MagicMock

import numpy as np
import pytest
from fastapi.testclient import TestClient


# Stubs are applied in conftest.py; they run before this module is imported.


def _build_openapi_client():
    """Build a minimal TestClient for fetching the OpenAPI schema."""
    from app.main import app
    from app.core.database import get_database
    from app.services.embedding_service import get_embedding_service, get_faiss_store

    # Minimal mocks — we only need the app to start, not real services
    db = MagicMock()
    emb_svc = MagicMock()
    emb_svc.dimension = 4

    from app.services.embedding_service import FAISSStore
    faiss = FAISSStore.__new__(FAISSStore)
    faiss.index_path = "test_index"
    faiss.dimension = 4
    faiss._index = sys.modules["faiss"].IndexFlatL2(4)
    faiss._id_map = {}
    faiss._count = 0

    app.dependency_overrides[get_database] = lambda: db
    app.dependency_overrides[get_embedding_service] = lambda: emb_svc
    app.dependency_overrides[get_faiss_store] = lambda: faiss

    client = TestClient(app, raise_server_exceptions=False)
    return client, app


# ---------------------------------------------------------------------------
# Task 18.3 — OpenAPI contract tests
# ---------------------------------------------------------------------------

class TestOpenAPIContract:
    """Validate the OpenAPI schema for all key endpoints."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.client, self.app = _build_openapi_client()
        yield
        self.app.dependency_overrides.clear()

    def _get_schema(self) -> dict:
        resp = self.client.get("/openapi.json")
        assert resp.status_code == 200, f"Failed to fetch /openapi.json: {resp.status_code}"
        return resp.json()

    def test_openapi_json_is_accessible(self):
        """GET /openapi.json returns 200 with a valid OpenAPI object."""
        schema = self._get_schema()
        assert "openapi" in schema
        assert "paths" in schema
        assert "info" in schema

    def test_openapi_version(self):
        """OpenAPI version field is present."""
        schema = self._get_schema()
        assert schema["openapi"].startswith("3.")

    def test_api_info_fields(self):
        """API info contains title and version."""
        schema = self._get_schema()
        info = schema["info"]
        assert "title" in info
        assert "version" in info
        assert info["title"]  # non-empty

    # ------------------------------------------------------------------
    # Endpoint existence checks
    # ------------------------------------------------------------------

    def test_auth_register_endpoint_exists(self):
        """POST /api/auth/register is present in the schema."""
        schema = self._get_schema()
        paths = schema["paths"]
        assert "/api/auth/register" in paths, (
            f"/api/auth/register not found. Available paths: {list(paths.keys())}"
        )
        assert "post" in paths["/api/auth/register"]

    def test_auth_login_endpoint_exists(self):
        """POST /api/auth/login is present in the schema."""
        schema = self._get_schema()
        paths = schema["paths"]
        assert "/api/auth/login" in paths, (
            f"/api/auth/login not found. Available paths: {list(paths.keys())}"
        )
        assert "post" in paths["/api/auth/login"]

    def test_match_endpoint_exists(self):
        """POST /api/match is present in the schema."""
        schema = self._get_schema()
        paths = schema["paths"]
        assert "/api/match" in paths, (
            f"/api/match not found. Available paths: {list(paths.keys())}"
        )
        assert "post" in paths["/api/match"]

    def test_deals_endpoint_exists(self):
        """POST /api/deals is present in the schema."""
        schema = self._get_schema()
        paths = schema["paths"]
        assert "/api/deals" in paths, (
            f"/api/deals not found. Available paths: {list(paths.keys())}"
        )
        assert "post" in paths["/api/deals"]

    def test_creators_featured_endpoint_exists(self):
        """GET /api/creators/featured is present in the schema."""
        schema = self._get_schema()
        paths = schema["paths"]
        assert "/api/creators/featured" in paths, (
            f"/api/creators/featured not found. Available paths: {list(paths.keys())}"
        )
        assert "get" in paths["/api/creators/featured"]

    def test_admin_reindex_endpoint_exists(self):
        """POST /api/admin/reindex is present in the schema."""
        schema = self._get_schema()
        paths = schema["paths"]
        assert "/api/admin/reindex" in paths, (
            f"/api/admin/reindex not found. Available paths: {list(paths.keys())}"
        )
        assert "post" in paths["/api/admin/reindex"]

    def test_deal_accept_endpoint_exists(self):
        """PUT /api/deals/{deal_id}/accept is present in the schema."""
        schema = self._get_schema()
        paths = schema["paths"]
        assert "/api/deals/{deal_id}/accept" in paths
        assert "put" in paths["/api/deals/{deal_id}/accept"]

    def test_deal_submit_endpoint_exists(self):
        """POST /api/deals/{deal_id}/submit is present in the schema."""
        schema = self._get_schema()
        paths = schema["paths"]
        assert "/api/deals/{deal_id}/submit" in paths
        assert "post" in paths["/api/deals/{deal_id}/submit"]

    def test_deal_payment_endpoint_exists(self):
        """GET /api/deals/{deal_id}/payment is present in the schema."""
        schema = self._get_schema()
        paths = schema["paths"]
        assert "/api/deals/{deal_id}/payment" in paths
        assert "get" in paths["/api/deals/{deal_id}/payment"]

    def test_deal_counter_endpoint_exists(self):
        """PUT /api/deals/{deal_id}/counter is present in the schema."""
        schema = self._get_schema()
        paths = schema["paths"]
        assert "/api/deals/{deal_id}/counter" in paths
        assert "put" in paths["/api/deals/{deal_id}/counter"]

    def test_deal_accept_counter_endpoint_exists(self):
        """PUT /api/deals/{deal_id}/accept-counter is present in the schema."""
        schema = self._get_schema()
        paths = schema["paths"]
        assert "/api/deals/{deal_id}/accept-counter" in paths
        assert "put" in paths["/api/deals/{deal_id}/accept-counter"]

    def test_deal_reject_counter_endpoint_exists(self):
        """PUT /api/deals/{deal_id}/reject-counter is present in the schema."""
        schema = self._get_schema()
        paths = schema["paths"]
        assert "/api/deals/{deal_id}/reject-counter" in paths
        assert "put" in paths["/api/deals/{deal_id}/reject-counter"]

    def test_deal_business_counter_endpoint_exists(self):
        """PUT /api/deals/{deal_id}/business-counter is present in the schema."""
        schema = self._get_schema()
        paths = schema["paths"]
        assert "/api/deals/{deal_id}/business-counter" in paths
        assert "put" in paths["/api/deals/{deal_id}/business-counter"]

    # ------------------------------------------------------------------
    # Response schema field checks
    # ------------------------------------------------------------------

    def test_match_response_schema_has_results_field(self):
        """MatchResponse schema contains 'results' and 'total' fields."""
        schema = self._get_schema()
        components = schema.get("components", {}).get("schemas", {})
        assert "MatchResponse" in components, (
            f"MatchResponse schema not found. Available: {list(components.keys())}"
        )
        props = components["MatchResponse"].get("properties", {})
        assert "results" in props
        assert "total" in props

    def test_deal_response_schema_has_status_field(self):
        """DealResponse schema contains 'status' field."""
        schema = self._get_schema()
        components = schema.get("components", {}).get("schemas", {})
        assert "DealResponse" in components
        props = components["DealResponse"].get("properties", {})
        assert "status" in props
        assert "offer_amount" in props
        assert "creator_id" in props
        assert "business_id" in props

    def test_deal_response_schema_has_no_embedding_field(self):
        """DealResponse schema does not expose embedding vectors."""
        schema = self._get_schema()
        components = schema.get("components", {}).get("schemas", {})
        if "DealResponse" in components:
            props = components["DealResponse"].get("properties", {})
            assert "embedding" not in props

    def test_creator_public_schema_excludes_embedding(self):
        """CreatorPublic schema does not contain 'embedding' field."""
        schema = self._get_schema()
        components = schema.get("components", {}).get("schemas", {})
        assert "CreatorPublic" in components, (
            f"CreatorPublic not found. Available: {list(components.keys())}"
        )
        props = components["CreatorPublic"].get("properties", {})
        assert "embedding" not in props, (
            "CreatorPublic schema must not expose 'embedding' field (Req 10.3)"
        )

    def test_payment_response_schema_has_required_fields(self):
        """PaymentResponse schema contains deal_id, status, blockchain_tx_hash."""
        schema = self._get_schema()
        components = schema.get("components", {}).get("schemas", {})
        assert "PaymentResponse" in components
        props = components["PaymentResponse"].get("properties", {})
        assert "deal_id" in props
        assert "status" in props
        assert "blockchain_tx_hash" in props
        assert "amount" in props

    def test_ranked_creator_schema_has_match_score(self):
        """RankedCreator schema contains 'match_score' and 'creator' fields."""
        schema = self._get_schema()
        components = schema.get("components", {}).get("schemas", {})
        assert "RankedCreator" in components
        props = components["RankedCreator"].get("properties", {})
        assert "match_score" in props
        assert "creator" in props

    def test_deal_status_enum_values(self):
        """DealStatus enum contains all expected values."""
        schema = self._get_schema()
        components = schema.get("components", {}).get("schemas", {})
        assert "DealStatus" in components
        enum_values = components["DealStatus"].get("enum", [])
        expected = {
            "pending", "accepted", "rejected", "countered",
            "content_submitted", "verified", "revision_requested", "completed"
        }
        for val in expected:
            assert val in enum_values, f"DealStatus missing value: {val}"

    def test_health_endpoint_exists(self):
        """GET /health endpoint is accessible."""
        resp = self.client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
