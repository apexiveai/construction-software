# Architecture and infrastructure

## Application shape

ApexiveAI Construction OS uses a modular-monolith architecture:

- **Web client:** React and Vite, served as static assets by Nginx.
- **API:** FastAPI, organized into versioned endpoints, services, repositories, schemas, and domain models.
- **Database:** PostgreSQL, accessed through SQLAlchemy 2 and changed only through Alembic migrations.
- **Runtime:** Docker Compose starts the web client, API, and database. PostgreSQL data is kept in a named volume.
- **Authorization:** Organization-scoped roles grant fine-grained permissions. System administrators bootstrap an organization; organization access managers create custom roles and assign them to active members.

The API is the system boundary for business rules and authorization. The frontend must not connect directly to PostgreSQL. Module code should remain grouped by domain as the platform grows (projects, site operations, planning, estimating, cost, procurement, inventory, engineering, documents, quality/safety, finance, HR, AI/automation, and reporting).

## Local container setup

1. Copy `.env.example` to `.env` and replace the example database password and `SECRET_KEY`. For production, use a unique secret of at least 32 characters and set `APP_ENV=production` with `DEBUG=false`.
2. Start the stack with `docker compose up --build`.
3. Open the web app at `http://localhost:4173`. The API documentation is at `http://localhost:8000/docs`.
4. The API liveness endpoint is `/api/v1/health`; readiness at `/api/v1/health/ready` also checks PostgreSQL. Compose waits for PostgreSQL and API readiness before marking dependent services healthy.

Alembic migrations are applied before the API starts. PostgreSQL data persists in the `postgres_data` volume. Do not put real credentials in `.env.example` or commit a local `.env`.

## Implemented data/API slice (work in progress)

The first business-data slice is tenant-scoped project registration and daily site reporting:

- `GET /api/v1/projects` lists projects in the caller's active organizations. `limit` is capped at 200; `offset` supports pagination.
- `POST /api/v1/projects` creates a project for an organization the caller belongs to.
- `GET /api/v1/projects/{project_id}` and `PATCH /api/v1/projects/{project_id}` read and update an accessible project.
- `GET` and `POST /api/v1/projects/{project_id}/daily-reports` list or create a project's daily shift reports.
- `GET` and `POST /api/v1/projects/{project_id}/workforce` record and list workforce counts by date, shift, trade, and contractor.
- `GET` and `POST /api/v1/projects/{project_id}/equipment-usage` record equipment operation, idle time, and fuel by date and shift.
- `GET` and `POST /api/v1/projects/{project_id}/material-usage` record consumed materials with units, quantities, and work locations.
- `GET` and `POST /api/v1/organizations/{organization_id}/equipment-assets` list and register equipment assets; `PATCH /.../equipment-assets/{asset_id}` updates asset details and status.
- `POST /api/v1/organizations/{organization_id}/access/bootstrap` initializes standard roles and assigns the initial organization admin. This endpoint is restricted to system administrators.
- `GET /api/v1/organizations/{organization_id}/access/permissions` and `/access/roles` expose the permission catalog and organization roles to active members.
- `POST /api/v1/organizations/{organization_id}/access/roles` creates a custom role; `PUT /api/v1/organizations/{organization_id}/access/members/{user_id}/roles` replaces a member's role assignments. Both require `access_control.manage`.

Project and site-operation endpoints now enforce `projects.*`, `site_reports.*`, `workforce.*`, `equipment_usage.*`, or `material_usage.*` permissions. A user with active organization membership but no granted permission is denied. System administrators bypass organization permissions for active organizations. `access_control.manage` cannot be removed from the last active role holder through the role-assignment API.

Quality inspections are exposed under `/api/v1/projects/{project_id}/inspections`: `GET` lists a project's records, `POST` creates a draft with findings, `POST /{inspection_id}/submit` submits it, and `POST /{inspection_id}/decision` records an approval or rejection. Failed findings require severity and corrective action; inspections with failed findings cannot be approved. Only submitted inspections can be decided, rejection requires a reason, and the creator cannot review their own inspection. Decisions are stored with the reviewer, timestamp, and comments. Quality routes enforce `quality_inspections.read`, `.create`, `.submit`, and `.review` permissions.

The web app now uses `/api/v1/auth/login` and the projects API; access and refresh tokens remain in memory, and an expired access token is refreshed through `/auth/refresh`. The Quality Inspection page loads, creates, submits, and reviews backend records. The remaining dashboard modules are still demonstration views.

Alembic revisions `20261119_01`–`20261119_05` add project, site-operation, permission-catalog, equipment-asset, and quality inspection data. For tests, install `backend/requirements-dev.txt`, then run `python -m unittest discover -s tests -v` from `backend`. Material usage here is a site consumption log, not the inventory stock ledger. Drawing/RFI, scheduling, procurement/inventory, finance/HR, AI/RPA, GIS, and the remaining project workflows are not implemented by these endpoints.

## Delivery boundaries

The current infrastructure and business-data slice are a development foundation, not a production-complete system. Fine-grained authorization currently covers project, site-operation, equipment asset, and quality inspection APIs; other domains still need permission policies. Quality decisions retain an inspection-specific decision record, but general audit events for business mutations and frontend role management are not implemented. Production also requires managed secret storage, TLS/ingress, backup and restore procedures, monitoring, and environment-specific database operations.
