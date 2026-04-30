# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Julius Baer hackathon project implementing two agentic AI-driven AML (Anti-Money Laundering) solutions:

1. **Part 1: Real-Time AML Monitoring & Alerts** - Monitors regulatory changes and client transactions to detect AML risks
2. **Part 2: Document & Image Corroboration** - Automates verification of client corroboration documents

## Architecture

The project uses a microservices architecture with the following components:

- **Frontend**: Next.js (T3 Stack) with TypeScript, TailwindCSS
- **Backend 1**: FastAPI Python application for core AML monitoring services
- **Backend 2**: FastAPI Python application for document/image processing services
- **Storage**: In-memory storage (data lost on restart - add persistent database as needed)
- **Infrastructure**: Docker Compose orchestration with Nginx reverse proxy

## Development Commands

### Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev          # Start development server with Turbo
npm run build        # Build for production
npm run check        # Run lint and type check
npm run lint         # ESLint
npm run lint:fix     # ESLint with auto-fix
npm run typecheck    # TypeScript type checking
npm run format:check # Prettier format check
npm run format:write # Prettier format and write
```

### Backend Services (Python FastAPI)
Both `backend_1` and `backend_2` follow the same structure:
```bash
cd backend_1  # or backend_2
python app.py  # Start FastAPI development server with uvicorn
# Or use uvicorn directly with hot-reload:
uvicorn app:create_app --factory --reload --host 0.0.0.0 --port 5000
```

### Docker Development
```bash
docker-compose up --build  # Start all services
docker-compose down        # Stop all services
```

## Service Architecture

### Frontend (Port 3000)
- Built on T3 Stack (Next.js, TypeScript, TailwindCSS)
- Environment variables for API endpoints:
  - `NEXT_PUBLIC_API_URL=/api` (backend services)
  - `NEXT_PUBLIC_LLM_API_URL=/llm-api` (LLM backend)

### Backend Services
- **backend_1**: Core AML monitoring, transaction analysis, alert system
  - API Docs: http://localhost:5000/docs (when running)
  - ReDoc: http://localhost:5000/redoc
- **backend_2**: Document processing, image analysis, compliance verification
  - API Docs: http://localhost:5000/docs (when running via LLM backend route)
  - ReDoc: http://localhost:5000/redoc
- Both use FastAPI with modular structure:
  - `routes/` - API endpoints (FastAPI routers)
  - `models/` - Pydantic data models
  - `services/` - Business logic
  - `database/` - Database connections and operations (in-memory storage)
  - `utils/` - Shared utilities

### Storage
- **In-Memory Storage**: Data stored in Python dictionaries
- Data is lost when services restart
- To add persistent storage (PostgreSQL, MySQL, etc.), modify `database/connection.py` in each backend

### Nginx Reverse Proxy (Port 80)
Routes requests to appropriate services:
- Frontend requests to port 3000
- Backend API requests to port 5000
- LLM API requests to backend_2 port 5000

## Key Features Implementation

### Part 1: Real-Time AML Monitoring
- Regulatory ingestion engine for external sources (MAS, FINMA, HKMA)
- Transaction analysis with configurable rules
- Role-specific alert system (Front/Compliance/Legal teams)
- Remediation workflow engine with audit trails

### Part 2: Document & Image Corroboration  
- Multi-format document processing (PDF, text, images)
- Format validation and content extraction
- Image authenticity verification and tampering detection
- Risk scoring and real-time feedback system

## Environment Variables

Required environment variables (create `.env` file):
```
GROQ_API_KEY=your_groq_api_key_here
```

## File Structure Notes

- Frontend follows T3 Stack conventions with `src/app/` directory structure
- Backend services use FastAPI routers for modular routing
- Docker configuration supports containerized development
- Both backends have identical FastAPI application structure for consistency
- FastAPI applications use factory pattern (`create_app()`) for better testability
- In-memory storage system mimics async database operations for easy migration to persistent storage

## Data Files

The project includes mock data for development:
- `transactions_mock_1000_for_participants.csv` - Sample transaction data for AML monitoring
- `Swiss_Home_Purchase_Agreement_Scanned_Noise_forparticipants.pdf` - Sample document for corroboration testing