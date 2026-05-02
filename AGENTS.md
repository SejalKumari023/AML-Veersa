# AGENTS.md

Guidance for AI coding agents working in this repository.

## Project Overview

AML-Veersa implements two agentic AI-driven AML (Anti-Money Laundering) solutions:

1. **Part 1: Real-Time AML Monitoring** — Monitors regulatory changes and client transactions; detects AML risks via configurable rules; generates role-based alerts
2. **Part 2: Document & Image Corroboration** — Automates verification of KYC documents; detects tampering, AI-generated images, and OCR extraction

## Architecture

```
User → Frontend (Next.js, port 3000)
         └→ /api/orchestrate  (Next.js API route — intent routing)
               ├→ POST /api/agent      (Backend 1, port 5001) — AML monitoring agent
               └→ POST /llm-api/agent  (Backend 2, port 5002) — Document agent
```

Both backends use identical **LangGraph ReAct** structure:
```
agent_node → should_continue → tool_node | END → agent_node (loop)
```

### Service Ports
| Service | Port | Notes |
|---------|------|-------|
| Frontend | 3000 | Next.js dev or built |
| Backend 1 | 5001 | FastAPI (macOS: avoid 5000 — AirPlay) |
| Backend 2 | 5002 | FastAPI |
| PostgreSQL | 5432 | Required for Backend 1 |
| Neo4j | 7474/7687 | Optional; graceful fallback if not available |
| Nginx | 80 | Docker only — routes `/api/*` to B1, `/llm-api/*` to B2 |

## Development Commands

### Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev           # Start with Turbopack on port 3000
npm run build         # Production build
npm run check         # Lint + typecheck
```

### Backend Services (Python FastAPI)
```bash
# Backend 1
cd backend_1
python app.py         # Starts on port 5001

# Backend 2
cd backend_2
python app.py         # Starts on port 5002
```

### Docker (full stack)
```bash
docker-compose up --build   # All services
docker-compose down         # Stop all
```

## Environment Variables

Minimum required (copy `.env.example` → `.env`):
```bash
GROQ_API_KEY=your_key          # Required for all LLM features
GROQ_API_BASE=https://api.groq.com/openai/v1
GROQ_MODEL=llama-3.3-70b-versatile
```

Frontend (local dev only — not needed with Docker/Nginx):
```bash
# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:5001/api
NEXT_PUBLIC_API_URL_2=http://localhost:5002/api
```

## Key Design Decisions

### Rule Parser (`backend_1/app/agents/rule_parser.py`)
- Uses `exec()` to execute LLM-generated Python code against a restricted namespace
- Namespace contains only the `Transaction` class — no filesystem or network access
- Three-node LangGraph graph: `parse_rule → test_rule → refine_rule` (loops until all tests pass)
- All Pydantic models use `method="json_mode"` for `with_structured_output()` (required for llama-3.3-70b)
- Field aliases handle LLM field name variations (`"function"` vs `"function_code"`)

### AML Agent (`backend_1/app/agents/aml_agent.py`)
- 10 tools: search_transactions, get_transaction, get_alerts, get_risk_summary,
  get_customer_profile, get_customer_relationships, run_rules_on_transaction,
  create_rule, get_all_rules, ingest_regulatory_notice
- System prompt loaded from PostgreSQL `prompts` table (editable via `/api/prompts`)
- If all LLM responses were tool-calls with no text, a final summarization call synthesizes the response

### Document Agent (`backend_2/app/agents/doc_agent.py`)
- 10 tools wrapping document/image analysis services
- Uses LangGraph 1.1.10 — `ToolNode` added directly to graph (not wrapped)
- Tool logs and thought process extracted post-hoc from message history
- Prompts stored in-memory (`app/database/prompt_store.py`)

### Frontend Orchestration (`frontend/src/app/api/orchestrate/route.ts`)
- Intent classification by keyword matching routes to AML or document backend
- Document keywords: document, pdf, image, tamper, ocr, forensic, authenticity, verify document, upload file

## File Structure (Source Files Only)

```
AML-Veersa/
├── frontend/src/
│   ├── app/
│   │   ├── agent/          # AI Agent Hub page (Chat + Prompt Editor tabs)
│   │   ├── api/orchestrate/ # Intent routing to backends
│   │   ├── auth/           # Login / register
│   │   ├── compliance/     # Rules, transactions, alerts, documents
│   │   ├── frontoffice/    # Client overview, KYC verification
│   │   └── legal/          # Regulatory notices, document ingest
│   ├── components/
│   │   ├── agent/          # AgentChat, PromptEditor
│   │   └── ui/             # shadcn/ui + custom components
│   └── lib/auth.ts         # Client-side auth (localStorage)
│
├── backend_1/app/
│   ├── agents/             # AML ReAct agent + rule parser
│   ├── database/           # PostgreSQL + Neo4j connections
│   ├── models/             # Transaction model (60+ fields)
│   ├── routes/             # API endpoints
│   └── services/           # Rule execution business logic
│
├── backend_2/app/
│   ├── agents/             # Document ReAct agent
│   ├── database/           # In-memory storage + prompt store
│   ├── models/             # Document and image models
│   ├── routes/             # API endpoints
│   └── services/           # OCR, tampering, AI detection, forensics
│
├── nginx/                  # Reverse proxy config
├── docker-compose.yml
├── render.yaml             # Render.com deployment blueprint
└── .env.example            # Environment variable template
```

## Common Issues

| Issue | Fix |
|-------|-----|
| Port 5000 in use on macOS | macOS AirPlay uses port 5000. Always use `PORT=5001` for Backend 1. |
| "Database pool not initialized" | PostgreSQL not running. Run `brew services start postgresql@15`. |
| "The api_key client option must be set" | Missing `GROQ_API_BASE` in `.env`. |
| "This model does not support json_schema" | Use `method="json_mode"` in `with_structured_output()`. |
| Frontend API calls 404 | When running locally (not Docker), create `frontend/.env.local` with absolute `localhost` URLs. |
| Agent returns empty response | If all LLM turns used tool_calls only, a final summarization call is made automatically. |
