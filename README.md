# AML-Veersa — Agentic AI for Real-Time AML Monitoring & Document Corroboration

> **An integrated, AI-driven Anti-Money Laundering platform** — Real-time transaction surveillance, regulatory compliance management, and automated document & image verification for Front Office, Compliance, and Legal teams.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Environment Variables](#environment-variables)
  - [Option 1 — Docker Compose (Recommended)](#option-1--docker-compose-recommended)
  - [Option 2 — Run Services Individually](#option-2--run-services-individually)
- [How to Navigate the App](#how-to-navigate-the-app)
  - [Authentication](#authentication)
  - [User Roles & Dashboards](#user-roles--dashboards)
  - [Sidebar Navigation](#sidebar-navigation)
- [How to Use the App](#how-to-use-the-app)
  - [Legal Team Workflow](#1-legal-team-workflow)
  - [Compliance Team Workflow](#2-compliance-team-workflow)
  - [Front Office Workflow](#3-front-office-team-workflow)
  - [AI Agent Chat](#4-ai-agent-chat)
- [API Reference](#api-reference)
- [Project Structure](#project-structure)
- [Deployment](#deployment)
- [Support & Contact](#support--contact)

---

## Overview

AML-Veersa implements two interconnected agentic AI solutions:

| Solution | Purpose |
|----------|---------|
| **Part 1: Real-Time AML Monitoring** | Ingest regulatory circulars, monitor transactions against configurable rules, generate role-based alerts, and maintain audit trails |
| **Part 2: Document & Image Corroboration** | Upload/process PDFs & images, detect formatting errors and tampering, perform image integrity analysis, and generate risk scores |

```
┌─────────────────────────────────────────────────────────────────┐
│  Frontend (Next.js)  —  Role-based dashboards & AI Agent chat  │
├──────────────────────────┬──────────────────────────────────────┤
│  Backend 1 (FastAPI)     │  Backend 2 (FastAPI)                 │
│  AML Monitoring, Rules,  │  Document Processing, Image          │
│  Transactions, Alerts,   │  Analysis, Tampering Detection,      │
│  Customer Graph (Neo4j)  │  OCR & Validation, Risk Scoring      │
├──────────────────────────┴──────────────────────────────────────┤
│  PostgreSQL  │  Neo4j  │  Nginx Reverse Proxy                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Architecture

The project uses a **microservices architecture** orchestrated with Docker Compose:

| Service | Technology | Port | Description |
|---------|-----------|------|-------------|
| **Frontend** | Next.js 15, TypeScript, TailwindCSS | `3000` | Role-based UI with sidebar navigation |
| **Backend 1** | Python FastAPI | `5001` | Core AML monitoring, transactions, rules engine, customer graph |
| **Backend 2** | Python FastAPI | `5002` | Document processing, image analysis, forensic analysis |
| **PostgreSQL** | PostgreSQL 14 | `5432` | Persistent storage for rules, transactions, alerts |
| **Neo4j** | Neo4j 5.13 Community | `7474` / `7687` | Customer relationship graph database |
| **Nginx** | Nginx | `80` | Reverse proxy routing requests to services |

### Request Routing (via Nginx)

| URL Path | Routes To |
|----------|-----------|
| `/` | Frontend (port 3000) |
| `/api/*` | Backend 1 (port 5001) |
| `/llm-api/*` | Backend 2 (port 5002) |

---

## Tech Stack

**Frontend:**
- Next.js 15 (T3 Stack) with TypeScript
- TailwindCSS v4 + Radix UI components
- Framer Motion for animations
- Lucide & Tabler icons

**Backend 1 (AML Monitoring):**
- Python 3.11+ with FastAPI + Uvicorn
- LangChain + LangGraph for agentic workflows
- Polars for data processing
- asyncpg for PostgreSQL, neo4j driver for graph DB
- Groq API for LLM features

**Backend 2 (Document & Image Processing):**
- Python 3.10+ with FastAPI + Uvicorn
- Docling + PyTesseract for OCR
- scikit-image + PIL for image forensics
- Google Cloud Vision API for image analysis
- Groq API for LLM-powered document analysis

---

## Getting Started

### Prerequisites

- **Docker & Docker Compose** (recommended) — or:
  - Node.js ≥ 18 and npm
  - Python ≥ 3.10 (with `uv` or `pip`)
  - PostgreSQL 14+
  - Neo4j 5.x
- A **Groq API key** (required for LLM features)

### Environment Variables

1. Copy the example env file at the project root:

   ```bash
   cp .env.example .env
   ```

2. Fill in required values:

   ```env
   # Required LLM key (Groq — free tier, tool-calling support)
   GROQ_API_KEY=your_groq_api_key_here
   GROQ_API_BASE=https://api.groq.com/openai/v1
   GROQ_MODEL=llama-3.3-70b-versatile

   # Required for Backend 2 OCR with Google Vision (API key mode)
   GOOGLE_CLOUD_VISION_ENABLED=true
   GOOGLE_VISION_API_KEY=your_google_vision_api_key_here

   # Required shared DB (local Docker or Supabase)
   DATABASE_URL=postgresql://aml:aml@localhost:5432/aml
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   POSTGRES_DB=aml
   POSTGRES_USER=aml
   POSTGRES_PASSWORD=aml
   ```

3. For the **frontend**, if running outside Docker:

   ```bash
   cp frontend/.env.example frontend/.env.local
   ```

   ```env
   NEXT_PUBLIC_API_URL=http://localhost:5001/api
   NEXT_PUBLIC_API_URL_2=http://localhost:5002/api
   ```

### Option 1 — Docker Compose (Recommended)

This starts **all services** (frontend, both backends, PostgreSQL, Neo4j, Nginx) in one command:

```bash
# Build and start everything
docker-compose up --build

# Stop all services
docker-compose down
```

Once running, access the app at **http://localhost** (port 80 via Nginx), or directly:
- Frontend: http://localhost:3000
- Backend 1 API docs: http://localhost:5001/docs
- Backend 2 API docs: http://localhost:5002/docs
- Neo4j Browser: http://localhost:7474

### Option 2 — Run Services Individually

**Frontend:**

```bash
cd frontend
npm install
npm run dev          # Starts on http://localhost:3000
```

**Backend 1:**

```bash
cd backend_1
uv sync              # or: pip install -r requirements.txt
python app.py        # Starts on http://localhost:5001
```

**Backend 2:**

```bash
cd backend_2
uv sync              # or: pip install -r requirements.txt
python app.py        # Starts on http://localhost:5002
```

> **Note:** When running individually, you must have PostgreSQL and Neo4j running separately, or the backends will fall back to in-memory storage.

---

## How to Navigate the App

### Authentication

1. **Open the app** — You'll see a landing page with the "AML" title and a **Login** button.
2. **Register a new account** — Click "Register" on the login page. You'll need to provide:
   - **Name**
   - **Email**
   - **Password**
   - **User Type** — Choose one of: `Legal`, `Compliance`, or `Front Office`
3. **Log in** — Use your registered email and password.
4. After login, you are **automatically redirected** to the dashboard matching your role.

> Authentication is handled client-side using `localStorage`. No server-side sessions are required.

### User Roles & Dashboards

Each user type sees a different dashboard tailored to their responsibilities:

| Role | Default Route | Purpose |
|------|--------------|---------|
| **Legal** | `/legal` | Manage regulatory notices, assign actions, ingest documents |
| **Compliance** | `/compliance` | Manage compliance rules, monitor transactions, review alerts, validate documents |
| **Front Office** | `/frontoffice` | View client profiles, KYC status, risk ratings, customer relationships |

### Sidebar Navigation

After logging in, the **left sidebar** provides navigation links specific to your role:

#### Legal Users
| Menu Item | Route | Description |
|-----------|-------|-------------|
| Contracts | `/legal` | View regulatory notices, action items, and their statuses |
| Ingest Documents | `/legal/ingest` | Upload regulatory PDFs for automated parsing |
| AI Agent → Chat | `/agent` | Chat with the AI agent for legal analysis |

#### Compliance Users
| Menu Item | Route | Description |
|-----------|-------|-------------|
| Rule Management | `/compliance` | View/create compliance rules from regulatory notices |
| Transactions | `/compliance/transactions` | Monitor transactions, upload CSVs, run rules |
| Alerts | `/compliance/alerts` | View alerts generated from rule execution |
| Documents | `/compliance/documents` | Upload & validate documents for compliance |
| AI Agent → Chat | `/agent` | Chat with the AI agent for compliance insights |

#### Front Office Users
| Menu Item | Route | Description |
|-----------|-------|-------------|
| Overview | `/frontoffice` | Client management dashboard with KYC overview |
| Client Verification | `/frontoffice/client-verification` | Upload & verify client KYC documents |
| AI Agent → Chat | `/agent` | Chat with the AI agent for client insights |

---

## How to Use the App

### 1. Legal Team Workflow

#### Viewing Regulatory Notices
- Navigate to `/legal` to see all regulatory notices.
- Each notice shows the **regulator**, **date received**, **category**, and **status** (pending, reviewed, action-required).
- Click a notice to see its details, assigned actions, and related information.

#### Managing Actions
- Each notice can have **action items** assigned to team members.
- Toggle action status between **Open**, **In Progress**, and **Completed** using the buttons on each action card.

#### Ingesting Documents
- Click **"Ingest Documents"** in the header or navigate to `/legal/ingest`.
- Drag-and-drop or browse to upload regulatory PDFs (supported: PDF, DOC, DOCX).
- Documents are automatically parsed and queued for review. Processing status updates in real time.

#### AI Agent
- Click the **floating "AI Agent" button** (bottom-right) on any legal page to open a slide-out chat panel for AI-assisted legal analysis.

---

### 2. Compliance Team Workflow

#### Rule Management (`/compliance`)
- View all regulatory notices with their **legal interpretations** and **priority levels**.
- Notices without rules show an **"Action Required"** indicator.
- Click **"Scan Regulatory Updates"** to trigger automated regulatory scraping (shows a multi-step loading animation).
- Select a notice → click **"Create Rule"** → fill in rule name and description → submit.
- Rules are sent to Backend 1's rules API where they are processed and stored.

#### Transaction Monitoring (`/compliance/transactions`)
- View all loaded transactions with their **status** (pending, flagged, cleared, escalated) and **risk scores**.
- **Upload transactions**: Click "Upload CSV" to upload a transaction CSV file for processing.
- **Select a transaction** to view full details including:
  - Originator & beneficiary information
  - SWIFT details and FX information
  - Customer KYC and compliance data
- **Run rules**: Select a transaction → choose a compliance rule → execute to check for violations.
- Rule execution results show triggered rules and generated alerts.

#### Alerts (`/compliance/alerts`)
- View a table of all generated alerts with **timestamp**, **alert type**, **severity**, **status**, and **message**.
- Alerts are generated automatically when transactions trigger compliance rules.

#### Document Validation (`/compliance/documents`)
- Upload documents (PDF, DOC, DOCX) for automated validation.
- Documents are processed by Backend 2 and analyzed for:
  - **Formatting issues** (spacing, fonts, indentation)
  - **Content errors** (spelling, missing sections)
  - **Risk scoring** (low, medium, high)
- View detailed **findings** with severity indicators and suggestions.
- **Download reports** in Markdown or JSON format.

---

### 3. Front Office Team Workflow

#### Client Management (`/frontoffice`)
- View all clients with their **status**, **risk rating**, **KYC status**, and **compliance score**.
- Search clients by name, email, or country.
- Select a client to view detailed information:
  - **Contact Information** — email, phone, location
  - **Compliance & Risk Profile** — risk rating, compliance score, KYC status, PEP status, EDD requirements
  - **Transaction Activity** — total transactions, volume, last transaction date
  - **Active Flags & Issues** — e.g., PEP status, high risk, KYC expired, EDD not completed
  - **Related Customers** — customers connected through shared transactions (powered by Neo4j graph database), showing relationship strength and linking transactions

#### Client Document Verification (`/frontoffice/client-verification`)
- Upload client KYC documents (passports, utility bills, bank statements).
- Supported formats: PDF, JPG, JPEG, PNG (max 10 MB).
- View **automated analysis results** including:
  - Format validation scores and checks
  - Image analysis (authenticity, AI detection, tampering detection)
  - Forensic analysis (metadata, pixel analysis, compression)
  - Risk scoring with detailed factors
- Click **"View Report"** for a comprehensive analysis summary with recommendations.

---

### 4. AI Agent Chat

Available to **all user roles** via the **AI Agent** section in the sidebar or the floating button:

- **Chat tab** (`/agent`) — Natural language conversation with the AML & Document Intelligence agent.
  - Queries are automatically routed: AML/transaction queries → Backend 1; document/image analysis queries → Backend 2.
  - Each response shows the **Thought Process** (Thought → Action → Observation chain) and **Tool Calls** log — collapsible panels below each response.
- **Prompt Editor tab** (`/agent?tab=prompts`) — Customize the system prompts used by both agents without redeployment.
  - Prompts from Backend 1 (PostgreSQL-backed, persisted) and Backend 2 (in-memory) are loaded and editable.
- **Floating chat button** — Available on all three dashboards (compliance, legal, frontoffice) for context-aware agent access.

---

## API Reference

### Backend 1 — AML Monitoring (`/api`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/users/` | POST | Register a new user |
| `/api/data/upload-transactions` | POST | Upload transaction CSV |
| `/api/data/transactions` | GET | List transactions |
| `/api/data/alerts` | GET | List alerts |
| `/api/data/run-rule/{txn_id}/{rule_id}` | GET | Execute rule on transaction |
| `/api/rules/` | GET/POST | List or create rules |
| `/api/customers/customers` | GET | List all customers |
| `/api/customers/customers/graph/relationships` | GET | Get customer relationships |
| `/api/agent` | POST | Chat with AML agent |
| `/api/prompts` | GET | List editable agent prompts |
| `/api/prompts/{name}` | PUT | Update an agent prompt |

> Full interactive docs: http://localhost:5001/docs

### Backend 2 — Document & Image Processing (`/llm-api`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/documents/upload` | POST | Upload document for analysis |
| `/api/documents/analysis` | GET | List all document analyses |
| `/api/documents/analysis/{id}` | GET/DELETE | Get or delete specific analysis |
| `/api/documents/download/{id}/{format}` | GET | Download analysis report (markdown/json) |
| `/api/documents/report/{id}` | GET | Persona report (executive/compliance/legal/audit/all) |
| `/api/images/upload` | POST | Upload image for analysis |
| `/api/images/verify/{id}` | POST | Full authenticity verification |
| `/api/agent` | POST | Chat with document agent |
| `/api/prompts` | GET | List editable agent prompts |
| `/api/prompts/{name}` | PUT | Update an agent prompt |

> Full interactive docs: http://localhost:5002/docs

---

## Project Structure

```
AML-Veersa/
├── frontend/                    # Next.js frontend application
│   ├── src/
│   │   ├── app/
│   │   │   ├── auth/            # Login & registration pages
│   │   │   │   ├── login/
│   │   │   │   └── register/
│   │   │   ├── legal/           # Legal team dashboard
│   │   │   │   └── ingest/      # Document ingestion page
│   │   │   ├── compliance/      # Compliance team dashboard
│   │   │   │   ├── transactions/  # Transaction monitoring
│   │   │   │   ├── alerts/        # Alert management
│   │   │   │   └── documents/     # Document validation
│   │   │   ├── frontoffice/     # Front office dashboard
│   │   │   │   └── client-verification/  # KYC document verification
│   │   │   └── agent/           # AI agent chat & prompt editor
│   │   ├── components/          # Reusable UI components
│   │   ├── lib/                 # Utilities (auth, etc.)
│   │   └── types/               # TypeScript type definitions
│   ├── package.json
│   └── Dockerfile
│
├── backend_1/                   # AML Monitoring backend
│   ├── app/
│   │   ├── routes/              # API endpoints
│   │   │   ├── data_routes.py     # Transaction & alert endpoints
│   │   │   ├── rules_routes.py    # Compliance rule endpoints
│   │   │   ├── customer_routes.py # Customer & graph endpoints
│   │   │   ├── user_routes.py     # User management endpoints
│   │   │   └── agent_routes.py    # AI agent chat endpoint
│   │   ├── agents/              # LangChain/LangGraph agent logic
│   │   ├── models/              # Pydantic data models
│   │   ├── services/            # Business logic
│   │   ├── database/            # PostgreSQL & Neo4j connections
│   │   └── utils/               # Shared utilities
│   ├── data/                    # Mock data files
│   ├── pyproject.toml
│   └── Dockerfile
│
├── backend_2/                   # Document & Image Processing backend
│   ├── app/
│   │   ├── routes/              # API endpoints
│   │   │   ├── document_routes.py  # Document upload & analysis
│   │   │   ├── image_routes.py     # Image upload & analysis
│   │   │   └── agent_routes.py     # AI agent chat endpoint
│   │   ├── agents/              # Document analysis agent
│   │   ├── services/            # Processing services
│   │   │   ├── process_document.py           # Document processing
│   │   │   ├── validate_document.py          # Format validation
│   │   │   ├── ai_detection_service.py       # AI image detection
│   │   │   ├── forensic_analysis_service.py  # Image forensics
│   │   │   ├── tampering_detection_service.py # Tampering checks
│   │   │   ├── reverse_search_service.py     # Reverse image search
│   │   │   └── report_generation_service.py  # Report generation
│   │   ├── models/              # Pydantic data models
│   │   ├── database/            # In-memory storage
│   │   └── utils/               # Shared utilities
│   ├── pyproject.toml
│   └── Dockerfile
│
├── nginx/                       # Nginx reverse proxy
│   ├── nginx.conf
│   └── Dockerfile
│
├── docker-compose.yml           # Full stack orchestration
├── render.yaml                  # Render.com deployment config
├── .env.example                 # Environment variable template
└── README.md                    # This file
```

---
