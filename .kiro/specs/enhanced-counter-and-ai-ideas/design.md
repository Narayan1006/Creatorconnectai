# Design Document: Enhanced Counter and AI Ideas

## Overview

This feature enhances the deal negotiation workflow by enabling rich counter-offer communication and upfront AI ad idea generation. Currently, the counter mechanism only changes deal status without capturing negotiation context, countered deals disappear from dashboards, and AI ad ideas are generated after acceptance rather than with the initial offer.

The enhancement addresses three key areas:

1. **Counter with Message and Terms**: Creators can counter offers with explanatory messages and optionally propose new amounts or deliverables, enabling meaningful negotiation dialogue.

2. **AI Ad Ideas with Initial Offer**: AI-generated ad concepts are created when businesses submit offers, allowing creators to evaluate creative direction before accepting or countering.

3. **Countered Deal Visibility**: Both creator and business dashboards display countered deals with full negotiation context, preventing deals from disappearing during negotiation.

The design maintains backward compatibility with existing deal flows while extending the data model and API to support richer negotiation workflows.

## Architecture

### System Components

The feature integrates with existing system components:

- **Deal Model** (`backend/app/models/deal.py`): Extended with counter negotiation fields
- **Deal Service** (`backend/app/services/deal_service.py`): Enhanced with counter term handling and business response logic
- **Deal Router** (`backend/app/routers/deals.py`): New endpoints for business counter responses and modified counter endpoint
- **LLM Service** (`backend/app/services/llm_service.py`): Reused for upfront ad idea generation
- **Creator Dashboard** (`frontend/src/pages/CreatorDashboard.tsx`): Enhanced to display countered deals and counter UI
- **Business Dashboard** (`frontend/src/pages/BusinessDashboard.tsx`): Enhanced to display countered deals and response UI

### Data Flow

#### Counter Offer Flow
```
Creator → PUT /api/deals/:id/counter (with message, amount, deliverables)
       → DealService.counter_deal() validates and stores counter data
       → Deal status transitions to "countered"
       → Creator Dashboard displays countered deal
       → Business Dashboard displays countered deal with counter details
```

#### AI Ad Idea Generation Flow
```
Business → POST /api/deals (create offer)
        → LLM Service generates ad idea (with retries/fallback)
        → Deal persisted with ad_idea field populated
        → Creator receives pending deal with ad idea visible
```

#### Business Response to Counter Flow
```
Business → PUT /api/deals/:id/accept-counter OR PUT /api/deals/:id/reject-counter
        → DealService validates current status is "countered"
        → If accepting: apply counter terms to deal, transition to "accepted"
        → If rejecting: transition to "rejected"
        → Updated deal returned to client
```

#### Round-Trip Counter Flow
```
Business → PUT /api/deals/:id/business-counter (with message, revised terms)
        → DealService stores business counter in history
        → Deal remains in "countered" status
        → Creator Dashboard displays business counter message
        → Creator can accept, reject, or counter again
```

### State Machine Extensions

The existing deal state machine is extended with new transitions:

```
Existing:
  pending → accepted (ACCEPT)
  pending → rejected (REJECT)
  pending → countered (COUNTER)

New:
  countered → accepted (ACCEPT_COUNTER)
  countered → rejected (REJECT_COUNTER)
  countered → countered (BUSINESS_COUNTER)
```

## Components and Interfaces

### Backend Components

#### Deal Model Extensions

```python
class CounterOffer(BaseModel):
    """Represents a single counter offer in negotiation history."""
    author: str  # "creator" or "business"
    message: Optional[str] = None
    proposed_amount: Optional[float] = None
    proposed_deliverables: Optional[str] = None
    timestamp: datetime

class Deal(BaseDocument):
    # ... existing fields ...
    ad_idea: Optional[str] = None  # Now populated at creation
    counter_message: Optional[str] = None  # Latest creator counter message
    counter_amount: Optional[float] = None  # Latest creator counter amount
    counter_deliverables: Optional[str] = None  # Latest creator counter deliverables
    counter_history: list[CounterOffer] = []  # Full negotiation history
```

#### Deal Service Methods

```python
class DealService:
    async def create_deal(self, payload: DealCreate, ad_idea: str) -> Deal:
        """Create deal with pre-generated ad idea."""
        
    async def counter_deal(
        self,
        deal_id: str,
        message: Optional[str] = None,
        amount: Optional[float] = None,
        deliverables: Optional[str] = None
    ) -> Deal:
        """Counter a pending deal with optional message and terms."""
        
    async def accept_counter(self, deal_id: str) -> Deal:
        """Accept a countered deal, applying counter terms if present."""
        
    async def reject_counter(self, deal_id: str) -> Deal:
        """Reject a countered deal."""
        
    async def business_counter(
        self,
        deal_id: str,
        message: Optional[str] = None,
        amount: Optional[float] = None,
        deliverables: Optional[str] = None
    ) -> Deal:
        """Business counters a countered deal."""
```

#### API Endpoints

```
POST   /api/deals
  Body: DealCreate
  Response: DealResponse (with ad_idea populated)
  
PUT    /api/deals/:id/counter
  Body: { message?: string, counter_amount?: number, counter_deliverables?: string }
  Response: DealResponse
  
PUT    /api/deals/:id/accept-counter
  Response: DealResponse (with counter terms applied)
  
PUT    /api/deals/:id/reject-counter
  Response: DealResponse
  
PUT    /api/deals/:id/business-counter
  Body: { message?: string, counter_amount?: number, counter_deliverables?: string }
  Response: DealResponse
```

### Frontend Components

#### Creator Dashboard Enhancements

```typescript
interface Deal {
  // ... existing fields ...
  ad_idea?: string
  counter_message?: string
  counter_amount?: number
  counter_deliverables?: string
  counter_history?: CounterOffer[]
}

// New UI sections:
// - Display ad_idea in pending deal cards
// - Counter form with message, amount, deliverables inputs
// - Countered deals section showing counter details
// - Counter history timeline for multi-round negotiations
```

#### Business Dashboard Enhancements

```typescript
// New UI sections:
// - Countered deals section
// - Display counter message and terms
// - Accept/Reject counter buttons
// - Business counter form for round-trip negotiation
// - Counter history timeline
```

## Data Models

### Counter Offer Model

```python
class CounterOffer(BaseModel):
    """Single counter offer in negotiation history."""
    author: str  # "creator" or "business"
    message: Optional[str] = None
    proposed_amount: Optional[float] = None
    proposed_deliverables: Optional[str] = None
    timestamp: datetime
    
    @field_validator("author")
    @classmethod
    def validate_author(cls, v: str) -> str:
        if v not in ("creator", "business"):
            raise ValueError("author must be 'creator' or 'business'")
        return v
    
    @field_validator("proposed_amount")
    @classmethod
    def validate_proposed_amount(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v <= 0:
            raise ValueError("proposed_amount must be positive")
        return v
```

### Deal Model Extensions

```python
class Deal(BaseDocument):
    business_id: str
    creator_id: str
    offer_amount: float
    deliverables: str
    deadline: datetime
    status: DealStatus = DealStatus.pending
    
    # AI ad idea (now populated at creation)
    ad_idea: Optional[str] = None
    
    # Latest counter offer fields (for quick access)
    counter_message: Optional[str] = None
    counter_amount: Optional[float] = None
    counter_deliverables: Optional[str] = None
    
    # Full negotiation history
    counter_history: list[CounterOffer] = []
    
    # ... existing fields ...
    content_url: Optional[str] = None
    verification_score: Optional[float] = None
    payment_status: PaymentStatus = PaymentStatus.not_triggered
```

### Request Models

```python
class CounterRequest(BaseModel):
    """Request body for counter offer."""
    message: Optional[str] = None
    counter_amount: Optional[float] = None
    counter_deliverables: Optional[str] = None
    
    @field_validator("counter_amount")
    @classmethod
    def validate_counter_amount(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            if v <= 0:
                raise ValueError("counter_amount must be positive")
            from app.core.config import settings
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
    
    # Same validators as CounterRequest
```

### Response Model Extensions

```python
class DealResponse(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    business_id: str
    creator_id: str
    offer_amount: float
    deliverables: str
    deadline: datetime
    status: DealStatus
    
    # AI ad idea
    ad_idea: Optional[str] = None
    
    # Counter fields
    counter_message: Optional[str] = None
    counter_amount: Optional[float] = None
    counter_deliverables: Optional[str] = None
    counter_history: list[CounterOffer] = []
    
    # ... existing fields ...
    content_url: Optional[str] = None
    verification_score: Optional[float] = None
    payment_status: PaymentStatus
    created_at: datetime
    updated_at: datetime
```


## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### Property 1: Counter fields are accepted

For any pending deal and any counter request (with or without message, counter_amount, or counter_deliverables), the Counter_Service should successfully accept and process the counter operation.

**Validates: Requirements 1.1, 1.2, 1.3**

### Property 2: Counter data round-trip

For any deal with counter data (message, amount, deliverables), storing the counter and then retrieving the deal should return the same counter values.

**Validates: Requirements 1.4, 4.5**

### Property 3: Counter amount validation rejects non-positive values

For any counter request with a non-positive counter_amount (≤ 0), the Counter_Service should reject the request with a validation error.

**Validates: Requirements 1.5**

### Property 4: Original offer terms are preserved

For any pending deal, after countering with any counter terms, the original offer_amount and deliverables fields should remain unchanged.

**Validates: Requirements 1.7**

### Property 5: Counter transitions status and updates timestamp

For any pending deal, countering should transition the status to "countered" and set updated_at to a timestamp after the original created_at.

**Validates: Requirements 1.8**

### Property 6: New deals always have ad_idea populated

For any newly created deal (regardless of whether AI generation succeeds or fails), the ad_idea field should be non-null and non-empty.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4**

### Property 7: Creator dashboard displays ad idea

For any pending deal with an ad_idea, rendering the deal in the Creator_Dashboard should produce output containing the ad_idea text.

**Validates: Requirements 2.5**

### Property 8: Countered deals appear in creator dashboard

For any set of deals that includes deals with status "countered", the Creator_Dashboard should display those countered deals.

**Validates: Requirements 3.1**

### Property 9: Countered deals appear in business dashboard

For any set of deals that includes deals with status "countered", the Business_Dashboard should display those countered deals.

**Validates: Requirements 3.2**

### Property 10: Creator dashboard displays counter data

For any countered deal with counter_message, counter_amount, or counter_deliverables, rendering the deal in Creator_Dashboard should include all present counter fields in the output.

**Validates: Requirements 3.3, 3.4**

### Property 11: Business dashboard displays counter data

For any countered deal with counter_message, counter_amount, or counter_deliverables, rendering the deal in Business_Dashboard should include all present counter fields in the output.

**Validates: Requirements 3.5, 3.6**

### Property 12: Counter fields default to None

For any newly created deal without counter data, the counter_message, counter_amount, and counter_deliverables fields should all be None.

**Validates: Requirements 4.4**

### Property 13: Counter history is preserved across state transitions

For any countered deal with counter_history, transitioning to accepted status should preserve all entries in counter_history.

**Validates: Requirements 4.6**

### Property 14: Accepting counter transitions to accepted

For any deal with status "countered", accepting the counter should transition the status to "accepted".

**Validates: Requirements 5.1**

### Property 15: Accepting counter applies counter terms

For any countered deal with counter_amount and/or counter_deliverables, accepting the counter should update offer_amount to counter_amount (if provided) and deliverables to counter_deliverables (if provided).

**Validates: Requirements 5.2, 5.3**

### Property 16: Rejecting counter transitions to rejected

For any deal with status "countered", rejecting the counter should transition the status to "rejected".

**Validates: Requirements 5.4**

### Property 17: Invalid state transitions return 409

For any deal not in "countered" status, attempting to accept-counter or reject-counter should return HTTP 409 with the current status.

**Validates: Requirements 5.5, 5.6**

### Property 18: Business counter is accepted for countered deals

For any deal with status "countered", the Counter_Service should accept a business counter with message and/or revised terms.

**Validates: Requirements 6.1, 6.2**

### Property 19: Counter history maintains author attribution

For any deal with counter_history containing both creator and business counters, each entry should have the correct author field ("creator" or "business").

**Validates: Requirements 6.3**

### Property 20: Multiple counter rounds are preserved

For any deal with multiple counter operations (creator counter, business counter, creator counter again), the counter_history should contain all counter entries.

**Validates: Requirements 6.4**

### Property 21: Counter history is displayed chronologically

For any deal with counter_history, rendering the history in either dashboard should display entries in chronological order (sorted by timestamp).

**Validates: Requirements 6.5, 6.6**

## Error Handling

### Validation Errors

The system handles validation errors at multiple layers:

1. **Pydantic Model Validation**: Field validators on `CounterRequest` and `BusinessCounterRequest` catch:
   - Non-positive counter amounts
   - Counter amounts exceeding MAX_OFFER_AMOUNT
   - Empty or whitespace-only messages
   - Returns HTTP 422 with validation error details

2. **State Transition Validation**: `DealService.transition_deal_status()` validates:
   - Current deal status matches expected state for action
   - Raises `InvalidTransitionError` with current_status and attempted_action
   - Router catches and returns HTTP 409 with error details

3. **Deal Not Found**: All service methods check deal existence:
   - Raises `DealNotFoundError` if deal_id doesn't exist
   - Router catches and returns HTTP 404

### AI Generation Failures

The LLM service handles AI generation failures gracefully:

1. **Retry Logic**: Up to 3 attempts with exponential backoff (1s, 2s, 4s)
2. **Timeout**: Each attempt has 30-second timeout
3. **Fallback**: After all retries exhausted, returns template-based fallback ad idea
4. **Guarantee**: `generate_ad_idea()` always returns a non-empty string

This ensures deal creation never fails due to AI service issues.

### Database Errors

MongoDB operations may fail due to:
- Connection issues
- Write conflicts
- Timeout

These are not caught explicitly and will propagate as 500 errors, which is appropriate for infrastructure failures.

## Testing Strategy

### Dual Testing Approach

This feature requires both unit tests and property-based tests for comprehensive coverage:

- **Unit tests**: Verify specific examples, edge cases, and error conditions
- **Property tests**: Verify universal properties across all inputs

Both are complementary and necessary. Unit tests catch concrete bugs in specific scenarios, while property tests verify general correctness across a wide input space.

### Property-Based Testing

We will use **Hypothesis** (Python) for backend property tests and **fast-check** (TypeScript) for frontend property tests.

Each property test must:
- Run minimum 100 iterations (due to randomization)
- Reference its design document property in a comment tag
- Tag format: `# Feature: enhanced-counter-and-ai-ideas, Property {number}: {property_text}`

Example property test structure:

```python
from hypothesis import given, strategies as st
import pytest

# Feature: enhanced-counter-and-ai-ideas, Property 1: Counter fields are accepted
@given(
    deal=st.builds(Deal, status=st.just(DealStatus.pending)),
    message=st.one_of(st.none(), st.text(min_size=1)),
    amount=st.one_of(st.none(), st.floats(min_value=0.01, max_value=100000)),
    deliverables=st.one_of(st.none(), st.text(min_size=1))
)
@pytest.mark.asyncio
async def test_counter_fields_accepted(deal, message, amount, deliverables):
    # Test that counter_deal accepts all combinations of optional fields
    result = await service.counter_deal(deal.id, message, amount, deliverables)
    assert result.status == DealStatus.countered
```

### Unit Testing Focus

Unit tests should focus on:

1. **Specific Examples**:
   - Counter with only message
   - Counter with only amount
   - Counter with all fields
   - Business accepts counter with terms
   - Multi-round negotiation example

2. **Edge Cases**:
   - Counter amount exactly at MAX_OFFER_AMOUNT
   - Empty counter_history
   - Very long counter messages
   - Rapid successive counters

3. **Error Conditions**:
   - Counter amount = 0
   - Counter amount = -100
   - Counter amount > MAX_OFFER_AMOUNT
   - Accept counter on pending deal (wrong status)
   - Business counter on pending deal (wrong status)

4. **Integration Points**:
   - Deal creation with AI generation
   - AI generation fallback when LLM fails
   - Dashboard filtering for countered deals
   - Counter history serialization

### Test Coverage Goals

- Backend service methods: 100% line coverage
- API endpoints: All success and error paths tested
- Frontend components: Key user interactions tested
- Property tests: All 21 properties implemented

### Testing Anti-Patterns to Avoid

- Don't write too many unit tests for input variations—property tests handle that
- Don't duplicate property test logic in unit tests
- Don't test implementation details (e.g., internal method calls)
- Don't test visual styling (e.g., "visually distinguish")

