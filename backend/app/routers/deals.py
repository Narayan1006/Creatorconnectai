"""
Deals router — deal lifecycle endpoints.

POST   /api/deals                  — create a new deal (business only)
PUT    /api/deals/:id/accept       — accept a pending deal (creator only)
PUT    /api/deals/:id/reject       — reject a pending deal (creator only)
PUT    /api/deals/:id/counter      — counter a pending deal (creator only)
POST   /api/deals/:id/submit       — submit content for an accepted deal (creator only)

HTTP 409 is returned with {current_status, attempted_action} on invalid transitions (Req 5.6).
updated_at is set on every status change (Req 5.8).
Ad idea is generated when a deal is accepted (Req 4.1).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from typing import Optional
from urllib.parse import urlparse

from app.core.auth import require_business, require_creator, get_current_user
from app.core.config import settings
from app.core.database import get_database
from app.models.deal import DealCreate, DealResponse
from app.models.payment import PaymentResponse
from app.services.deal_service import DealService, InvalidTransitionError, DealNotFoundError
from app.services.llm_service import generate_ad_idea
from app.services.payment_service import (
    PaymentService,
    PaymentNotFoundError,
    InvalidPaymentTriggerError,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------

class ContentSubmitRequest(BaseModel):
    content_url: str


class CounterRequest(BaseModel):
    """Request body for creator counter offer."""
    message: Optional[str] = None
    counter_amount: Optional[float] = None
    counter_deliverables: Optional[str] = None

    @field_validator("counter_amount")
    @classmethod
    def validate_counter_amount(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            if v <= 0:
                raise ValueError("counter_amount must be positive")
            if v > settings.MAX_OFFER_AMOUNT:
                raise ValueError(f"counter_amount exceeds maximum {settings.MAX_OFFER_AMOUNT}")
        return v

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v.strip()) == 0:
            raise ValueError("message cannot be empty or whitespace only")
        return v


class BusinessCounterRequest(BaseModel):
    """Request body for business counter offer."""
    message: Optional[str] = None
    counter_amount: Optional[float] = None
    counter_deliverables: Optional[str] = None

    @field_validator("counter_amount")
    @classmethod
    def validate_counter_amount(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            if v <= 0:
                raise ValueError("counter_amount must be positive")
            if v > settings.MAX_OFFER_AMOUNT:
                raise ValueError(f"counter_amount exceeds maximum {settings.MAX_OFFER_AMOUNT}")
        return v

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v.strip()) == 0:
            raise ValueError("message cannot be empty or whitespace only")
        return v


# ---------------------------------------------------------------------------
# Dependency
# ---------------------------------------------------------------------------

def get_deal_service(db=Depends(get_database)) -> DealService:
    return DealService(db)


def get_payment_service(db=Depends(get_database)) -> PaymentService:
    return PaymentService(db)


# ---------------------------------------------------------------------------
# Helper: validate content URL domain against CDN allowlist (Req 13.3)
# ---------------------------------------------------------------------------

def _get_allowed_domains() -> list[str]:
    """Parse the comma-separated ALLOWED_CDN_DOMAINS setting into a list."""
    raw = settings.ALLOWED_CDN_DOMAINS
    return [d.strip() for d in raw.split(",") if d.strip()]


def _validate_content_url_domain(url: str) -> None:
    """
    Validate that the URL's hostname matches or ends with one of the trusted
    CDN domains. Raises HTTP 422 if the domain is not on the allowlist.
    """
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname or ""
    except Exception:
        hostname = ""

    allowed_domains = _get_allowed_domains()
    for domain in allowed_domains:
        if hostname == domain or hostname.endswith("." + domain):
            return

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=f"Content URL domain '{hostname}' is not in the trusted CDN allowlist",
    )


# ---------------------------------------------------------------------------
# Helper: fetch creator niche for ad idea generation
# ---------------------------------------------------------------------------

async def _get_creator_niche(db, creator_id: str) -> list[str]:
    """Return the creator's niche list, falling back to ['general'] if not found."""
    doc = await db["creators"].find_one({"_id": creator_id})
    if doc and doc.get("niche"):
        return doc["niche"]
    return ["general"]


# ---------------------------------------------------------------------------
# GET /api/deals/all-creator — list ALL deals for any creator (no profile link needed)
# ---------------------------------------------------------------------------

@router.get("/all-creator", response_model=list[DealResponse])
async def list_all_creator_deals(
    _current_user: dict = Depends(get_current_user),
    service: DealService = Depends(get_deal_service),
):
    """Return all deals in the system for any creator to see.
    
    Since creator profiles may not be linked to user accounts yet,
    this returns all deals so creators can see and act on them.
    """
    col = service._col
    docs = await col.find({}).to_list(length=200)
    results = []
    for doc in docs:
        try:
            from app.models.deal import Deal
            deal = Deal(**doc)
            data = deal.model_dump(by_alias=True)
            results.append(DealResponse(**data))
        except Exception:
            continue
    return results


# ---------------------------------------------------------------------------
# GET /api/deals — list deals for current user
# ---------------------------------------------------------------------------

from app.core.auth import get_current_user

@router.get("", response_model=list[DealResponse])
async def list_deals(
    current_user: dict = Depends(get_current_user),
    service: DealService = Depends(get_deal_service),
    db=Depends(get_database),
    creator_profile_id: str = None,
):
    """Return all deals for the current user (business or creator).
    
    For creators, optionally pass creator_profile_id to override the user_id lookup.
    """
    user_id = current_user.get("sub", "")
    role = current_user.get("role", "")
    col = service._col

    if role == "business":
        cursor = col.find({"business_id": user_id})
        docs = await cursor.to_list(length=100)
    else:
        # If creator_profile_id is explicitly provided, use it directly
        if creator_profile_id:
            profile_ids = [creator_profile_id]
        else:
            # Find creator profiles with user_id matching this user
            all_creator_docs = await db["creators"].find({}).to_list(length=500)
            profile_ids = [
                str(doc["_id"]) for doc in all_creator_docs
                if doc.get("user_id") == user_id
            ]
            if not profile_ids:
                # No linked profile — return empty, frontend will show claim UI
                return []

        all_docs = []
        for cid in profile_ids:
            c = col.find({"creator_id": cid})
            docs_for_cid = await c.to_list(length=100)
            all_docs.extend(docs_for_cid)
        docs = all_docs
    results = []
    for doc in docs:
        try:
            from app.models.deal import Deal
            deal = Deal(**doc)
            data = deal.model_dump(by_alias=True)
            results.append(DealResponse(**data))
        except Exception:
            continue
    return results


# ---------------------------------------------------------------------------
# POST /api/deals — create deal (business only)
# Task 8.3 | Req 5.1 — new deal must have status pending
# Task 5.1 | Req 2.1, 2.2, 2.3, 2.4, 2.6 — generate AI ad idea upfront
# ---------------------------------------------------------------------------

@router.post("", response_model=DealResponse, status_code=status.HTTP_201_CREATED)
async def create_deal(
    payload: DealCreate,
    _current_user: dict = Depends(require_business),
    service: DealService = Depends(get_deal_service),
    db=Depends(get_database),
):
    """Create a new deal with status=pending and AI-generated ad idea."""
    # Task 5.1 — generate ad idea before persisting (Req 2.1, 2.2, 2.3, 2.4)
    creator_niche = await _get_creator_niche(db, payload.creator_id)
    ad_idea = await generate_ad_idea(payload.deliverables, creator_niche)
    
    deal = await service.create_deal(payload, ad_idea=ad_idea)
    return _to_response(deal)


# ---------------------------------------------------------------------------
# PUT /api/deals/:id/accept — accept deal (creator only)
# Task 8.3, 8.7 | Req 5.2, 4.1 — trigger ad idea generation on accept
# ---------------------------------------------------------------------------

@router.put("/{deal_id}/accept", response_model=DealResponse)
async def accept_deal(
    deal_id: str,
    _current_user: dict = Depends(require_creator),
    service: DealService = Depends(get_deal_service),
    db=Depends(get_database),
):
    """Accept a pending deal and trigger LLM ad idea generation (Req 4.1)."""
    try:
        # Fetch deal first to get creator_id for ad idea context
        deal = await service.get_deal(deal_id)
    except DealNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")

    # Task 8.7 — generate ad idea before persisting (Req 4.1)
    creator_niche = await _get_creator_niche(db, deal.creator_id)
    ad_idea = await generate_ad_idea(deal.deliverables, creator_niche)

    try:
        updated = await service.accept_deal(deal_id, ad_idea=ad_idea)
    except InvalidTransitionError as exc:
        # Task 8.5 — HTTP 409 with current_status and attempted_action (Req 5.6)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "Invalid transition",
                "current_status": exc.current_status,
                "attempted_action": exc.attempted_action,
            },
        )
    except DealNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")

    return _to_response(updated)


# ---------------------------------------------------------------------------
# PUT /api/deals/:id/reject — reject deal (creator only)
# Task 8.3 | Req 5.3
# ---------------------------------------------------------------------------

@router.put("/{deal_id}/reject", response_model=DealResponse)
async def reject_deal(
    deal_id: str,
    _current_user: dict = Depends(require_creator),
    service: DealService = Depends(get_deal_service),
):
    """Reject a pending deal."""
    try:
        updated = await service.reject_deal(deal_id)
    except InvalidTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "Invalid transition",
                "current_status": exc.current_status,
                "attempted_action": exc.attempted_action,
            },
        )
    except DealNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")

    return _to_response(updated)


# ---------------------------------------------------------------------------
# PUT /api/deals/:id/counter — counter deal (creator only)
# Task 8.3 | Req 5.4
# ---------------------------------------------------------------------------

@router.put("/{deal_id}/counter", response_model=DealResponse)
async def counter_deal(
    deal_id: str,
    body: CounterRequest,
    _current_user: dict = Depends(require_creator),
    service: DealService = Depends(get_deal_service),
):
    """Counter a pending deal with optional message and terms."""
    try:
        updated = await service.counter_deal(
            deal_id,
            message=body.message,
            counter_amount=body.counter_amount,
            counter_deliverables=body.counter_deliverables
        )
    except InvalidTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "Invalid transition",
                "current_status": exc.current_status,
                "attempted_action": exc.attempted_action,
            },
        )
    except DealNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")

    return _to_response(updated)


# ---------------------------------------------------------------------------
# PUT /api/deals/:id/accept-counter — accept counter (business only)
# Task 9 | Req 5.1, 5.2, 5.3
# ---------------------------------------------------------------------------

@router.put("/{deal_id}/accept-counter", response_model=DealResponse)
async def accept_counter(
    deal_id: str,
    _current_user: dict = Depends(require_business),
    service: DealService = Depends(get_deal_service),
):
    """Accept a countered deal, applying counter terms if present."""
    try:
        updated = await service.accept_counter(deal_id)
    except InvalidTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "Invalid transition",
                "current_status": exc.current_status,
                "attempted_action": exc.attempted_action,
            },
        )
    except DealNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")

    return _to_response(updated)


# ---------------------------------------------------------------------------
# PUT /api/deals/:id/reject-counter — reject counter (business only)
# Task 9 | Req 5.4
# ---------------------------------------------------------------------------

@router.put("/{deal_id}/reject-counter", response_model=DealResponse)
async def reject_counter(
    deal_id: str,
    _current_user: dict = Depends(require_business),
    service: DealService = Depends(get_deal_service),
):
    """Reject a countered deal."""
    try:
        updated = await service.reject_counter(deal_id)
    except InvalidTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "Invalid transition",
                "current_status": exc.current_status,
                "attempted_action": exc.attempted_action,
            },
        )
    except DealNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")

    return _to_response(updated)


# ---------------------------------------------------------------------------
# PUT /api/deals/:id/business-counter — business counter (business only)
# Task 9 | Req 6.1, 6.2
# ---------------------------------------------------------------------------

@router.put("/{deal_id}/business-counter", response_model=DealResponse)
async def business_counter(
    deal_id: str,
    body: BusinessCounterRequest,
    _current_user: dict = Depends(require_business),
    service: DealService = Depends(get_deal_service),
):
    """Business counters a countered deal with optional message and revised terms."""
    try:
        updated = await service.business_counter(
            deal_id,
            message=body.message,
            counter_amount=body.counter_amount,
            counter_deliverables=body.counter_deliverables
        )
    except InvalidTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "Invalid transition",
                "current_status": exc.current_status,
                "attempted_action": exc.attempted_action,
            },
        )
    except DealNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")

    return _to_response(updated)


# ---------------------------------------------------------------------------
# POST /api/deals/:id/submit — submit content (creator only)
# Task 8.4 | Req 5.5
# ---------------------------------------------------------------------------

@router.post("/{deal_id}/submit", response_model=DealResponse)
async def submit_content(
    deal_id: str,
    body: ContentSubmitRequest,
    _current_user: dict = Depends(require_creator),
    service: DealService = Depends(get_deal_service),
):
    """Submit content URL for an accepted deal."""
    # Validate content URL domain against CDN allowlist (Req 13.3, 13.5)
    _validate_content_url_domain(body.content_url)

    try:
        updated = await service.submit_content(deal_id, body.content_url)
    except InvalidTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "Invalid transition",
                "current_status": exc.current_status,
                "attempted_action": exc.attempted_action,
            },
        )
    except DealNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")

    return _to_response(updated)


# ---------------------------------------------------------------------------
# Serialization helper
# ---------------------------------------------------------------------------

def _to_response(deal) -> DealResponse:
    data = deal.model_dump(by_alias=True)
    return DealResponse(**data)


# ---------------------------------------------------------------------------
# GET /api/deals/:id/payment — get payment status (business only)
# Task 10.3 | Req 7.4 — returns current PaymentRecord
# Task 10.4 | Req 7.5 — HTTP 409 if payment trigger attempted for non-verified deal
# ---------------------------------------------------------------------------

@router.get("/{deal_id}/payment", response_model=PaymentResponse)
async def get_payment(
    deal_id: str,
    _current_user: dict = Depends(require_business),
    payment_service: PaymentService = Depends(get_payment_service),
):
    """Return the current PaymentRecord for a deal (Req 7.4).

    Returns HTTP 404 if the deal does not exist.
    Returns HTTP 409 if payment has not been triggered (deal not verified).
    """
    try:
        record = await payment_service.get_payment_status(deal_id)
    except PaymentNotFoundError:
        # Check if the deal exists at all
        deal_service = DealService(payment_service._db)
        try:
            deal = await deal_service.get_deal(deal_id)
        except DealNotFoundError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")

        # Deal exists but payment not triggered — means deal is not verified (Req 7.5)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "Payment not triggered",
                "current_status": deal.status,
                "detail": "Payment is only available for verified deals",
            },
        )

    data = record.model_dump(by_alias=True)
    return PaymentResponse(**data)
