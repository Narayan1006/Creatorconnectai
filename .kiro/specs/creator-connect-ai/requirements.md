# Requirements Document

## Introduction

CreatorConnectAI is a premium AI-powered full-stack web platform that connects businesses with content creators. The platform uses a RAG-based matching pipeline (FAISS vector search + LLM embeddings) to semantically match brands with relevant creators, automates deal workflows from offer creation through content verification, and triggers a blockchain-ready payment state upon successful content validation. The frontend is built with React + Tailwind CSS + Framer Motion using an Apple-inspired dark aesthetic. The backend is FastAPI with Python AI services.

## Glossary

- **System**: The CreatorConnectAI platform as a whole
- **Business_User**: A brand or company seeking to engage content creators
- **Creator**: An influencer or content producer registered on the platform
- **RAG_Engine**: The Retrieval-Augmented Generation matching engine backed by FAISS
- **Embedding_Service**: The service that converts text into vector embeddings
- **FAISS_Store**: The FAISS vector index storing creator embeddings
- **Matching_Service**: The orchestration layer that runs RAG-based creator retrieval
- **Deal_Service**: The service managing the full deal lifecycle state machine
- **Verification_Service**: The service that compares ad ideas against submitted content using cosine similarity
- **Payment_Service**: The service managing payment state transitions (blockchain-ready mock)
- **LLM_Service**: The large language model service used for embedding and ad idea generation
- **Auth_Service**: The JWT-based authentication and authorization service
- **Deal**: A negotiated agreement between a Business_User and a Creator
- **DealStatus**: The current state of a Deal within the state machine
- **VerificationResult**: The output of content verification including match score and pass/fail
- **PaymentRecord**: A record of a payment state transition for a Deal
- **MatchQuery**: The input submitted by a Business_User to find matching creators
- **Ad_Idea**: An LLM-generated advertising concept produced when a deal is accepted

---

## Requirements

### Requirement 1: User Authentication and Role-Based Access

**User Story:** As a user, I want to register and log in with a role (Business or Creator), so that I can access the features relevant to my persona.

#### Acceptance Criteria

1. WHEN a user submits valid registration credentials with a role selection, THE Auth_Service SHALL create a new account and return a JWT token
2. WHEN a user submits valid login credentials, THE Auth_Service SHALL return a signed JWT token containing the user's role
3. WHEN a request is made to any `/api/*` endpoint without a valid JWT token, THE System SHALL return HTTP 401
4. WHEN a Creator attempts to access a Business-only endpoint (e.g., `/api/match`), THE Auth_Service SHALL return HTTP 403
5. WHEN a Business_User attempts to access a Creator-only endpoint, THE Auth_Service SHALL return HTTP 403
6. IF a JWT token is expired or malformed, THEN THE Auth_Service SHALL return HTTP 401 with a descriptive error message

---

### Requirement 2: Creator Profile Management

**User Story:** As a Creator, I want to create and manage my profile with niche, platform, and stats, so that I can be discovered by businesses through AI matching.

#### Acceptance Criteria

1. THE System SHALL store Creator profiles containing: id, name, avatar_url, niche (array), platform, followers, engagement_rate, bio, and optional portfolio_url
2. WHEN a Creator submits a profile with an engagement_rate outside [0.0, 1.0], THE System SHALL reject the request with HTTP 422
3. WHEN a Creator submits a profile with followers less than or equal to zero, THE System SHALL reject the request with HTTP 422
4. WHEN a Creator submits a profile with an empty niche array, THE System SHALL reject the request with HTTP 422
5. WHEN a Creator profile is created or updated, THE Embedding_Service SHALL generate an embedding from the creator's bio, niche, and platform and store it in the FAISS_Store
6. WHEN a Creator profile is indexed, THE FAISS_Store SHALL increase its index size by exactly one entry

---

### Requirement 3: RAG-Based Creator Matching

**User Story:** As a Business_User, I want to submit a product description, target audience, and budget to find the most relevant creators, so that I can identify the best partners for my campaign.

#### Acceptance Criteria

1. WHEN a Business_User submits a MatchQuery with product_description (min 10 chars), target_audience (min 5 chars), and a positive budget, THE Matching_Service SHALL return a ranked list of creators
2. THE Matching_Service SHALL return at most `top_k` creators (default 5) per query
3. THE Matching_Service SHALL return creators sorted in descending order by match_score
4. FOR ALL creators returned by the Matching_Service, THE System SHALL ensure each match_score is in the range [0.0, 1.0]
5. WHEN the FAISS_Store is empty or unavailable, THE Matching_Service SHALL return HTTP 503 with error code `FAISS_NOT_READY`
6. WHEN a MatchQuery is submitted, THE RAG_Engine SHALL build a composite query text from product_description, target_audience, and budget, embed it, and perform similarity search against the FAISS_Store
7. IF a MatchQuery contains a product_description shorter than 10 characters, THEN THE System SHALL return HTTP 422

---

### Requirement 4: Ad Idea Generation

**User Story:** As a Business_User, I want an AI-generated ad concept when a creator accepts my deal, so that I have a creative starting point for the campaign.

#### Acceptance Criteria

1. WHEN a Creator accepts a Deal, THE LLM_Service SHALL generate an Ad_Idea based on the deal's product description and the creator's niche
2. THE LLM_Service SHALL return a non-empty string as the Ad_Idea
3. WHEN the LLM_Service exceeds a 30-second timeout, THE System SHALL return a fallback ad idea template and log the error
4. WHEN the LLM_Service fails after 3 retry attempts with exponential backoff, THE System SHALL use the fallback template

---

### Requirement 5: Deal Lifecycle Management

**User Story:** As a Business_User, I want to send offers to creators and track the deal through acceptance, content submission, and verification, so that I can manage my campaigns end-to-end.

#### Acceptance Criteria

1. WHEN a Business_User submits a deal with a creator_id, offer_amount, deliverables, and deadline, THE Deal_Service SHALL create a Deal with status `pending`
2. WHEN a Creator accepts a pending Deal, THE Deal_Service SHALL transition the Deal status to `accepted`
3. WHEN a Creator rejects a pending Deal, THE Deal_Service SHALL transition the Deal status to `rejected`
4. WHEN a Creator counters a pending Deal, THE Deal_Service SHALL transition the Deal status to `countered`
5. WHEN a Creator submits content for an accepted Deal, THE Deal_Service SHALL transition the Deal status to `content_submitted`
6. WHEN a client attempts an invalid state transition (e.g., accepting an already-accepted deal), THE Deal_Service SHALL return HTTP 409 with the current status and attempted action
7. THE Deal_Service SHALL only allow the following state transitions:
   - `pending` → `accepted` (ACCEPT)
   - `pending` → `rejected` (REJECT)
   - `pending` → `countered` (COUNTER)
   - `accepted` → `content_submitted` (SUBMIT_CONTENT)
   - `content_submitted` → `verified` (VERIFY, score ≥ 0.75)
   - `content_submitted` → `revision_requested` (VERIFY, score < 0.75)
   - `revision_requested` → `content_submitted` (RESUBMIT)
   - `verified` → `completed` (COMPLETE)
8. WHEN a Deal status is updated, THE Deal_Service SHALL set the `updated_at` timestamp to the current time

---

### Requirement 6: Content Verification

**User Story:** As a Business_User, I want submitted creator content to be automatically verified against the ad idea, so that I can ensure the content meets campaign requirements before payment.

#### Acceptance Criteria

1. WHEN a Creator submits a content_url for a Deal in `accepted` status, THE Verification_Service SHALL compute a cosine similarity score between the Ad_Idea embedding and the submitted content embedding
2. FOR ALL verification results, THE System SHALL ensure match_score is in the range [0.0, 1.0]
3. WHEN the match_score is greater than or equal to 0.75, THE Verification_Service SHALL set `passed = true` and transition the Deal to `verified`
4. WHEN the match_score is less than 0.75, THE Verification_Service SHALL set `passed = false` and transition the Deal to `revision_requested`
5. WHEN the submitted content URL is inaccessible or cannot be processed, THE Verification_Service SHALL return a VerificationResult with match_score 0.0, passed false, and feedback "Content could not be processed"
6. WHEN either the ad_idea or submitted_content produces a zero-magnitude embedding vector, THE Verification_Service SHALL return match_score 0.0 with feedback "Empty embedding"
7. THE Verification_Service SHALL include a non-empty feedback string in every VerificationResult

---

### Requirement 7: Payment State Management

**User Story:** As a Business_User, I want payment to be automatically triggered when content is verified, so that creators are compensated promptly upon successful delivery.

#### Acceptance Criteria

1. WHEN a Deal transitions to `verified` status, THE Payment_Service SHALL automatically trigger a payment-ready state for that Deal
2. WHEN payment is triggered, THE Payment_Service SHALL create a PaymentRecord with status `ready_for_payment` and a mock blockchain_tx_hash
3. FOR ALL Deals, THE System SHALL ensure that payment_status is `ready_for_payment` only when deal status is `verified` or later
4. WHEN a Business_User queries payment status for a Deal, THE Payment_Service SHALL return the current PaymentRecord
5. IF a payment trigger is attempted for a Deal not in `verified` status, THEN THE Payment_Service SHALL return HTTP 409

---

### Requirement 8: Business Dashboard

**User Story:** As a Business_User, I want a dedicated dashboard to submit matching queries, view creator results, and manage my deals, so that I can run campaigns efficiently.

#### Acceptance Criteria

1. WHEN a Business_User loads the dashboard, THE System SHALL display a form with fields for product_description, target_audience, and budget
2. WHEN matching results are returned, THE System SHALL render creator cards showing name, avatar, niche, follower count, engagement rate, and match score
3. WHEN a Business_User clicks to send an offer from a creator card, THE System SHALL open an offer creation modal
4. WHEN a Business_User submits an offer, THE System SHALL call the deal creation API and display the resulting deal status

---

### Requirement 9: Creator Dashboard

**User Story:** As a Creator, I want a dedicated dashboard to view incoming offers and manage my deal responses, so that I can efficiently handle business partnerships.

#### Acceptance Criteria

1. WHEN a Creator loads the dashboard, THE System SHALL fetch and display all incoming Deals for that Creator
2. WHEN a Creator views a Deal, THE System SHALL display offer amount, deliverables, deadline, and current status
3. WHEN a Creator accepts, rejects, or counters a Deal, THE System SHALL call the appropriate API endpoint and update the displayed status
4. WHEN a Deal is in `accepted` status, THE System SHALL display the generated Ad_Idea to the Creator
5. WHEN a Creator submits a content URL, THE System SHALL call the content submission API and display the VerificationResult

---

### Requirement 10: Creator Showcase (Public)

**User Story:** As a visitor, I want to browse featured creators on the homepage without logging in, so that I can understand the platform's value before registering.

#### Acceptance Criteria

1. THE System SHALL expose a public endpoint that returns a list of featured Creator profiles without requiring authentication
2. WHEN the homepage loads, THE System SHALL display creator cards with name, avatar, niche, platform, followers, and engagement rate
3. THE System SHALL NOT expose creator embedding vectors in any public API response

---

### Requirement 11: Embedding Service and FAISS Indexing

**User Story:** As a system operator, I want creator embeddings to be consistently generated and stored, so that the matching service always has accurate vector representations.

#### Acceptance Criteria

1. FOR ALL text inputs to the Embedding_Service, THE System SHALL produce an embedding vector of exactly EMBEDDING_DIM dimensions (1536 for OpenAI, 384 for local model)
2. WHEN the FAISS_Store is built with one embedding model and a query is made with a different model producing a different dimension, THE System SHALL return HTTP 500 with error "Embedding dimension mismatch"
3. WHEN an embedding dimension mismatch is detected, THE System SHALL block all matching requests until a full reindex is completed
4. THE System SHALL provide an authenticated admin endpoint `/api/admin/reindex` that triggers full re-embedding of all creators
5. WHEN the admin reindex endpoint is called, THE Embedding_Service SHALL re-embed all Creator profiles and rebuild the FAISS_Store

---

### Requirement 12: Frontend Aesthetic and Animation

**User Story:** As a user, I want the platform to have a premium Apple-inspired dark aesthetic with smooth animations, so that the experience feels polished and professional.

#### Acceptance Criteria

1. THE System SHALL render all pages using a dark background color (#0B0B0C), primary text (#FFFFFF), and accent color (#8E8E93)
2. WHEN the homepage loads, THE System SHALL display a full-screen hero section with an animated dark gradient background and floating creator profile cards
3. WHEN creator cards enter the viewport, THE System SHALL animate them using Framer Motion entrance animations
4. THE System SHALL use GPU-accelerated CSS properties (`will-change: transform`) for all Framer Motion animations
5. THE System SHALL achieve a homepage JavaScript bundle size under 200KB gzipped via React.lazy and Suspense code splitting

---

### Requirement 13: API Security and Validation

**User Story:** As a system operator, I want all API inputs validated and secured, so that the platform is protected against malicious or malformed requests.

#### Acceptance Criteria

1. THE System SHALL validate all incoming request bodies using Pydantic v2 models on the backend
2. WHEN a deal offer_amount is submitted, THE System SHALL validate server-side that the value is positive and within configured limits
3. WHEN a content_url is submitted, THE System SHALL validate it against an allowlist of trusted CDN domains before processing
4. THE System SHALL sanitize all user-provided text before interpolating into LLM prompts to prevent prompt injection
5. WHEN an invalid content_url domain is submitted, THE System SHALL return HTTP 422 with a descriptive validation error
