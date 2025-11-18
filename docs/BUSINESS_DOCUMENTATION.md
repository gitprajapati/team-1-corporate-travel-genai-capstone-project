# Yash Travel Management Platform – Business Documentation

## Executive Summary
The Yash Travel Management Platform digitises and automates the end-to-end employee travel workflow. It covers travel indent creation, approval routing, bookings, and policy support under a single experience for employees, managers, and HR travel desk teams. Large language models (LLMs) and Model Context Protocol (MCP) tools augment the travel desk with AI-assisted booking and policy retrieval, reducing manual effort while enforcing corporate compliance.

## Strategic Objectives
- Streamline how Yash employees raise and track travel requests, eliminating ad hoc email chains.
- Equip managers with real-time visibility to approve, reject, or request changes with full context.
- Give HR and the travel desk a unified command centre with AI-backed booking automations.
- Increase travel policy adherence by surfacing the correct guidance at request time.
- Improve employee experience with quicker turnaround times and self-service insights.

## Stakeholders and Personas
- **Traveling employees**: submit indents, reuse frequent routes, consult the policy assistant.
- **People managers**: review pending requests, drill into employee history, approve or reject.
- **HR travel desk**: completes bookings, uses AI chat with MCP airline/hotel tooling, updates ticket status.
- **Finance and compliance**: benefit from structured audit trails and policy-aligned actions.
- **IT operations**: deploys and maintains the FastAPI backend, Vue front-end, and supporting services.

## Value Proposition
- **Cycle time reduction**: automated routing and dashboards collapse request-to-booking turnaround.
- **Policy compliance**: embedded RAG policy assistant ensures guidance is grounded in approved documents.
- **Operational efficiency**: AI-driven tool execution (flight and hotel MCP servers) handles repetitive tasks.
- **Data visibility**: centralised status tracking and reporting unlock better spend governance.
- **Employee satisfaction**: quick draft saving, bookmark reuse, and transparent status lanes remove friction.

## Key Capabilities
- Role-aware Vue dashboard covering employee, manager, and HR experiences.
- FastAPI services with JWT authentication, status-aware workflow APIs, and health endpoints.
- LLM-powered HR assistant that orchestrates MCP airline and hotel booking servers.
- Milvus-backed retrieval augmented generation (RAG) policy chat for employees.
- Frequent route bookmarking, draft handling, and detailed ticket history for employees.
- Manager profile lookups, consolidated pending queues, and streamlined approvals.
- HR ticket lifecycle management with automated status updates and tool telemetry.

## Process Overview
1. Employee logs in, raises a travel indent (or saves a draft), optionally consulting the policy assistant.
2. Submitted requests automatically appear in the manager lane for approval or rejection.
3. Approved requests transition to the HR lane; HR staff use the AI chat to execute bookings via MCP tools.
4. Final booking confirmations and status updates cascade back into the employee dashboard.
5. All actors can review history, metrics, and health endpoints for operational oversight.

## Success Metrics
- Average request-to-approval time (employee to manager).
- Average approval-to-booking time (manager to HR completion).
- Policy assistant usage rates and unanswered query percentage.
- Reduction in duplicate or non-compliant travel requests.
- User satisfaction (internal CSAT) for employees and HR teams.

## Risks and Mitigations
- **LLM or MCP downtime**: monitor `/health` endpoints; fall back to manual booking flow if tools unavailable.
- **Data accuracy**: enforce validation in form submissions and duplicate route guards via backend checks.
- **Adoption resistance**: provide phased rollout, training modules, and quick-reference guides.
- **Security**: rely on JWT authentication, enforce HTTPS in production, and rotate API keys regularly.
- **Regulatory changes**: keep policy corpus in Milvus current; schedule periodic ingestion jobs.

## Change Management and Rollout Plan
- Pilot with a subset of business units, collecting feedback on workflow friction and policy clarity.
- Train HR desk users on AI chat usage, including interpreting tool outputs.
- Provide managers with short videos on approval features and notifications.
- Launch company-wide with support channels and a targeted communication plan.

## Future Enhancements
- Expense claim integration and automated reconciliation with finance systems.
- Mobile-responsive micro-frontend for on-the-go approvals.
- Deeper analytics covering travel spend by department, grade, and route.
- Integration with corporate calendar and SSO for seamless authentication.
- Automated post-trip feedback loops informing vendor negotiations.
