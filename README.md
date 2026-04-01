# CreatorConnectAI

AI-powered platform connecting businesses with content creators through intelligent matching and automated deal management.

## 🚀 Features

### Core Features
- **AI-Powered Creator Matching** - RAG-based semantic search using FAISS vector embeddings
- **Automated Ad Idea Generation** - LLM-generated creative concepts for every deal
- **Multi-Round Negotiation** - Counter offers with message history and term modifications
- **Deal Lifecycle Management** - Complete workflow from offer to payment
- **Real-time Dashboards** - Separate interfaces for creators and businesses

### Technical Highlights
- FastAPI backend with async/await
- React + TypeScript frontend with Vite
- Firestore database for scalability
- FAISS vector search for semantic matching
- JWT authentication with role-based access
- Property-based testing for correctness

## 📋 Prerequisites

- Python 3.11+
- Node.js 18+
- Firebase project with Firestore enabled
- OpenAI API key (optional, for enhanced AI features)

## 🛠️ Installation

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend Setup

```bash
cd frontend
npm install
```

### Environment Configuration

Create `.env` file in the backend directory:

```env
# Firebase
FIREBASE_CREDENTIALS_PATH=firebase-service-account.json
FIREBASE_PROJECT_ID=your-project-id

# JWT
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440

# LLM (Optional)
OPENAI_API_KEY=your-openai-key
EMBEDDING_MODEL=local  # or "openai"

# FAISS
FAISS_INDEX_PATH=faiss_index
EMBEDDING_DIM=384
```

Create `.env` file in the frontend directory:

```env
VITE_API_URL=http://localhost:8000
```

## 🚀 Running the Application

### Start Backend

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at http://localhost:8000

### Start Frontend

```bash
cd frontend
npm run dev
```

Frontend will be available at http://localhost:5173

### Using Docker (Alternative)

```bash
docker-compose up
```

## 📚 API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🧪 Testing

### Run Backend Tests

```bash
cd backend
pytest -v
```

### Run Frontend Tests

```bash
cd frontend
npm test
```

## 📖 Project Structure

```
CreatorConnectAI/
├── backend/
│   ├── app/
│   │   ├── core/          # Auth, config, database
│   │   ├── models/        # Pydantic models
│   │   ├── routers/       # API endpoints
│   │   ├── services/      # Business logic
│   │   └── main.py        # FastAPI app
│   ├── tests/             # Backend tests
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── context/       # React context
│   │   └── main.tsx       # Entry point
│   └── package.json
├── .kiro/
│   └── specs/             # Feature specifications
├── docker-compose.yml
├── QA_REPORT.md          # Quality assurance report
└── README.md
```

## 🔑 Key Technologies

**Backend:**
- FastAPI - Modern async web framework
- Pydantic - Data validation
- Firebase Admin SDK - Firestore integration
- FAISS - Vector similarity search
- Sentence Transformers - Text embeddings
- PyJWT - Authentication

**Frontend:**
- React 18 - UI framework
- TypeScript - Type safety
- Vite - Build tool
- TailwindCSS - Styling
- Axios - HTTP client

## 🎯 User Flows

### Business User Flow
1. Register as business user
2. Search for creators using AI-powered matching
3. Review creator profiles with match scores
4. Send offers with auto-generated ad ideas
5. Negotiate terms through counter offers
6. Accept final terms and proceed to payment

### Creator User Flow
1. Register as creator user
2. Create detailed creator profile
3. Receive offers with AI-generated ad ideas
4. Review and counter offers with custom terms
5. Accept deals and submit content
6. Receive payment upon verification

## 🔐 Security Features

- JWT-based authentication
- Role-based access control (RBAC)
- Input validation and sanitization
- Secure password hashing
- CORS protection
- Rate limiting ready

## 📊 Performance

- FAISS search: <100ms for 10K creators
- API response time: <500ms average
- Embedding model pre-loaded at startup
- Efficient Firestore queries with indexing

## 🐛 Known Issues

See [QA_REPORT.md](QA_REPORT.md) for detailed testing results and known issues.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License.

## 👥 Authors

- Narayan - Initial work

## 🙏 Acknowledgments

- OpenAI for LLM capabilities
- Sentence Transformers for embeddings
- FAISS for vector search
- Firebase for backend infrastructure

## 📞 Support

For issues and questions, please open an issue on GitHub.

---

**Note:** This is a development version. For production deployment, ensure proper security configurations, environment variables, and monitoring are in place.
