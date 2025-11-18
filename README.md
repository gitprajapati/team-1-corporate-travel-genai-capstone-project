# Yash Travel Management Platform (Gen-AI Capstone)

AI-powered corporate travel workflow for Yash employees, managers, and HR travel desks. The system unifies traditional approval flows with LLM-assisted booking via Model Context Protocol (MCP) tools and a Milvus-backed travel policy assistant.

## Highlights
- Role-aware Vue dashboards for employees, managers, and HR operations.
- FastAPI backend with JWT auth, workflow-aware APIs, and MCP-powered HR chat.
- Retrieval augmented policy assistant grounded in Milvus vector search and Azure OpenAI.
- Frequent route bookmarking, draft handling, and detailed lifecycle tracking for each travel indent.


## Architecture Snapshot
```
[Vue 3 SPA] --REST--> [FastAPI Service] --SQL--> [Cloud PostgreSQL]
						  \--MCP--> [Airline Booking Server]
						  \--MCP--> [Hotel Booking Server]
						  \--Vector--> [Cloud Milvus]
						  \--LLM--> [Azure OpenAI]
```

## Documentation
- Business overview: `docs/BUSINESS_DOCUMENTATION.md`
- API reference: `docs/API_DOCUMENTATION.md`
- Technical deep dive: `docs/TECHNICAL_DOCUMENTATION.md`
- Configuration options: `CONFIGURATION.md`

## Getting Started

### Option A — Docker Compose
```bash
docker compose up --build
```
Compose now assumes you have provisioned cloud services (PostgreSQL, Milvus) and that their connection strings live in `.env`.

### Option B — Manual Setup
1. **Create virtual environment**
	```bash
	python3.11 -m venv .venv
	source .venv/bin/activate  # Windows: .venv\Scripts\activate
	```
2. **Install dependencies**
	```bash
	pip install -r requirements.txt
	```
3. **Configure environment**
	```bash
	cp .env.example .env  # if provided
	```
	Update at minimum: `AZURE_API_KEY`, `AZURE_API_BASE`, `AZURE_API_VERSION`, `DB_PASSWORD`, `MILVUS_TOKEN`, `SECRET_KEY`.
4. **Database preparation**
	```bash
	python scripts/init_db.py
	```
	Optional: run `scripts/create_employee_route_bookmarks.sql` against your cloud database if the feature is enabled.
5. **Run FastAPI backend**
	```bash
	uvicorn src.main:app --reload --port 8000
	```
6. **Run Vue dashboard**
	```bash
	cd frontend/vue-project
	npm install
	npm run dev
	```
	Set `VITE_API_BASE_URL` in `frontend/vue-project/.env` if the API is not on `http://127.0.0.1:8000`.
7. **Optional services**
	```bash
	
	# MCP airline + hotel tools
	python src/mcp_servers/airlines/airline_booking_server.py
	python src/mcp_servers/hotel/hotel_booking_mcp_server.py
	```

## Key Features
- **Travel indents**: employees raise requests, save drafts, or pre-fill using frequent route bookmarks.
- **Manager console**: review queues, approvals, and employee profiles.
- **HR command center**: LLM chat uses MCP airline/hotel tools to plan and confirm bookings while updating statuses.
- **Policy assistant**: retrieval augmented chat grounded in Milvus-stored policy documents.
- **Health endpoints**: `/health` and `/hr-mcp/health` expose runtime diagnostics.

### Frequent Route Bookmarks
1. Create the table (per environment):
	```bash
	psql $DATABASE_URL -f scripts/create_employee_route_bookmarks.sql
	```
2. Employee APIs (requires JWT):
	- `GET /employee/frequent-routes`
	- `POST /employee/frequent-routes`
	- `DELETE /employee/frequent-routes/{bookmark_id}`
	- `POST /employee/frequent-routes/{bookmark_id}/use`
3. Vue dashboard exposes bookmark creation, reuse, and usage analytics within the employee workflow.

## Configuration Essentials
All runtime settings are environment-driven (see `src/config/settings.py`). Key groups (point each to cloud resources):
- **Database**: `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_SSLMODE`
- **Auth**: `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`
- **LLM**: `AZURE_API_KEY`, `AZURE_API_BASE`, `AZURE_API_VERSION`, `AZURE_MODEL`, `LLM_TEMPERATURE`
- **Milvus**: `MILVUS_URI`, `MILVUS_TOKEN`, `MILVUS_COLLECTION_NAME`, `MILVUS_DIM`
- **MCP**: `MCP_AIRLINE_COMMAND`, `MCP_AIRLINE_ARGS`, `MCP_HOTEL_COMMAND`, `MCP_HOTEL_ARGS`
- **Sessions**: `SESSION_TIMEOUT_HOURS` for chat lifetimes


## Project Structure
```
Gen-AI-Capstone-Projects/
├── .env.example                  # Sample configuration scaffold
├── docs/
│   ├── BUSINESS_DOCUMENTATION.md # Stakeholders, value proposition, rollout
│   ├── API_DOCUMENTATION.md      # Endpoint reference with payloads
│   └── TECHNICAL_DOCUMENTATION.md# Architecture, components, ops guidance
├── scripts/
│   ├── init_db.py                # Bootstrap database schema/seed data
│   └── create_employee_route_bookmarks.sql
│                                # SQL helper for frequent route feature
├── src/
│   ├── main.py                   # FastAPI application entrypoint
│   ├── api/
│   │   ├── auth_router.py        # Login, registration, session endpoints
│   │   ├── employee_router.py    # Employee travel indent and policy APIs
│   │   ├── manager_router.py     # Manager approval and profile APIs
│   │   ├── hr_mcp_router.py      # HR AI chat + ticket lifecycle endpoints
│   │   ├── models/               # Pydantic request/response schemas
│   │   └── services/             # Session + travel indent service layer
│   ├── auth/                     # JWT creation, verification, revocation
│   ├── config/                   # Settings, prompts, LLM & MCP factories
│   ├── db/                       # Psycopg queries and workflow helpers
│   ├── rag/                      # Milvus store + policy RAG chat service
│   └── mcp_servers/              # Airline & hotel MCP reference servers
├── frontend/
│   └── vue-project/
│       ├── src/
│       │   ├── views/            # Employee/Manager/HR dashboards
│       │   ├── components/       # Frequent routes, cards, lists, etc.
│       │   ├── services/api.js   # Axios client with auth interception
│       │   └── stores/auth.js    # Pinia auth store (JWT persistence)
│       └── Dockerfile            # Dev container for Vite app
├── Dockerfile                    # Backend service image definition
├── docker-compose.yml            # Local orchestration (API, MCP, Milvus)
└── requirements.txt              # Python dependency lock file
```

## Testing
- Backend: add pytest suites for auth, employee flows, MCP chat, and policy RAG (tests not yet included).
- Frontend: use Vitest or Cypress for dashboard regression.
- Health checks: `curl http://127.0.0.1:8000/health` and `curl http://127.0.0.1:8000/hr-mcp/health`.

## Troubleshooting
- **401/403 responses**: verify the correct role is logged in and the JWT is valid (`/auth/me`).
- **MCP errors**: confirm airline/hotel servers are running; `/hr-mcp/health` lists available tools.
- **Milvus issues**: ensure your cloud instance is reachable and credentials match `.env`; see `src/rag/milvus_store.py`.
- **Docker build failures**: update `.env` to provide all required secrets before `docker compose up`.