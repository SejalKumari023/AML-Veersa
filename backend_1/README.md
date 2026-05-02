# Backend 1 — AML Monitoring Service

FastAPI service for real-time AML transaction monitoring, compliance rule management, alert generation, and the AML monitoring agent.

## Quick Start

```bash
# Install dependencies (uses uv)
uv sync
# or: pip install -r requirements.txt

# Start server (default port 5001)
python app.py

# With hot-reload for development
uvicorn app:create_app --factory --reload --host 0.0.0.0 --port 5001
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `5001` | Server port |
| `HOST` | `0.0.0.0` | Bind address |
| `GROQ_API_KEY` | — | **Required** — Groq API key |
| `GROQ_API_BASE` | `https://api.groq.com/openai/v1` | LLM API base URL |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | LLM model for agents |
| `POSTGRES_HOST` | `localhost` | PostgreSQL host |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |
| `POSTGRES_DB` | `aml` | Database name |
| `POSTGRES_USER` | `aml` | Database user |
| `POSTGRES_PASSWORD` | `aml` | Database password |
| `NEO4J_URI` | — | Neo4j bolt URI (optional) |
| `NEO4J_USER` | — | Neo4j username (optional) |
| `NEO4J_PASSWORD` | — | Neo4j password (optional) |
| `CORS_ORIGINS` | `*` | Allowed CORS origins |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/health` | GET | Detailed health |
| `/api/users/` | POST | Register user |
| `/api/data/transactions` | GET | List transactions |
| `/api/data/upload-transactions` | POST | Upload CSV |
| `/api/data/alerts` | GET | List alerts |
| `/api/data/analytics/risk-summary` | GET | Risk analytics |
| `/api/data/analytics/run-rules` | GET | Run all rules on all transactions |
| `/api/data/transactions/{id}/run-rules` | POST | Run rules on single transaction |
| `/api/rules/` | GET/POST | List or create rules |
| `/api/rules/{id}` | GET/PUT/DELETE | Manage a rule |
| `/api/customers/customers` | GET | List customers |
| `/api/customers/customers/{id}` | GET | Get customer profile |
| `/api/customers/customers/graph/relationships` | GET | Customer relationship graph |
| `/api/agent` | POST | Chat with AML agent |
| `/api/prompts` | GET | List agent prompts |
| `/api/prompts/{name}` | PUT | Update agent prompt |

Full interactive docs: **http://localhost:5001/docs**

## Architecture

```
app/
├── __init__.py         # FastAPI app factory, middleware, router registration
├── app.py              # Entry point (uvicorn)
├── config.py           # Environment-based configuration
├── agents/
│   ├── aml_agent.py    # LangGraph ReAct agent (agent_node → tools → agent_node)
│   ├── aml_tools.py    # 10 @tool functions wrapping DB/service logic
│   └── rule_parser.py  # Rule text → Python function pipeline (parse→test→refine)
├── database/
│   ├── connection.py   # PostgreSQL (asyncpg) — transactions, rules, alerts, prompts
│   └── neo4j_connection.py  # Neo4j graph — customer relationships
├── models/
│   └── transaction.py  # Pydantic Transaction model (60+ fields)
├── routes/
│   ├── agent_routes.py    # /api/agent, /api/prompts
│   ├── data_routes.py     # /api/data/*
│   ├── rules_routes.py    # /api/rules/*
│   ├── customer_routes.py # /api/customers/*
│   └── user_routes.py     # /api/users/*
└── services/           # Business logic (rule execution, transaction processing)
```

## Creating a Rule (Example)

```bash
curl -X POST http://localhost:5001/api/rules/ \
  -H "Content-Type: application/json" \
  -d '{
    "rule": "Flag transactions over 10000 USD from high-risk jurisdictions",
    "rule_id": "RULE-001"
  }'
```

The rule goes through a **3-stage LangGraph pipeline**:
1. **Parse** — LLM converts rule text to a Python `apply_rule(transaction) -> bool` function
2. **Test** — LLM generates 10 test transactions; the function is executed against each
3. **Refine** — If tests fail, LLM refines the code and re-tests until all pass

## Ingesting a Regulatory Notice

```bash
curl -X POST http://localhost:5001/api/agent \
  -H "Content-Type: application/json" \
  -d '{"message": "Ingest this notice: All cash transactions above S$5000 must be flagged for review.", "conversation_history": []}'
```

## Security Notes

- The rule parser uses `exec()` to execute LLM-generated Python code. This is sandboxed to a restricted namespace but is an intentional design choice for the hackathon. In production, consider using a sandboxed execution environment.
- All LLM interactions use a read-only `Transaction` model — the generated function cannot modify database state.
