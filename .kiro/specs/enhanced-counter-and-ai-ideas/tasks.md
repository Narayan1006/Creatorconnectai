# Implementation Plan: Enhanced Counter and AI Ideas

## Overview

This implementation plan breaks down the enhanced counter and AI ideas feature into discrete coding tasks. The feature adds three key capabilities: counter offers with messages and terms, upfront AI ad idea generation, and countered deal visibility on dashboards. Tasks are organized to build incrementally, with early validation through code and property-based tests.

## Tasks

- [x] 1. Extend Deal model with counter and AI fields
  - Add counter_message, counter_amount, counter_deliverables fields to Deal model
  - Add ad_idea field to Deal model
  - Add counter_history field as list of CounterOffer objects
  - Create CounterOffer embedded model with author, message, proposed_amount, proposed_deliverables, timestamp
  - Add field validators for counter_amount (positive) and author (creator/business only)
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 4.1, 4.2, 4.3, 4.4, 6.3_

- [ ]* 1.1 Write property test for counter fields round-trip
  - **Property 2: Counter data round-trip**
  - **Validates: Requirements 1.4, 4.5**

- [ ]* 1.2 Write property test for counter amount validation
  - **Property 3: Counter amount validation rejects non-positive values**
  - **Validates: Requirements 1.5**

- [ ]* 1.3 Write property test for counter fields default to None
  - **Property 12: Counter fields default to None**
  - **Validates: Requirements 4.4**

- [x] 2. Create request/response models for counter operations
  - Create CounterRequest model with optional message, counter_amount, counter_deliverables
  - Create BusinessCounterRequest model with same fields as CounterRequest
  - Add validators to CounterRequest for positive amounts and non-empty messages
  - Extend DealResponse model to include ad_idea and counter fields
  - _Requirements: 1.5, 1.6, 4.5, 6.1, 6.2_

- [-] 3. Implement DealService.counter_deal method
  - [x] 3.1 Add counter_deal method to DealService
    - Validate deal exists and status is pending
    - Accept optional message, counter_amount, counter_deliverables parameters
    - Store counter data in deal fields
    - Create CounterOffer entry with author="creator" and add to counter_history
    - Transition deal status to countered
    - Update deal timestamp
    - Return updated deal
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.7, 1.8, 6.4_

  - [ ]* 3.2 Write property test for counter fields acceptance
    - **Property 1: Counter fields are accepted**
    - **Validates: Requirements 1.1, 1.2, 1.3**

  - [ ]* 3.3 Write property test for original offer preservation
    - **Property 4: Original offer terms are preserved**
    - **Validates: Requirements 1.7**

  - [ ]* 3.4 Write property test for counter status transition
    - **Property 5: Counter transitions status and updates timestamp**
    - **Validates: Requirements 1.8**

  - [x] 3.5 Write unit tests for counter_deal edge cases
    - Test counter with only message
    - Test counter with only amount
    - Test counter with all fields
    - Test counter amount at MAX_OFFER_AMOUNT boundary
    - Test counter on non-existent deal returns 404
    - _Requirements: 1.1, 1.2, 1.3, 1.5, 1.6_

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Modify DealService.create_deal to generate AI ad ideas upfront
  - [x] 5.1 Update create_deal method to call LLM service before persisting
    - Call llm_service.generate_ad_idea() with deal details
    - Pass generated ad_idea to Deal constructor
    - Ensure ad_idea is always populated (fallback on LLM failure)
    - Return deal with ad_idea field populated
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.6_

  - [ ]* 5.2 Write property test for ad_idea population
    - **Property 6: New deals always have ad_idea populated**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4**

  - [ ]* 5.3 Write unit tests for AI generation scenarios
    - Test deal creation with successful AI generation
    - Test deal creation with AI generation failure (uses fallback)
    - Test ad_idea is non-empty string in all cases
    - _Requirements: 2.2, 2.3, 2.4_

- [x] 6. Implement business response endpoints
  - [x] 6.1 Add accept_counter method to DealService
    - Validate deal exists and status is countered
    - If counter_amount provided, update offer_amount to counter_amount
    - If counter_deliverables provided, update deliverables to counter_deliverables
    - Transition status to accepted
    - Preserve counter_history
    - Return updated deal
    - _Requirements: 5.1, 5.2, 5.3, 4.6_

  - [x] 6.2 Add reject_counter method to DealService
    - Validate deal exists and status is countered
    - Transition status to rejected
    - Return updated deal
    - _Requirements: 5.4_

  - [ ]* 6.3 Write property test for accept counter transition
    - **Property 14: Accepting counter transitions to accepted**
    - **Validates: Requirements 5.1**

  - [ ]* 6.4 Write property test for accept counter applies terms
    - **Property 15: Accepting counter applies counter terms**
    - **Validates: Requirements 5.2, 5.3**

  - [ ]* 6.5 Write property test for reject counter transition
    - **Property 16: Rejecting counter transitions to rejected**
    - **Validates: Requirements 5.4**

  - [ ]* 6.6 Write property test for invalid state transitions
    - **Property 17: Invalid state transitions return 409**
    - **Validates: Requirements 5.5, 5.6**

  - [ ]* 6.7 Write property test for counter history preservation
    - **Property 13: Counter history is preserved across state transitions**
    - **Validates: Requirements 4.6**

  - [ ]* 6.8 Write unit tests for business response edge cases
    - Test accept counter with counter terms applies them correctly
    - Test accept counter without counter terms keeps original
    - Test accept counter on pending deal returns 409
    - Test reject counter on pending deal returns 409
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

- [x] 7. Implement business counter method
  - [x] 7.1 Add business_counter method to DealService
    - Validate deal exists and status is countered
    - Accept optional message, counter_amount, counter_deliverables
    - Create CounterOffer entry with author="business"
    - Add to counter_history
    - Update counter fields with business values
    - Keep status as countered
    - Return updated deal
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [ ]* 7.2 Write property test for business counter acceptance
    - **Property 18: Business counter is accepted for countered deals**
    - **Validates: Requirements 6.1, 6.2**

  - [ ]* 7.3 Write property test for counter history author attribution
    - **Property 19: Counter history maintains author attribution**
    - **Validates: Requirements 6.3**

  - [ ]* 7.4 Write property test for multiple counter rounds
    - **Property 20: Multiple counter rounds are preserved**
    - **Validates: Requirements 6.4**

  - [ ]* 7.5 Write unit tests for business counter scenarios
    - Test business counter with message only
    - Test business counter with revised terms
    - Test business counter on pending deal returns 409
    - Test multiple round negotiation (creator → business → creator)
    - _Requirements: 6.1, 6.2, 6.4_

- [x] 8. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Add API endpoints to deals router
  - Add PUT /api/deals/:id/counter endpoint calling counter_deal
  - Add PUT /api/deals/:id/accept-counter endpoint calling accept_counter
  - Add PUT /api/deals/:id/reject-counter endpoint calling reject_counter
  - Add PUT /api/deals/:id/business-counter endpoint calling business_counter
  - Add authentication and authorization checks (creator for counter, business for accept/reject/business-counter)
  - Add error handling for 404, 409, 422 responses
  - _Requirements: 1.1, 1.2, 1.3, 5.1, 5.4, 5.5, 5.6, 6.1, 6.2_

- [ ]* 9.1 Write integration tests for counter endpoints
  - Test POST /api/deals returns deal with ad_idea
  - Test PUT /api/deals/:id/counter with valid payload
  - Test PUT /api/deals/:id/accept-counter applies terms
  - Test PUT /api/deals/:id/reject-counter transitions status
  - Test PUT /api/deals/:id/business-counter adds to history
  - Test authorization (creator can counter, business cannot)
  - Test authorization (business can accept/reject/counter, creator cannot)
  - _Requirements: 1.1, 2.1, 5.1, 5.4, 6.1_

- [x] 10. Update Creator Dashboard to display countered deals
  - [x] 10.1 Modify deal filtering to include countered status
    - Update dashboard query/filter to fetch deals with status=countered
    - Display countered deals in a separate section or with visual distinction
    - _Requirements: 3.1, 3.7_

  - [x] 10.2 Add counter form UI to pending deals
    - Add counter button to pending deal cards
    - Create counter form with message textarea, amount input, deliverables textarea
    - Wire form to PUT /api/deals/:id/counter endpoint
    - Show validation errors for invalid amounts
    - _Requirements: 1.1, 1.2, 1.3, 1.5_

  - [x] 10.3 Display counter data in countered deal cards
    - Show counter_message if present
    - Show counter_amount if present
    - Show counter_deliverables if present
    - Display counter_history timeline with author and timestamp
    - _Requirements: 3.3, 3.4, 6.5_

  - [x] 10.4 Display ad_idea in pending deal cards
    - Add ad idea section to pending deal display
    - Show ad_idea text prominently
    - _Requirements: 2.5_

  - [ ]* 10.5 Write property test for creator dashboard displays ad idea
    - **Property 7: Creator dashboard displays ad idea**
    - **Validates: Requirements 2.5**

  - [ ]* 10.6 Write property test for countered deals visibility
    - **Property 8: Countered deals appear in creator dashboard**
    - **Validates: Requirements 3.1**

  - [ ]* 10.7 Write property test for counter data display
    - **Property 10: Creator dashboard displays counter data**
    - **Validates: Requirements 3.3, 3.4**

  - [ ]* 10.8 Write property test for counter history chronological order
    - **Property 21: Counter history is displayed chronologically**
    - **Validates: Requirements 6.5, 6.6**

- [x] 11. Update Business Dashboard to display countered deals
  - [x] 11.1 Modify deal filtering to include countered status
    - Update dashboard query/filter to fetch deals with status=countered
    - Display countered deals in a separate section or with visual distinction
    - _Requirements: 3.2, 3.8_

  - [x] 11.2 Display counter data in countered deal cards
    - Show counter_message if present
    - Show counter_amount if present
    - Show counter_deliverables if present
    - Display counter_history timeline with author and timestamp
    - _Requirements: 3.5, 3.6, 6.6_

  - [x] 11.3 Add accept/reject counter buttons
    - Add "Accept Counter" button to countered deals
    - Add "Reject Counter" button to countered deals
    - Wire buttons to PUT /api/deals/:id/accept-counter and reject-counter endpoints
    - Show confirmation dialog before accepting (especially if terms changed)
    - _Requirements: 5.1, 5.4_

  - [x] 11.4 Add business counter form UI
    - Add "Counter Back" button to countered deals
    - Create business counter form with message, amount, deliverables inputs
    - Wire form to PUT /api/deals/:id/business-counter endpoint
    - _Requirements: 6.1, 6.2_

  - [ ]* 11.5 Write property test for countered deals visibility
    - **Property 9: Countered deals appear in business dashboard**
    - **Validates: Requirements 3.2**

  - [ ]* 11.6 Write property test for counter data display
    - **Property 11: Business dashboard displays counter data**
    - **Validates: Requirements 3.5, 3.6**

- [x] 12. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties across all inputs
- Unit tests validate specific examples and edge cases
- Counter history enables multi-round negotiation tracking
- AI ad ideas are generated upfront to inform creator decisions before acceptance
