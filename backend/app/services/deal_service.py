"""
DealService — full deal lifecycle management with state machine validation.

Valid transitions (Req 5.7):
  pending            → accepted          (ACCEPT)
  pending            → rejected          (REJECT)
  pending            → countered         (COUNTER)
  countered          → accepted          (ACCEPT_COUNTER)
  countered          → rejected          (REJECT_COUNTER)
  countered          → countered         (BUSINESS_COUNTER)
  countered          → countered         (COUNTER)
  accepted           → content_submitted (SUBMIT_CONTENT)
  content_submitted  → verified          (VERIFY_PASS)
  content_submitted  → revision_requested(VERIFY_FAIL)
  revision_requested → content_submitted (RESUBMIT)
  verified           → completed         (COMPLETE)
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from app.models.deal import CounterOffer, Deal, DealCreate, DealStatus


VALID_TRANSITIONS: dict[tuple[str, str], str] = {
    (DealStatus.pending,            "ACCEPT"):         DealStatus.accepted,
    (DealStatus.pending,            "REJECT"):         DealStatus.rejected,
    (DealStatus.pending,            "COUNTER"):        DealStatus.countered,
    (DealStatus.countered,          "ACCEPT_COUNTER"): DealStatus.accepted,
    (DealStatus.countered,          "REJECT_COUNTER"): DealStatus.rejected,
    (DealStatus.countered,          "BUSINESS_COUNTER"): DealStatus.countered,
    (DealStatus.countered,          "COUNTER"):        DealStatus.countered,
    (DealStatus.accepted,           "SUBMIT_CONTENT"): DealStatus.content_submitted,
    (DealStatus.content_submitted,  "VERIFY_PASS"):    DealStatus.verified,
    (DealStatus.content_submitted,  "VERIFY_FAIL"):    DealStatus.revision_requested,
    (DealStatus.revision_requested, "RESUBMIT"):       DealStatus.content_submitted,
    (DealStatus.verified,           "COMPLETE"):       DealStatus.completed,
}


class InvalidTransitionError(Exception):
    def __init__(self, current_status: str, attempted_action: str):
        self.current_status = current_status
        self.attempted_action = attempted_action
        super().__init__(
            f"Cannot apply action '{attempted_action}' to deal in status '{current_status}'"
        )


class DealNotFoundError(Exception):
    pass


class DealService:
    def __init__(self, db):
        self._db = db
        self._col = db["deals"]

    def transition_deal_status(self, deal: Deal, action: str) -> Deal:
        key = (deal.status, action)
        new_status = VALID_TRANSITIONS.get(key)
        if new_status is None:
            raise InvalidTransitionError(deal.status, action)
        deal.status = new_status
        deal.updated_at = datetime.now(timezone.utc)
        return deal

    async def create_deal(self, payload: DealCreate, ad_idea: str) -> Deal:
        """Create a new deal with pre-generated ad idea.
        
        Requirements: 2.1, 2.2, 2.3, 2.4, 2.6
        """
        now = datetime.now(timezone.utc)
        deal_id = uuid.uuid4().hex
        deal = Deal(
            _id=deal_id,
            business_id=payload.business_id,
            creator_id=payload.creator_id,
            offer_amount=payload.offer_amount,
            deliverables=payload.deliverables,
            deadline=payload.deadline,
            status=DealStatus.pending,
            ad_idea=ad_idea,
            created_at=now,
            updated_at=now,
        )
        doc = deal.model_dump(by_alias=True)
        await self._col.insert_one(doc)
        return deal

    async def get_deal(self, deal_id: str) -> Deal:
        doc = await self._col.find_one({"_id": deal_id})
        if doc is None:
            raise DealNotFoundError(deal_id)
        return Deal(**doc)

    async def _save_deal(self, deal: Deal) -> Deal:
        update_doc: dict = {
            "status": deal.status,
            "updated_at": deal.updated_at,
            "offer_amount": deal.offer_amount,
            "deliverables": deal.deliverables,
        }
        if deal.ad_idea is not None:
            update_doc["ad_idea"] = deal.ad_idea
        if deal.content_url is not None:
            update_doc["content_url"] = deal.content_url
        if deal.verification_score is not None:
            update_doc["verification_score"] = deal.verification_score
        if deal.payment_status is not None:
            update_doc["payment_status"] = deal.payment_status
        
        # Save counter fields
        if deal.counter_message is not None:
            update_doc["counter_message"] = deal.counter_message
        if deal.counter_amount is not None:
            update_doc["counter_amount"] = deal.counter_amount
        if deal.counter_deliverables is not None:
            update_doc["counter_deliverables"] = deal.counter_deliverables
        if deal.counter_history:
            update_doc["counter_history"] = [
                counter.model_dump() for counter in deal.counter_history
            ]

        await self._col.update_one({"_id": deal.id}, {"$set": update_doc})
        return deal

    async def accept_deal(self, deal_id: str, ad_idea: Optional[str] = None) -> Deal:
        deal = await self.get_deal(deal_id)
        deal = self.transition_deal_status(deal, "ACCEPT")
        if ad_idea:
            deal.ad_idea = ad_idea
        return await self._save_deal(deal)

    async def reject_deal(self, deal_id: str) -> Deal:
        deal = await self.get_deal(deal_id)
        deal = self.transition_deal_status(deal, "REJECT")
        return await self._save_deal(deal)

    async def counter_deal(
        self,
        deal_id: str,
        message: Optional[str] = None,
        counter_amount: Optional[float] = None,
        counter_deliverables: Optional[str] = None
    ) -> Deal:
        """Counter a pending deal with optional message and terms.
        
        Validates deal exists and status is pending, stores counter data,
        creates CounterOffer entry with author="creator", transitions to countered,
        and updates timestamp.
        
        Requirements: 1.1, 1.2, 1.3, 1.4, 1.7, 1.8, 6.4
        """
        deal = await self.get_deal(deal_id)
        deal = self.transition_deal_status(deal, "COUNTER")
        
        # Store counter data in deal fields
        deal.counter_message = message
        deal.counter_amount = counter_amount
        deal.counter_deliverables = counter_deliverables
        
        # Create CounterOffer entry and add to counter_history
        counter_offer = CounterOffer(
            author="creator",
            message=message,
            proposed_amount=counter_amount,
            proposed_deliverables=counter_deliverables,
            timestamp=deal.updated_at
        )
        deal.counter_history.append(counter_offer)
        
        return await self._save_deal(deal)

    async def accept_counter(self, deal_id: str) -> Deal:
        """Accept a countered deal, applying counter terms if present.
        
        Validates deal exists and status is countered, applies counter_amount
        to offer_amount if provided, applies counter_deliverables to deliverables
        if provided, transitions to accepted, preserves counter_history.
        
        Requirements: 5.1, 5.2, 5.3, 4.6
        """
        deal = await self.get_deal(deal_id)
        deal = self.transition_deal_status(deal, "ACCEPT_COUNTER")
        
        # Apply counter terms to the deal if they were provided
        if deal.counter_amount is not None:
            deal.offer_amount = deal.counter_amount
        if deal.counter_deliverables is not None:
            deal.deliverables = deal.counter_deliverables
        
        # counter_history is already part of the deal object and will be preserved
        return await self._save_deal(deal)

    async def reject_counter(self, deal_id: str) -> Deal:
        """Reject a countered deal.
        
        Validates deal exists and status is countered, transitions to rejected,
        returns updated deal.
        
        Requirements: 5.4
        """
        deal = await self.get_deal(deal_id)
        deal = self.transition_deal_status(deal, "REJECT_COUNTER")
        return await self._save_deal(deal)

    async def business_counter(
        self,
        deal_id: str,
        message: Optional[str] = None,
        counter_amount: Optional[float] = None,
        counter_deliverables: Optional[str] = None
    ) -> Deal:
        """Business counters a countered deal with optional message and terms.
        
        Validates deal exists and status is countered, stores business counter data,
        creates CounterOffer entry with author="business", adds to counter_history,
        keeps status as countered, and updates timestamp.
        
        Requirements: 6.1, 6.2, 6.3, 6.4
        """
        deal = await self.get_deal(deal_id)
        deal = self.transition_deal_status(deal, "BUSINESS_COUNTER")
        
        # Store business counter data in deal fields
        deal.counter_message = message
        deal.counter_amount = counter_amount
        deal.counter_deliverables = counter_deliverables
        
        # Create CounterOffer entry with author="business" and add to counter_history
        counter_offer = CounterOffer(
            author="business",
            message=message,
            proposed_amount=counter_amount,
            proposed_deliverables=counter_deliverables,
            timestamp=deal.updated_at
        )
        deal.counter_history.append(counter_offer)
        
        return await self._save_deal(deal)

    async def submit_content(self, deal_id: str, content_url: str) -> Deal:
        deal = await self.get_deal(deal_id)
        deal = self.transition_deal_status(deal, "SUBMIT_CONTENT")
        deal.content_url = content_url
        return await self._save_deal(deal)
