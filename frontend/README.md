# Frontend — AML-Veersa UI

Next.js 15 (T3 Stack) frontend for the AML-Veersa platform. Role-based dashboards for Legal, Compliance, and Front Office teams, plus an AI Agent chat hub.

## Quick Start

```bash
npm install
npm run dev     # http://localhost:3000
```

## Environment Variables

Create `frontend/.env.local` when running outside Docker:

```env
NEXT_PUBLIC_API_URL=http://localhost:5001/api
NEXT_PUBLIC_API_URL_2=http://localhost:5002/api
```

Inside Docker, Nginx provides `/api` → Backend 1 and `/llm-api` → Backend 2 routing — no `.env.local` needed.

## Pages

| Route | Role | Description |
|-------|------|-------------|
| `/` | All | Landing page |
| `/auth/login` | All | Login |
| `/auth/register` | All | Register (select role) |
| `/legal` | Legal | Regulatory notices & action items |
| `/legal/ingest` | Legal | Upload regulatory documents |
| `/compliance` | Compliance | Rule management from notices |
| `/compliance/transactions` | Compliance | Transaction monitor, CSV upload, rule execution |
| `/compliance/alerts` | Compliance | Alert table |
| `/compliance/documents` | Compliance | Document validation |
| `/frontoffice` | Front Office | Client KYC overview |
| `/frontoffice/client-verification` | Front Office | Upload & verify KYC documents |
| `/agent` | All | AI Agent Chat + Prompt Editor |

## Build

```bash
npm run build    # Production build
npm run check    # Lint + typecheck
```
