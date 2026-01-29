# Feature Implementation Plan: Rich Task Communication (WhatsApp + Form + Activity Feed)

Last updated: 2026-01-27

Overview
--------
This document describes a phased, stage-by-stage plan to implement "Rich Task Communication" for the WhatsApp Task Manager application. The goal is a mobile-first, robust system that lets employees respond to EOD task checks with text, photos, documents, videos, or use a browser form for larger uploads, while providing admins a Jira-style activity feed on each task. The implementation is broken into phases and atomic stages. Each stage includes acceptance criteria and test cases that must pass before moving forward.

Constraints & Principles
------------------------
- Mobile-first UX: every UI change must be optimized for small screens first.
- No shortcuts: changes must be minimal, well-tested, and maintainable.
- Test-driven incremental development: after every stage, automated tests are added/updated and must pass.
- Start with a lightweight core (Phase 1) and add reliability/UX improvements in later phases.
- Polling + toast already exist; WebSocket/real-time will be added in Phase 3.
- No audio transcription or typing indicators.

High-level Phases
-----------------
- Phase 1 (Core MVP): attachments + activity feed + form URL + WhatsApp reply threading basics.
- Phase 2 (Reliability & UX): @mentions -> WhatsApp, bot clarification for ambiguous replies, duplicate prevention improvements, polling refinements.
- Phase 3 (Polish & Realtime): file preview, unread badges, WebSocket real-time updates, canned responses, read receipts.

Phase 1 — Core MVP (safe, minimal, tested)
------------------------------------------
Summary: Implement activity feed, form-submission flow, and reply-thread handling to link WhatsApp replies to tasks. Keep the implementation minimal and strictly tested.

Stages (Phase 1):

Stage 1.1 — DB schema additions (atomic)
- Goal: Add tables to store activities, attachments, and submission tokens.
- Changes:
  - Create `task_activities` (activity log entries).
  - Create `task_activity_attachments` (attachments linked to an activity).
  - Create `task_submission_tokens` (token for form URLs).
- SQL (SQLite):

```sql
CREATE TABLE IF NOT EXISTS task_submission_tokens (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  task_id TEXT NOT NULL,
  employee_id INTEGER NOT NULL,
  token TEXT NOT NULL UNIQUE,
  status TEXT NOT NULL DEFAULT 'pending',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  expires_at DATETIME
);

CREATE TABLE IF NOT EXISTS task_activities (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  task_id TEXT NOT NULL,
  author_type TEXT NOT NULL, -- 'employee' | 'admin' | 'system'
  author_id INTEGER,
  author_name TEXT,
  activity_type TEXT NOT NULL, -- 'comment'|'attachment'|'status_change'|'mention'|'system'
  source TEXT NOT NULL, -- 'whatsapp_reply'|'form_submission'|'web_dashboard'|'system'
  message TEXT,
  mentioned_user_id INTEGER,
  whatsapp_message_id TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS task_activity_attachments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  activity_id INTEGER NOT NULL,
  task_id TEXT NOT NULL,
  media_type TEXT NOT NULL, -- 'image'|'video'|'document'|'audio'
  file_path TEXT NOT NULL,
  filename TEXT,
  content_type TEXT,
  file_size INTEGER,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(activity_id) REFERENCES task_activities(id)
);
```

- Acceptance criteria:
  - DB schema can be created via `db.init_database()` or migrations.
  - New tables appear and are usable in tests.
- Tests:
  - DB initialization test ensures tables exist.
  - Insert/select a mock activity and attachment.

Stage 1.2 — Backend: submission token service and endpoints (atomic)
- Goal: Generate one-time (or time-limited) submission tokens and expose two endpoints:
  - `GET /api/submissions/<token>` — Get task & token metadata (for form client)
  - `POST /api/submissions/<token>` — Submit form payload + files
  - `POST /api/submissions/<token>/upload` — (optional) upload individual files (multipart)

- Implementation notes:
  - Add a `services/submission_service.py` with `create_submission_token(task_id, employee_id)` and `get_submission_by_token(token)`.
  - Token generation: use `secrets.token_urlsafe(16)`; store created_at and expiry.
  - For files: accept multipart uploads; store files under `backend/uploads/<task_id>/<token>/` and write path to DB.
  - Enforce file size and type validation.

- Acceptance criteria:
  - Requesting a valid token returns task summary + employee name.
  - POSTing valid form data stores activity + attachments and sets token `status='submitted'`.

- Tests:
  - Unit tests for token creation and retrieval.
  - Integration tests for `GET /api/submissions/<token>` and `POST /api/submissions/<token>` mocking file uploads.

Stage 1.3 — Backend: webhook reply threading handling (atomic)
- Goal: When Kapso webhook arrives for a WhatsApp reply with `context.id` referencing a sent message, link that reply to the correct task by mapping original `whatsapp_message_id` → `task_id`.

- Implementation notes:
  - When sending an interactive message (EOD check), save a `task_messages` record tying `task_id` → `whatsapp_message_id`.
  - In `webhooks.py`, when `payload['message']` has `context.id`, look up `task_messages` to find `task_id`.
  - Create a `task_activities` record with `source='whatsapp_reply'` and `whatsapp_message_id=context.id`.
  - For media messages, download the media URL (`kapso.media_url`), store temporarily, write file to `uploads/` and create attachment records.
  - If no `context.id` (no reply threading), create a fallback activity of source `whatsapp_reply_unlinked` and set a system flag for admin review.
  - Implement Bot Clarification (simple flow): if webhook contains media but no `context.id`, send a short WhatsApp message asking "I see a file — which task is this for? Reply with the task code or click this link: <form_url>". That behavior is implemented conservatively.

- Acceptance criteria:
  - Replies with `context.id` become activities attached to the correct task.
  - Media replies get downloaded and stored; attachments associated with the activity.
  - Unthreaded replies generate a `task_activity` with `source='whatsapp_reply_unlinked'` and the system triggers an optional clarification message.

- Tests:
  - Unit tests for webhook parsing and mapping to `task_messages`.
  - Integration test: simulate Kapso webhook payloads for text, image, document types and verify DB entries and files created (use mocking for external download).

Stage 1.4 — Frontend: Activity feed in `TaskModal` (atomic)
- Goal: Add a mobile-first activity feed to the existing `TaskModal` so admins can view comments, attachments, status changes. Feed shows newest-first.

- Implementation notes:
  - New React component `src/components/tasks/ActivityFeed.jsx` with subcomponents `ActivityItem`, `AttachmentList`.
  - `TaskModal` should call `GET /api/tasks/:taskId/activities` when opened (and on poll refresh).
  - Comment box component `CommentBox` that allows admin to type, attach files (optional), and `@mention` users (autocomplete over `employees`).
  - When admin posts a comment with `@user`, backend will create `task_activity` and send a WhatsApp message to that user (Phase 2 will refine behavior). Initially we will store `mention` activities and mark `whatsapp_sent=False`.

- Acceptance criteria:
  - Activity feed displays activities sorted descending (newest first).
  - Attachments show filename and a link to download (small preview optional later).
  - Admin can post comments; comments appear immediately (optimistic UI) and are saved to backend.

- Tests:
  - Unit test for `ActivityFeed` rendering (Vitest/React Testing Library): render with mock activities, verify order and attachment rendering.
  - Integration test: open `TaskModal`, post a comment, assert API call and feed update.

Stage 1.5 — Frontend: Submission Form page (atomic)
- Goal: Add `src/pages/TaskSubmission.jsx` reachable at `/submit/:token` to accept status, notes, and multiple file uploads.

- Implementation notes:
  - Mobile-first responsive page optimized for uploads.
  - `GET /api/submissions/:token` fetches task info; submit via `POST /api/submissions/:token`.
  - Support chunked/resumable uploads later; starter will do single-request multi-file uploads (multipart/form-data). Validate file sizes client-side.

- Acceptance criteria:
  - Employee opens link from WhatsApp, sees task details, uploads files, and receives a confirmation message in WhatsApp (backend will send confirmation text back to employee).

- Tests:
  - Frontend E2E test (playwright or Cypress optional) or unit test for upload functionality mocking network.
  - Backend integration tests as in Stage 1.2.

Stage 1.6 — Tests, Acceptance, and Rollout (atomic)
- Goal: Add test cases for all above stages and only proceed if all tests pass.

- Implementation notes:
  - Update `backend/test_api.py` to include tests for token endpoints, webhook parsing, activity inserts, and file handling (mock network calls to Kapso and file download).
  - Update frontend unit tests under `src/__tests__` or existing test suites to cover `ActivityFeed` and `TaskSubmission` behaviors.
  - Run tests locally; ensure `pytest` backend and `npm test` frontend pass.

- Acceptance criteria:
  - All new tests pass.
  - Manual verification checklist passed in staging environment.

Phase 1 Deliverables
--------------------
- DB migrations / SQL statements
- `services/submission_service.py` (token generation)
- `api/submissions.py` routes
- `api/webhooks.py` updated behavior for reply threading + file handling
- `src/pages/TaskSubmission.jsx` (form)
- `src/components/tasks/ActivityFeed.jsx` and `CommentBox.jsx`
- Tests updated/added in `backend/test_api.py` and frontend tests

Potential Issues & Mitigations (Phase 1)
---------------------------------------
- Media URL expiry: Kapso media URLs expire quickly. Always download immediately during webhook processing. Use a background job or immediate synchronous download.
- Large files: For large files, recommend form upload over WhatsApp. Enforce limits and provide clear messaging.
- Reply without context: Implement a Bot Clarification (ask which task or present form links). Store unlinked replies in a review queue.
- Duplicate clicks: Webhook handler already checks existing `whatsapp_response`; extend to prevent duplicate attachments by deduplicating by file hash or media ID.
- Concurrency: Use DB transactions and `get_db_connection()` context to ensure integrity. Consider locking logic if future race conditions arise.

Chronology / Event flows (examples)
-----------------------------------
1) Normal threaded reply (best case):
  - System sends EOD interactive message -> Kapso returns `whatsapp_message_id` on success -> store mapping `task_messages(task_id, whatsapp_message_id)`.
  - Employee replies to that message with image: webhook contains `context.id=whatsapp_message_id` -> handler maps to `task_id`, downloads media, creates `task_activity` and `task_activity_attachments`.
  - Admin sees activity in feed (newest-first).

2) Unthreaded media reply (no context):
  - Employee sends photo not replying to specific message -> webhook has no `context.id` -> create `task_activity` with `source='whatsapp_reply_unlinked'` and store media.
  - Send Bot Clarification to employee asking to pick a task or open the form; admin will see unlinked items in a review queue.

API Contracts & Examples
------------------------
- `GET /api/submissions/:token` → 200 `{ success: true, data: { task: { id, title, description }, employee: {...}, existing_attachments: [...] }}`
- `POST /api/submissions/:token` (multipart form): formData fields: `status`, `notes`, `files[]` → returns `{ success: true }`
- Webhook sample (Kapso):
```json
{
  "message": {
    "type": "image",
    "from": "919876543210",
    "image": {"id": "mmg-id", "caption": "here"},
    "context": {"id": "whatsapp_message_id"},
    "kapso": { "media_url": "https://media.kapso.ai/xxx", "media_data": {"filename":"IMG.jpg","content_type":"image/jpeg"} }
  }
}
```

Testing Plan (detailed)
-----------------------
- Backend tests (pytest): Add tests in `backend/test_api.py` for:
  - `test_db_schema_created`
  - `test_create_submission_token_and_retrieve`
  - `test_submission_post_stores_activity_and_attachments` (mock file upload)
  - `test_webhook_threaded_reply_creates_activity` (mock Kapso payload)
  - `test_webhook_unthreaded_reply_creates_unlinked_activity_and_clarification_sent` (mock kapso_service send_text)

- Frontend tests (Vitest/RTL):
  - `ActivityFeed` renders activities properly (newest-first)
  - `CommentBox` posts comment and calls API
  - `TaskSubmission` form uploads files and submits

- Manual verification checklist for each stage (see Stage 1.6 Acceptance criteria).

Migration & Rollback
--------------------
- Migration: Add an idempotent script `backend/db/migrations/20260127_add_activity_tables.sql` that runs the above `CREATE TABLE IF NOT EXISTS` statements.
- Rollback: Provide `DROP TABLE IF EXISTS` statements only for dev/staging. For production, prefer leaving tables and migrating data carefully.

Operational Notes
-----------------
- File storage path: `backend/uploads/<task_id>/<activity_id>/`.
- Ensure `uploads/` is writable and included in `.gitignore`.
- Consider a future move to object storage (S3) with signed URLs.
- Ensure HTTPS for all external URLs and form pages.

Stage Exit Criteria & How to Proceed
-----------------------------------
- Each stage must pass automated tests added at the same time.
- Manual acceptance: basic integration flows work in staging.
- After Stage 1.6 passes, move to Phase 2 design/implementation.

Phase 2 & 3 (high level)
-------------------------
Phase 2: implement @mentions that send WhatsApp messages, improved duplicate prevention, bot clarification flows, and admin-to-employee message threading. Add read/delivery status processing.

Phase 3: add file previews, unread badge, WebSocket-based realtime updates, canned replies, and other UX polish.

Appendix: Developer Checklist (for each stage)
----------------------------------------------
1. Write schema + migration file.
2. Implement backend service functions & endpoints.
3. Add/modify tests; run `pytest` and ensure green.
4. Implement frontend UI components, run `npm test` and unit tests.
5. Manual smoke test in staging: end-to-end flow (send message → reply → activity appears).
6. Code review & linting.
7. Merge and deploy to staging.

How I will help next
--------------------
I can now:
- Implement Stage 1.1 SQL and add migration file.
- Implement Stage 1.2 backend endpoints scaffolding and tests.
- Implement Stage 1.3 webhook updates and tests.
- Implement Stage 1.4 frontend components and tests.

Tell me which stage I should implement first (I recommend Stage 1.1 → Stage 1.2). If you approve, I'll start implementing Stage 1.1 and update the todo list accordingly.
