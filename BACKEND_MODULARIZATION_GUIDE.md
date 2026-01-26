# Backend Modularization Guide (LLM Execution Doc)

This document is designed to be **fed into an LLM** to guide a safe, staged modularization of the backend. It is written as a **senior architect teaching an SDE‑1**. The goal is **clean, minimal, consistent** refactors with **no hot fixes** and **no behavior changes**.

---

## 0) Context Snapshot (Current State)

- **Backend stack**: Flask 3 + SQLite
- **Monolith files**:
  - `backend/app.py` (routes + handlers + error handlers + logging)
  - `backend/database.py` (DB connection + init + migrations + all CRUD)
  - `backend/kapso_service.py` (WhatsApp API)
  - `backend/config.py` (config, keys)
- **Testing**:
  - `backend/test_api.py` (single file with full API tests)
  - `backend/test_employee_crud.py` (employee CRUD tests)

**Do not change behavior or response shapes.** Refactor only.

---

## 1) Global Rules for the LLM

- **No behavior changes.** Only move code and update imports.
- **No refactors inside logic** unless essential for imports.
- **No reformatting** or unrelated cleanup.
- **Keep error messages and status codes identical.**
- **Tests remain in a single file** (`backend/test_api.py`), per requirement.
- **Always run tests after each stage** and fix only regressions caused by the refactor.

---

## 2) Target Modular Structure (Minimal & Clean)

```
backend/
  app.py                    # thin entrypoint
  config.py                 # configuration
  api/
    __init__.py             # register blueprints
    employees.py            # employee routes
    projects.py             # project routes
    tasks.py                # task routes
    whatsapp.py             # outbound WhatsApp endpoints
    webhooks.py             # webhook endpoints
  db/
    __init__.py             # get_db_connection, init_database, DATABASE_PATH
    migrations.py           # seed_employees, migrate_status_values, sync_task_sequence
    employees.py            # employee CRUD
    projects.py             # project CRUD
    tasks.py                # task CRUD
  services/
    kapso_service.py        # WhatsApp API client
  utils/
    validators.py           # validate_phone + other validators
    responses.py            # standard response helpers (optional)
```

---

## 3) Stage-by-Stage Plan (Do Not Skip Order)

### Stage 0 — Baseline Safety
**Goal**: Confirm current behavior via tests.
- Run: `pytest backend/test_api.py -v`
- Capture baseline behavior (sample responses for 3 endpoints).

**Potential bugs to watch**
- Tests depend on specific error strings.
- Temporary DB path override in tests.

---

### Stage 1 — Extract DB Layer into `db/`
**Goal**: Move DB functions into `backend/db` modules with minimal changes.

**Steps**
1. Create `backend/db/__init__.py`
   - Export `DATABASE_PATH`, `get_db_connection`, `init_database`
2. Create `backend/db/migrations.py`
   - Move `seed_employees`, `migrate_status_values`, `sync_task_sequence`
3. Create `backend/db/employees.py` (move employee CRUD)
4. Create `backend/db/projects.py` (move project CRUD)
5. Create `backend/db/tasks.py` (move task CRUD)
6. Update `app.py` imports to use `db.*` modules

**Definition of Done**
- All API endpoints still work.
- Tests pass with the same DB path override behavior.

**Tests to add after Stage 1**
- Smoke test for each domain (employee, project, task) verifying DB access.

**Potential bugs**
- Missing `DATABASE_PATH` in new modules.
- Circular imports between `db/__init__.py` and `db/*`.
- Connection context manager not reused properly.

---

### Stage 2 — Extract Employees API
**Goal**: Move employee endpoints to `api/employees.py`.

**Steps**
1. Create `backend/api/employees.py` Blueprint.
2. Move all `/api/employees` routes.
3. Update DB calls to `db.employees`.
4. Register blueprint in `api/__init__.py`.

**Definition of Done**
- Employee routes return identical JSON + status codes.

**Tests to add after Stage 2**
- Employee CRUD tests remain green.
- Add route existence test for `/api/employees`.

**Potential bugs**
- Missing imports (`request`, `jsonify`).
- Route decorators not converted to Blueprint.

---

### Stage 3 — Extract Projects API
**Goal**: Move project endpoints to `api/projects.py`.

**Steps**
- Blueprint extraction, same pattern as employees.
- Ensure `project_employees` logic unchanged.

**Tests to add after Stage 3**
- Project CRUD tests.
- Edge case: partial update and empty team members.

**Potential bugs**
- Join table association broken.
- Team member assignment mapping lost.

---

### Stage 4 — Extract Tasks API
**Goal**: Move task endpoints to `api/tasks.py`.

**Steps**
- Blueprint extraction, same pattern as employees.
- Keep mapping between API fields and DB fields unchanged.

**Tests to add after Stage 4**
- Task CRUD tests.
- Update task with `whatsappSent` and `whatsappResponse`.

**Potential bugs**
- `assignedTo` vs `employee_id` mapping errors.
- Status updates not applied.

---

### Stage 5 — Extract WhatsApp + Webhooks
**Goal**: Separate outbound WhatsApp endpoints and inbound webhooks.

**Steps**
1. Create `api/whatsapp.py` for WhatsApp send endpoints.
2. Create `api/webhooks.py` for webhook handlers.
3. Move `kapso_service.py` under `services/` and update imports.

**Tests to add after Stage 5**
- Webhook request processing (mock Kapso API).
- Idempotent webhook handling (repeat event must not re-update task).

**Potential bugs**
- Mock patching path changed (e.g., `kapso_service` import path).
- Webhook returns wrong status codes.

---

### Stage 6 — App Factory Cleanup
**Goal**: Make `app.py` a thin entrypoint.

**Steps**
1. Add `create_app()` in `app.py`.
2. Register blueprints, error handlers, logging inside `create_app`.
3. Update tests to use `create_app()` if needed.

**Definition of Done**
- Same runtime behavior.
- All tests pass.

**Potential bugs**
- Double initialization of DB or handlers.
- App context issues in tests.

---

## 4) Test Strategy (Single File Only)

All tests stay in `backend/test_api.py` as requested.

Add tests **after each stage** and keep them organized by section comments.

**Required test categories**
- Employee CRUD + validation
- Project CRUD + membership
- Task CRUD + status updates
- WhatsApp + webhook (mocked)

---

## 5) Prompt Template (Use This to Instruct the LLM)

> You are a junior developer refactoring a Flask backend. Your only task is to **move code into new modules** without changing behavior. **Do not change logic or response shapes.** Follow the stage plan in `BACKEND_MODULARIZATION_GUIDE.md` exactly. After each stage, run the existing tests in `backend/test_api.py`. If any tests fail, fix only the issues caused by the refactor, not unrelated items. Keep tests in a single file.

---

## 6) Stage Checklist (Use at Every Stage)

- [ ] Move only the required functions/routes
- [ ] Update imports
- [ ] Confirm no response payload changes
- [ ] Run tests and verify
- [ ] Fix only regressions from refactor

---

## 7) Common Pitfalls

- Blueprint routes not registered correctly.
- Wrong `kapso_service` patch path in tests.
- DB path override breaks after module split.
- Field mapping regressions (`assignedTo`, `whatsappSent`, etc.)

---

## 8) Final Validation

Run full backend tests once all stages are complete:
```
pytest backend/test_api.py -v
```

If everything passes, the modularization is complete.
