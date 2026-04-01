"""
VerificationService — content verification via cosine similarity.

Algorithm (from design.md):
  1. Embed ad_idea and submitted_content
  2. Compute cosine similarity
  3. Guard against zero-magnitude vectors (return 0.0 / "Empty embedding")
  4. Clamp score to [0.0, 1.0]
  5. passed = score >= THRESHOLD (0.75)
  6. Trigger deal state transition: VERIFY_PASS or VERIFY_FAIL

Req 6.1 — cosine similarity between ad_idea and content embeddings
Req 6.2 — match_score in [0.0, 1.0]
Req 6.3 — passed = true iff score >= 0.75
Req 6.4 — passed = false iff score < 0.75
Req 6.5 — inaccessible URL → match_score=0.0, passed=false, feedback="Content could not be processed"
Req 6.6 — zero-magnitude embedding → match_score=0.0, feedback="Empty embedding"
Req 6.7 — feedback is always non-empty
"""

import math
from typing import Optional

from app.models.verification import VerificationResult
from app.services.deal_service import DealService
from app.services.embedding_service import EmbeddingService
from app.services.payment_service import PaymentService

THRESHOLD = 0.75


class VerificationService:
    """Verifies submitted content against an ad idea using cosine similarity."""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        deal_service: DealService,
        payment_service: Optional[PaymentService] = None,
    ) -> None:
        self._embedding = embedding_service
        self._deal_service = deal_service
        self._payment_service = payment_service

    # ------------------------------------------------------------------
    # Task 9.2 — cosine similarity with zero-vector guard
    # ------------------------------------------------------------------

    def compute_cosine_similarity(
        self, vec_a: list[float], vec_b: list[float]
    ) -> tuple[float, Optional[str]]:
        """Compute cosine similarity between two vectors.

        Returns (similarity, error_feedback).
        If either vector has zero magnitude, returns (0.0, "Empty embedding").
        Otherwise returns (clamped_similarity, None).

        Req 6.6 — zero-magnitude guard
        Req 6.2 — result clamped to [0.0, 1.0]
        """
        magnitude_a = math.sqrt(sum(x * x for x in vec_a))
        magnitude_b = math.sqrt(sum(x * x for x in vec_b))

        # Task 9.2 — zero-vector guard
        if magnitude_a == 0.0 or magnitude_b == 0.0:
            return 0.0, "Empty embedding"

        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        raw_score = dot_product / (magnitude_a * magnitude_b)

        # Task 9.4 — clamp to [0.0, 1.0]
        clamped = max(0.0, min(1.0, raw_score))
        return clamped, None

    # ------------------------------------------------------------------
    # Task 9.3 — fetch content text with fallback on failure
    # ------------------------------------------------------------------

    async def _fetch_content_text(self, content_url: str) -> Optional[str]:
        """Attempt to fetch text from content_url.

        Returns the URL itself as a proxy text for embedding (the URL string
        carries semantic signal for testing purposes). Returns None if the URL
        is inaccessible or an error occurs.

        Req 6.5 — inaccessible URL returns None → fallback result
        """
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(content_url)
                if response.status_code == 200:
                    # Use response text if available, else fall back to URL
                    text = response.text.strip()
                    return text if text else content_url
                return None
        except Exception:
            # Any network error, timeout, or invalid URL → inaccessible
            return None

    # ------------------------------------------------------------------
    # Task 9.1 — main verify method
    # ------------------------------------------------------------------

    async def verify(
        self,
        deal_id: str,
        ad_idea: str,
        content_url: str,
    ) -> VerificationResult:
        """Verify submitted content against the ad idea.

        Steps:
          1. Fetch content text from URL (fallback on failure — Req 6.5)
          2. Embed both texts
          3. Compute cosine similarity with zero-vector guard (Req 6.6)
          4. Clamp score, determine passed (Req 6.2, 6.3, 6.4)
          5. Trigger deal state transition (Task 9.5)
          6. Return VerificationResult with non-empty feedback (Req 6.7)
        """
        # Task 9.3 — fetch content with fallback
        content_text = await self._fetch_content_text(content_url)
        if content_text is None:
            # Req 6.5 — inaccessible URL fallback
            result = VerificationResult(
                deal_id=deal_id,
                match_score=0.0,
                threshold=THRESHOLD,
                passed=False,
                feedback="Content could not be processed",
            )
            await self._apply_deal_transition(deal_id, result)
            return result

        # Task 9.1 — embed both texts
        vec_idea = self._embedding.embed(ad_idea)
        vec_content = self._embedding.embed(content_text)

        # Task 9.2 — cosine similarity with zero-vector guard
        match_score, error_feedback = self.compute_cosine_similarity(vec_idea, vec_content)

        if error_feedback is not None:
            # Req 6.6 — zero-magnitude embedding
            result = VerificationResult(
                deal_id=deal_id,
                match_score=0.0,
                threshold=THRESHOLD,
                passed=False,
                feedback=error_feedback,
            )
            await self._apply_deal_transition(deal_id, result)
            return result

        # Task 9.4 — passed = score >= threshold
        passed = match_score >= THRESHOLD

        if passed:
            feedback = f"Content aligns well. Score: {match_score:.4f}"
        else:
            feedback = (
                f"Content needs revision. Score: {match_score:.4f}. "
                f"Threshold: {THRESHOLD}"
            )

        result = VerificationResult(
            deal_id=deal_id,
            match_score=match_score,
            threshold=THRESHOLD,
            passed=passed,
            feedback=feedback,
        )

        # Task 9.5 — trigger deal state transition
        await self._apply_deal_transition(deal_id, result)
        return result

    # ------------------------------------------------------------------
    # Task 9.5 — deal state transition helper
    # ------------------------------------------------------------------

    async def _apply_deal_transition(
        self, deal_id: str, result: VerificationResult
    ) -> None:
        """Transition deal to verified or revision_requested based on result.

        Uses VERIFY_PASS / VERIFY_FAIL actions defined in DealService state machine.
        When deal transitions to 'verified', triggers payment-ready state (Req 7.1).
        Silently ignores transition errors (e.g., deal already in terminal state).
        """
        action = "VERIFY_PASS" if result.passed else "VERIFY_FAIL"
        try:
            deal = await self._deal_service.get_deal(deal_id)
            deal = self._deal_service.transition_deal_status(deal, action)
            deal.verification_score = result.match_score
            await self._deal_service._save_deal(deal)

            # Task 10.2 — trigger payment when deal transitions to verified (Req 7.1)
            if result.passed and self._payment_service is not None:
                try:
                    await self._payment_service.trigger_payment_ready(
                        deal_id, deal.offer_amount
                    )
                except Exception:
                    # Payment trigger failure must not block verification result
                    pass
        except Exception:
            # Don't let transition errors bubble up — verification result is still valid
            pass
