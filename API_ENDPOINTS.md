# CreatorConnectAI API Endpoints

**Base URL:** `http://localhost:8000`  
**API Documentation:** `http://localhost:8000/docs` (Swagger UI)

---

## 📋 Table of Contents
1. [Authentication](#authentication)
2. [Creators](#creators)
3. [Matching](#matching)
4. [Deals](#deals)
5. [Admin](#admin)

---

## 🔐 Authentication

### Register User
**POST** `/api/auth/register`

Register a new user (business or creator).

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "role": "business"  // or "creator"
}
```

**Response:** `201 Created`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "user123",
    "email": "user@example.com",
    "role": "business"
  }
}
```

---

### Login
**POST** `/api/auth/login`

Authenticate and get access token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "user123",
    "email": "user@example.com",
    "role": "business"
  }
}
```

**Error Response:** `401 Unauthorized`
```json
{
  "detail": "Invalid credentials"
}
```

---

## 👤 Creators

### Create Creator Profile
**POST** `/api/creators`

Create a new creator profile (Creator only).

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "name": "Jane Doe",
  "bio": "Fashion and lifestyle content creator",
  "niche": ["fashion", "lifestyle", "beauty"],
  "platform": "Instagram",
  "followers": 50000,
  "engagement_rate": 0.045,
  "avatar_url": "https://example.com/avatar.jpg"
}
```

**Response:** `201 Created`
```json
{
  "_id": "creator123",
  "name": "Jane Doe",
  "bio": "Fashion and lifestyle content creator",
  "niche": ["fashion", "lifestyle", "beauty"],
  "platform": "Instagram",
  "followers": 50000,
  "engagement_rate": 0.045,
  "avatar_url": "https://example.com/avatar.jpg",
  "user_id": "user123"
}
```

---

### Get My Creator Profile
**GET** `/api/creators/me`

Get the current user's creator profile.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{
  "_id": "creator123",
  "name": "Jane Doe",
  "bio": "Fashion and lifestyle content creator",
  "niche": ["fashion", "lifestyle", "beauty"],
  "platform": "Instagram",
  "followers": 50000,
  "engagement_rate": 0.045,
  "avatar_url": "https://example.com/avatar.jpg"
}
```

---

### Get Featured Creators
**GET** `/api/creators/featured`

Get up to 10 featured creators (Public, no auth required).

**Response:** `200 OK`
```json
[
  {
    "_id": "creator123",
    "name": "Jane Doe",
    "niche": ["fashion", "lifestyle"],
    "platform": "Instagram",
    "followers": 50000,
    "engagement_rate": 0.045,
    "avatar_url": "https://example.com/avatar.jpg"
  }
]
```

---

### Get Creator by ID
**GET** `/api/creators/{creator_id}`

Get a specific creator's profile (Authenticated).

**Headers:**
```
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{
  "_id": "creator123",
  "name": "Jane Doe",
  "bio": "Fashion and lifestyle content creator",
  "niche": ["fashion", "lifestyle", "beauty"],
  "platform": "Instagram",
  "followers": 50000,
  "engagement_rate": 0.045,
  "avatar_url": "https://example.com/avatar.jpg"
}
```

---

### Update Creator Profile
**PUT** `/api/creators/{creator_id}`

Update creator profile (Creator only, own profile).

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "bio": "Updated bio",
  "followers": 55000,
  "engagement_rate": 0.048
}
```

**Response:** `200 OK`
```json
{
  "_id": "creator123",
  "name": "Jane Doe",
  "bio": "Updated bio",
  "niche": ["fashion", "lifestyle", "beauty"],
  "platform": "Instagram",
  "followers": 55000,
  "engagement_rate": 0.048,
  "avatar_url": "https://example.com/avatar.jpg"
}
```

---

## 🔍 Matching

### Match Creators
**POST** `/api/match`

AI-powered creator matching using RAG (Business only).

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "product_description": "Sustainable fashion brand targeting eco-conscious millennials",
  "target_audience": "Women aged 25-35 interested in sustainable fashion",
  "budget": 5000,
  "top_k": 10
}
```

**Response:** `200 OK`
```json
{
  "results": [
    {
      "creator": {
        "_id": "creator123",
        "name": "Jane Doe",
        "niche": ["fashion", "sustainability"],
        "platform": "Instagram",
        "followers": 50000,
        "engagement_rate": 0.045,
        "avatar_url": "https://example.com/avatar.jpg"
      },
      "match_score": 0.87
    }
  ],
  "total": 10
}
```

---

## 💼 Deals

### Create Deal
**POST** `/api/deals`

Create a new deal with AI-generated ad idea (Business only).

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "business_id": "business123",
  "creator_id": "creator123",
  "offer_amount": 2500,
  "deliverables": "2 Instagram posts + 3 stories",
  "deadline": "2026-05-01T00:00:00Z"
}
```

**Response:** `201 Created`
```json
{
  "_id": "deal123",
  "business_id": "business123",
  "creator_id": "creator123",
  "offer_amount": 2500,
  "deliverables": "2 Instagram posts + 3 stories",
  "deadline": "2026-05-01T00:00:00Z",
  "status": "pending",
  "ad_idea": "Create authentic behind-the-scenes content showcasing sustainable fashion choices...",
  "created_at": "2026-04-01T10:00:00Z",
  "updated_at": "2026-04-01T10:00:00Z"
}
```

---

### Get Deals
**GET** `/api/deals`

Get all deals for the current user (filtered by role).

**Headers:**
```
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
[
  {
    "_id": "deal123",
    "business_id": "business123",
    "creator_id": "creator123",
    "offer_amount": 2500,
    "deliverables": "2 Instagram posts + 3 stories",
    "deadline": "2026-05-01T00:00:00Z",
    "status": "pending",
    "ad_idea": "Create authentic behind-the-scenes content...",
    "created_at": "2026-04-01T10:00:00Z",
    "updated_at": "2026-04-01T10:00:00Z"
  }
]
```

---

### Accept Deal
**PUT** `/api/deals/{deal_id}/accept`

Accept a pending deal (Creator only).

**Headers:**
```
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{
  "_id": "deal123",
  "status": "accepted",
  "ad_idea": "Create authentic behind-the-scenes content...",
  "updated_at": "2026-04-01T11:00:00Z"
}
```

---

### Reject Deal
**PUT** `/api/deals/{deal_id}/reject`

Reject a pending deal (Creator only).

**Headers:**
```
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{
  "_id": "deal123",
  "status": "rejected",
  "updated_at": "2026-04-01T11:00:00Z"
}
```

---

### Counter Deal
**PUT** `/api/deals/{deal_id}/counter`

Counter a pending deal with message and/or terms (Creator only).

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "message": "I'd love to work with you! However, I'd need a higher budget for this scope.",
  "counter_amount": 3000,
  "counter_deliverables": "2 Instagram posts + 5 stories + 1 Reel"
}
```

**Response:** `200 OK`
```json
{
  "_id": "deal123",
  "status": "countered",
  "counter_message": "I'd love to work with you! However, I'd need a higher budget for this scope.",
  "counter_amount": 3000,
  "counter_deliverables": "2 Instagram posts + 5 stories + 1 Reel",
  "counter_history": [
    {
      "author": "creator",
      "message": "I'd love to work with you! However, I'd need a higher budget for this scope.",
      "proposed_amount": 3000,
      "proposed_deliverables": "2 Instagram posts + 5 stories + 1 Reel",
      "timestamp": "2026-04-01T11:00:00Z"
    }
  ],
  "updated_at": "2026-04-01T11:00:00Z"
}
```

---

### Accept Counter
**PUT** `/api/deals/{deal_id}/accept-counter`

Accept a countered deal (Business only). Applies counter terms if present.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{
  "_id": "deal123",
  "status": "accepted",
  "offer_amount": 3000,
  "deliverables": "2 Instagram posts + 5 stories + 1 Reel",
  "counter_history": [...],
  "updated_at": "2026-04-01T12:00:00Z"
}
```

---

### Reject Counter
**PUT** `/api/deals/{deal_id}/reject-counter`

Reject a countered deal (Business only).

**Headers:**
```
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{
  "_id": "deal123",
  "status": "rejected",
  "updated_at": "2026-04-01T12:00:00Z"
}
```

---

### Business Counter
**PUT** `/api/deals/{deal_id}/business-counter`

Counter back on a countered deal (Business only).

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "message": "How about we meet in the middle?",
  "counter_amount": 2750,
  "counter_deliverables": "2 Instagram posts + 4 stories"
}
```

**Response:** `200 OK`
```json
{
  "_id": "deal123",
  "status": "countered",
  "counter_message": "How about we meet in the middle?",
  "counter_amount": 2750,
  "counter_deliverables": "2 Instagram posts + 4 stories",
  "counter_history": [
    {
      "author": "creator",
      "message": "I'd love to work with you!...",
      "proposed_amount": 3000,
      "timestamp": "2026-04-01T11:00:00Z"
    },
    {
      "author": "business",
      "message": "How about we meet in the middle?",
      "proposed_amount": 2750,
      "proposed_deliverables": "2 Instagram posts + 4 stories",
      "timestamp": "2026-04-01T12:00:00Z"
    }
  ],
  "updated_at": "2026-04-01T12:00:00Z"
}
```

---

### Submit Content
**POST** `/api/deals/{deal_id}/submit`

Submit content URL for an accepted deal (Creator only).

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "content_url": "https://instagram.com/p/abc123"
}
```

**Response:** `200 OK`
```json
{
  "_id": "deal123",
  "status": "content_submitted",
  "content_url": "https://instagram.com/p/abc123",
  "updated_at": "2026-05-01T10:00:00Z"
}
```

---

## 🔧 Admin

### Reindex FAISS
**POST** `/api/admin/reindex`

Rebuild FAISS index from all creator profiles (Authenticated).

**Headers:**
```
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{
  "reindexed": 150,
  "message": "Reindex complete"
}
```

---

## 📊 Status Codes

| Code | Description |
|------|-------------|
| 200 | OK - Request successful |
| 201 | Created - Resource created successfully |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Missing or invalid token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource not found |
| 409 | Conflict - Invalid state transition |
| 422 | Unprocessable Entity - Validation error |
| 500 | Internal Server Error |
| 503 | Service Unavailable - FAISS not ready |

---

## 🔑 Authentication

All protected endpoints require a JWT token in the Authorization header:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Get the token from `/api/auth/login` or `/api/auth/register`.

---

## 🎯 Deal Status Flow

```
pending → accepted → content_submitted → verified → completed
   ↓         ↓
countered  rejected
   ↓
accepted/rejected
```

**Valid Transitions:**
- `pending` → `accepted`, `rejected`, `countered`
- `countered` → `accepted`, `rejected`, `countered` (business counter)
- `accepted` → `content_submitted`
- `content_submitted` → `verified`, `revision_requested`
- `revision_requested` → `content_submitted`
- `verified` → `completed`

---

## 🧪 Testing Endpoints

### Using cURL

**Register:**
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123","role":"business"}'
```

**Login:**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'
```

**Match Creators:**
```bash
curl -X POST http://localhost:8000/api/match \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "product_description":"Sustainable fashion brand",
    "target_audience":"Eco-conscious millennials",
    "budget":5000,
    "top_k":10
  }'
```

---

## 📝 Notes

1. **CORS:** Frontend at `http://localhost:5173` is whitelisted
2. **Rate Limiting:** Not currently implemented (recommended for production)
3. **Pagination:** Not currently implemented for list endpoints
4. **Filtering:** Limited filtering available on GET endpoints
5. **Webhooks:** Not currently implemented

---

## 🔗 Related Documentation

- [README.md](README.md) - Project overview and setup
- [QA_REPORT.md](QA_REPORT.md) - Testing and quality assurance
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

**Last Updated:** April 1, 2026  
**API Version:** 0.1.0
