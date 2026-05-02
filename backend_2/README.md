# Backend 2 — Document & Image Corroboration Service

FastAPI service for automated KYC document verification: OCR extraction, tampering detection, AI-generated image detection, forensic analysis, risk scoring, and the document corroboration agent.

## Quick Start

```bash
# Install dependencies (uses uv)
uv sync
# or: pip install -r requirements.txt

# Start server (default port 5002)
python app.py

# With hot-reload for development
uvicorn app:create_app --factory --reload --host 0.0.0.0 --port 5002
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `5002` | Server port |
| `GROQ_API_KEY` | — | **Required** — Groq API key |
| `GROQ_API_BASE` | `https://api.groq.com/openai/v1` | LLM API base URL |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | LLM model |
| `GOOGLE_CLOUD_VISION_ENABLED` | `true` | Enable Google Vision OCR |
| `GOOGLE_VISION_API_KEY` | — | Google Cloud Vision API key |
| `SERPAPI_API_KEY` | — | Optional — reverse image search |
| `SIGHTENGINE_API_USER` | — | Optional — AI image detection |
| `SIGHTENGINE_API_SECRET` | — | Optional — AI image detection |
| `IMGUR_CLIENT_ID` | — | Optional — for reverse search image hosting |
| `MAX_CONTENT_LENGTH` | `52428800` | Max document upload size (bytes, default 50 MB) |
| `MAX_IMAGE_SIZE` | `20971520` | Max image upload size (bytes, default 20 MB) |
| `CORS_ORIGINS` | `*` | Allowed CORS origins |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/health` | GET | Detailed health |
| `/api/documents/upload` | POST | Upload document (PDF, DOC, DOCX) |
| `/api/documents/analysis` | GET | List all document analyses |
| `/api/documents/analysis/{id}` | GET | Get document analysis |
| `/api/documents/analysis/{id}` | DELETE | Delete document |
| `/api/documents/download/{id}/{format}` | GET | Download report (markdown/json) |
| `/api/documents/report/{id}` | GET | Persona report (executive/compliance/legal/audit/all) |
| `/api/images/upload` | POST | Upload image (JPG, PNG, BMP, TIFF) |
| `/api/images/analysis` | GET | List all image analyses |
| `/api/images/analysis/{id}` | GET | Get image analysis |
| `/api/images/verify/{id}` | POST | Full authenticity verification |
| `/api/agent` | POST | Chat with document agent |
| `/api/prompts` | GET | List agent prompts |
| `/api/prompts/{name}` | PUT | Update agent prompt |

Full interactive docs: **http://localhost:5002/docs**

## Architecture

```
app/
├── __init__.py         # FastAPI app factory, CORS, router registration, prompt seeding
├── app.py              # Entry point (uvicorn)
├── config.py           # Environment-based configuration
├── agents/
│   ├── doc_agent.py    # LangGraph ReAct agent for document corroboration
│   └── doc_tools.py    # 10 @tool functions wrapping analysis services
├── database/
│   ├── connection.py   # In-memory storage (documents, images)
│   └── prompt_store.py # In-memory prompt store
├── models/             # Pydantic models for documents and images
├── routes/
│   ├── agent_routes.py    # /api/agent, /api/prompts
│   ├── document_routes.py # /api/documents/*
│   └── image_routes.py    # /api/images/*
└── services/
    ├── process_document.py           # Docling OCR + content extraction
    ├── validate_document.py          # Structure & format validation
    ├── ai_detection_service.py       # AI-generated image detection
    ├── forensic_analysis_service.py  # ELA, noise, JPEG artifact analysis
    ├── tampering_detection_service.py # Copy-move, splicing detection
    ├── reverse_search_service.py     # SerpAPI reverse image search
    └── report_generation_service.py  # Multi-persona report generation
```

## Document Analysis Features

### Document Processing (PDF/DOC/DOCX)
- **OCR**: Google Cloud Vision + Docling fallback
- **Content extraction**: Text, tables, structured sections
- **Format validation**: Missing sections, date formats, required fields
- **Risk scoring**: Low / Medium / High with contributing factors

### Image Forensics
- **Tampering detection**: Copy-move forgery, splicing, resampling, compression artifact analysis
- **AI generation detection**: Sightengine API (requires key) or heuristic fallback
- **Forensic analysis**: Error Level Analysis (ELA), noise pattern analysis, JPEG quality checks
- **Reverse image search**: SerpAPI Google reverse search (requires key) or metadata fallback

## Sample Document for Testing

The repo includes a sample scanned PDF for demo purposes:
```
backend_2/uploads/Swiss_Home_Purchase_Agreement_Scanned_Noise_forparticipants.pdf
```

Upload it via the frontend at `/frontoffice/client-verification` or directly:
```bash
curl -X POST http://localhost:5002/api/documents/upload \
  -F "file=@uploads/Swiss_Home_Purchase_Agreement_Scanned_Noise_forparticipants.pdf"
```
