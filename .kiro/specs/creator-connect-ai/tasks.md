# Tasks

## Task List

- [x] 1 Project Scaffolding and Infrastructure
  - [x] 1.1 Initialize React + Vite frontend with Tailwind CSS and Framer Motion
  - [x] 1.2 Initialize FastAPI backend with project structure (routers, services, models)
  - [x] 1.3 Set up MongoDB connection and Pydantic v2 data models
  - [x] 1.4 Set up FAISS vector store initialization and embedding service skeleton
  - [x] 1.5 Configure Docker Compose for local development (frontend, backend, MongoDB)
  - [x] 1.6 Set up JWT authentication middleware and role-based access control

- [x] 2 Data Models and Validation
  - [x] 2.1 Implement Creator Pydantic model with validation (engagement_rate [0,1], followers > 0, niche non-empty)
  - [x] 2.2 Implement BusinessUser Pydantic model
  - [x] 2.3 Implement Deal Pydantic model with DealStatus and PaymentStatus enums
  - [x] 2.4 Implement MatchQuery Pydantic model with field constraints (min lengths, positive budget)
  - [x] 2.5 Implement VerificationResult and PaymentRecord Pydantic models

- [x] 3 Authentication Service
  - [x] 3.1 Implement user registration endpoint with role selection (Business / Creator)
  - [x] 3.2 Implement login endpoint returning signed JWT with role claim
  - [x] 3.3 Implement JWT validation middleware for all protected /api/* routes
  - [x] 3.4 Implement role-based access control decorators/dependencies for Business-only and Creator-only endpoints
  - [x] 3.5 Write property tests: JWT contains role claim (Property 9, Req 1.4/1.5), unauthenticated requests return 401 (Property 16, Req 1.3)

- [x] 4 Embedding Service and FAISS Indexing
  - [x] 4.1 Implement EmbeddingService with OpenAI and local sentence-transformers fallback
  - [x] 4.2 Implement embed_and_index_creator function (composite text from bio + niche + platform)
  - [x] 4.3 Implement FAISS index initialization, load, and save logic
  - [x] 4.4 Implement admin reindex endpoint /api/admin/reindex
  - [x] 4.5 Implement embedding dimension mismatch detection and error response
  - [x] 4.6 Write property tests: embedding dimension consistency (Property 8, Req 11.1), FAISS count increments by 1 on index (Property 12, Req 2.5/2.6)

- [x] 5 Creator Profile Service
  - [x] 5.1 Implement CRUD endpoints for Creator profiles (POST /api/creators, GET /api/creators/:id, PUT /api/creators/:id)
  - [x] 5.2 Wire creator creation/update to trigger embedding and FAISS indexing (Req 2.5)
  - [x] 5.3 Implement public creator showcase endpoint (GET /api/creators/featured) — no auth, no embedding field in response
  - [x] 5.4 Write property tests: engagement_rate validation (Property 7, Req 2.2), embedding excluded from public response (Property 13, Req 10.3)

- [x] 6 RAG Matching Service
  - [x] 6.1 Implement MatchingService.match_creators with composite query text construction
  - [x] 6.2 Implement FAISS similarity_search_with_score and L2-to-similarity normalization
  - [x] 6.3 Implement POST /api/match endpoint (Business-only, validates MatchQuery)
  - [x] 6.4 Handle FAISS unavailable / empty index with HTTP 503 FAISS_NOT_READY
  - [x] 6.5 Write property tests: result count <= top_k (Property 1, Req 3.2), scores in [0,1] (Property 2, Req 3.4), results sorted descending (Property 3, Req 3.3)

- [x] 7 LLM Ad Idea Generation
  - [x] 7.1 Implement generate_ad_idea function using LangChain with product description + creator niche context
  - [x] 7.2 Implement 30-second timeout with exponential backoff retry (max 3 attempts)
  - [x] 7.3 Implement fallback ad idea template for LLM failures
  - [x] 7.4 Sanitize user input before LLM prompt interpolation (Req 13.4)

- [x] 8 Deal Service and State Machine
  - [x] 8.1 Implement DealService with create_deal (initial status: pending)
  - [x] 8.2 Implement transition_deal_status with full state machine validation
  - [x] 8.3 Implement deal endpoints: POST /api/deals, PUT /api/deals/:id/accept, PUT /api/deals/:id/reject, PUT /api/deals/:id/counter
  - [x] 8.4 Implement content submission endpoint POST /api/deals/:id/submit
  - [x] 8.5 Return HTTP 409 with current_status and attempted_action on invalid transitions
  - [x] 8.6 Set updated_at timestamp on every status change
  - [x] 8.7 Trigger ad idea generation when deal is accepted
  - [x] 8.8 Write property tests: new deal status is pending (Property 10, Req 5.1), invalid transitions return 409 (Property 6, Req 5.6/5.7)

- [x] 9 Content Verification Service
  - [x] 9.1 Implement VerificationService.verify with cosine similarity computation
  - [x] 9.2 Implement compute_cosine_similarity with zero-vector guard (returns 0.0 with "Empty embedding" feedback)
  - [x] 9.3 Implement content URL accessibility check with fallback result on failure
  - [x] 9.4 Clamp match_score to [0.0, 1.0] and set passed = (score >= 0.75)
  - [x] 9.5 Trigger deal status transition to verified or revision_requested based on result
  - [x] 9.6 Write property tests: passed iff score >= 0.75 (Property 4, Req 6.3/6.4), score in [0,1] (Property 2 pattern, Req 6.2), feedback always non-empty (Property 11, Req 6.7)

- [x] 10 Payment Service
  - [x] 10.1 Implement PaymentService.trigger_payment_ready creating a PaymentRecord with mock blockchain_tx_hash
  - [x] 10.2 Wire payment trigger to deal verification (called when deal transitions to verified)
  - [x] 10.3 Implement GET /api/deals/:id/payment endpoint
  - [x] 10.4 Return HTTP 409 if payment trigger attempted for non-verified deal
  - [x] 10.5 Write property tests: payment safety invariant — payment_status ready_for_payment implies deal.status is verified (Property 5, Req 7.3)

- [x] 11 API Security and Input Validation
  - [x] 11.1 Implement content URL domain allowlist validation (Req 13.3)
  - [x] 11.2 Implement offer_amount server-side range validation (positive, within configured max) (Req 13.2)
  - [x] 11.3 Write property tests: non-allowlisted content URLs rejected with 422 (Property 15, Req 13.3), non-positive offer_amount rejected with 422 (Property 14, Req 13.2)

- [x] 12 Frontend: Core Layout and Design System
  - [x] 12.1 Configure Tailwind with custom color palette (#0B0B0C background, #FFFFFF text, #8E8E93 accent)
  - [x] 12.2 Implement base layout component with dark theme
  - [x] 12.3 Implement React Router setup with routes for /, /login, /register, /business, /creator
  - [x] 12.4 Configure React.lazy + Suspense code splitting for dashboard routes

- [x] 13 Frontend: Landing Page and Hero Section
  - [x] 13.1 Implement HeroSection with animated dark gradient background (Framer Motion)
  - [x] 13.2 Implement floating creator profile cards with entrance animations (GPU-accelerated, will-change: transform)
  - [x] 13.3 Implement dual CTA buttons (For Businesses / For Creators)
  - [x] 13.4 Fetch and display featured creators from public /api/creators/featured endpoint

- [x] 14 Frontend: Creator Card Component
  - [x] 14.1 Implement CreatorCard component with showcase and match-result variants
  - [x] 14.2 Display avatar, name, niche, follower count, engagement rate
  - [x] 14.3 Display match score badge in match-result variant
  - [x] 14.4 Implement offer trigger callback on button click

- [x] 15 Frontend: Business Dashboard
  - [x] 15.1 Implement MatchQuery form (product_description, target_audience, budget fields)
  - [x] 15.2 Submit form to POST /api/match and render CreatorCard results
  - [x] 15.3 Implement offer creation modal triggered from CreatorCard
  - [x] 15.4 Submit offer to POST /api/deals and display resulting deal status

- [x] 16 Frontend: Creator Dashboard
  - [x] 16.1 Fetch and display incoming Deals from GET /api/deals (Creator view)
  - [x] 16.2 Implement OfferCard with accept, reject, and counter action buttons
  - [x] 16.3 Display Ad_Idea when deal is in accepted status
  - [x] 16.4 Implement content URL submission form and display VerificationResult
  - [x] 16.5 Display deal status timeline

- [x] 17 Frontend: Auth Pages
  - [x] 17.1 Implement registration form with role selection
  - [x] 17.2 Implement login form with JWT storage (httpOnly cookie or memory)
  - [x] 17.3 Implement auth context/provider for role-based route protection

- [x] 18 Integration and End-to-End Testing
  - [x] 18.1 Seed FAISS index with 20 dummy creators for integration tests
  - [x] 18.2 Write end-to-end integration test: match query → create deal → accept → submit content → verify → check payment status
  - [x] 18.3 Validate API contract against OpenAPI schema for all endpoints
