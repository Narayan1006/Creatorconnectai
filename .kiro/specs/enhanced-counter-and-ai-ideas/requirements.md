# Requirements Document

## Introduction

This feature enhances the deal negotiation workflow by allowing creators to counter offers with messages and proposed terms, and by generating AI ad ideas upfront with initial offers so creators can review them before making decisions. Currently, countering only changes status without communication, countered deals disappear from dashboards, and AI ad ideas are generated after acceptance rather than with the initial offer.

## Glossary

- **Deal_System**: The backend service managing deal lifecycle and state transitions
- **Counter_Service**: The service handling counter offer creation and message exchange
- **AI_Generator**: The LLM service that generates ad idea concepts
- **Creator_Dashboard**: The frontend interface where creators view and manage deals
- **Business_Dashboard**: The frontend interface where businesses view and manage deals
- **Counter_Message**: A text message from creator explaining their counter position
- **Counter_Terms**: Optional proposed changes to offer amount or deliverables
- **Initial_Offer**: The deal creation request from business to creator
- **Ad_Idea**: The AI-generated advertising concept for a deal

## Requirements

### Requirement 1: Counter with Message and Terms

**User Story:** As a creator, I want to counter an offer with a message and optionally propose new terms, so that I can negotiate effectively with the business.

#### Acceptance Criteria

1. WHEN a creator counters a pending deal, THE Counter_Service SHALL accept an optional counter message
2. WHEN a creator counters a pending deal, THE Counter_Service SHALL accept an optional counter amount
3. WHEN a creator counters a pending deal, THE Counter_Service SHALL accept optional modified deliverables
4. WHEN counter message is provided, THE Counter_Service SHALL store the message with the deal
5. WHEN counter amount is provided, THE Counter_Service SHALL validate the amount is positive
6. WHEN counter amount exceeds maximum allowed, THE Counter_Service SHALL return an error
7. THE Deal_System SHALL preserve the original offer amount and deliverables when counter terms are proposed
8. WHEN a deal is countered, THE Deal_System SHALL transition status to countered and update the timestamp

### Requirement 2: AI Ad Idea Generation with Initial Offer

**User Story:** As a creator, I want to see the AI-generated ad idea when I receive an offer, so that I can evaluate the creative concept before accepting or countering.

#### Acceptance Criteria

1. WHEN a business creates a new deal, THE AI_Generator SHALL generate an ad idea before persisting the deal
2. WHEN AI generation succeeds, THE Deal_System SHALL store the ad idea with the pending deal
3. IF AI generation fails after all retries, THE Deal_System SHALL store a fallback ad idea template
4. THE Deal_System SHALL ensure every new deal has an ad_idea field populated before returning to the client
5. WHEN a creator views a pending deal, THE Creator_Dashboard SHALL display the ad idea
6. THE AI_Generator SHALL use the same sanitization and timeout logic as the existing accept flow

### Requirement 3: Countered Deals Visibility

**User Story:** As a creator, I want to see countered deals on my dashboard, so that I can track negotiations in progress.

#### Acceptance Criteria

1. WHEN a creator views their dashboard, THE Creator_Dashboard SHALL display deals with status countered
2. WHEN a business views their dashboard, THE Business_Dashboard SHALL display deals with status countered
3. WHEN displaying a countered deal, THE Creator_Dashboard SHALL show the counter message if present
4. WHEN displaying a countered deal, THE Creator_Dashboard SHALL show the counter terms if present
5. WHEN displaying a countered deal, THE Business_Dashboard SHALL show the counter message if present
6. WHEN displaying a countered deal, THE Business_Dashboard SHALL show the counter terms if present
7. THE Creator_Dashboard SHALL visually distinguish countered deals from pending and accepted deals
8. THE Business_Dashboard SHALL visually distinguish countered deals from pending and accepted deals

### Requirement 4: Counter Data Model

**User Story:** As a developer, I want the deal model to support counter negotiation data, so that counter messages and terms can be persisted and retrieved.

#### Acceptance Criteria

1. THE Deal_System SHALL add a counter_message field to the Deal model
2. THE Deal_System SHALL add a counter_amount field to the Deal model
3. THE Deal_System SHALL add a counter_deliverables field to the Deal model
4. THE Deal_System SHALL ensure counter fields are optional and default to None
5. WHEN serializing a deal to JSON, THE Deal_System SHALL include counter fields in the response
6. WHEN a deal transitions from countered to accepted, THE Deal_System SHALL preserve counter history

### Requirement 5: Business Response to Counter

**User Story:** As a business, I want to accept or reject a counter offer, so that I can complete the negotiation.

#### Acceptance Criteria

1. WHEN a business accepts a countered deal, THE Deal_System SHALL transition status from countered to accepted
2. WHEN a business accepts a countered deal with counter terms, THE Deal_System SHALL update the deal amount to counter_amount if provided
3. WHEN a business accepts a countered deal with counter terms, THE Deal_System SHALL update deliverables to counter_deliverables if provided
4. WHEN a business rejects a countered deal, THE Deal_System SHALL transition status from countered to rejected
5. IF a business attempts to accept a deal not in countered status, THE Deal_System SHALL return HTTP 409 with current status
6. IF a business attempts to reject a deal not in countered status, THE Deal_System SHALL return HTTP 409 with current status

### Requirement 6: Round-Trip Counter Negotiation

**User Story:** As a business, I want to counter a creator's counter offer, so that we can negotiate back and forth until we reach agreement.

#### Acceptance Criteria

1. WHEN a business counters a countered deal, THE Counter_Service SHALL accept a business counter message
2. WHEN a business counters a countered deal, THE Counter_Service SHALL accept revised terms
3. THE Deal_System SHALL store business counter messages separately from creator counter messages
4. WHEN a deal has multiple counter rounds, THE Deal_System SHALL preserve the counter history
5. WHEN displaying counter history, THE Creator_Dashboard SHALL show all counter messages in chronological order
6. WHEN displaying counter history, THE Business_Dashboard SHALL show all counter messages in chronological order

