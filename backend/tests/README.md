# Backend Test Suite Organization

## ✅ Modular Test Structure (RECOMMENDED for LLM maintenance)

The test suite has been split into logical modules for better maintainability:

```
backend/tests/
├── __init__.py                 # Package marker
├── conftest.py                 # Shared fixtures (client, sample_employee, etc.)
├── test_employees.py           # Employee CRUD tests (18KB, ~50 tests)
├── test_projects.py            # Project tests (19KB, ~40 tests)
├── test_tasks.py               # Task & Kanban tests (28KB, ~60 tests)
├── test_webhooks.py            # WhatsApp webhook tests (30KB, ~35 tests)
├── test_messages.py            # Message status & tracking tests (107KB, ~70 tests)
├── test_dashboard.py           # Dashboard & attention tests (28KB, ~25 tests)
└── test_health.py              # Health check tests (1KB, ~3 tests)
```

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific module
pytest tests/test_employees.py -v
pytest tests/test_dashboard.py -v

# Run with coverage
pytest tests/ -v --cov=. --cov-report=html

# Run specific test class
pytest tests/test_employees.py::TestEmployeeCRUD -v

# Run specific test function
pytest tests/test_employees.py::TestEmployeeCRUD::test_create_employee_success -v
```

## Benefits for LLM Maintenance

1. **Faster Context Loading** - LLM only needs to read relevant 20-30KB files instead of 300KB
2. **Clearer Intent** - Filename immediately tells what's being tested
3. **Easier Parallel Updates** - Can modify employee tests without touching webhook tests
4. **Better Error Isolation** - Test failures scoped to specific modules
5. **Reduced Token Usage** - Smaller files = fewer tokens per operation

## Shared Fixtures (conftest.py)

All test modules automatically have access to:
- `client` - Flask test client with temp database
- `mock_kapso` - Mocked WhatsApp API (auto-applied globally)
- `sample_employee` - Pre-created test employee
- `sample_project` - Pre-created test project
- `sample_task` - Pre-created test task
- `get_unique_msg_id()` - Helper for generating unique message IDs

## Migration Notes

- ✅ Original `test_api.py` kept as backup
- ✅ All 245 tests migrated successfully
- ✅ Tests can run from either location
- ⚠️  Some standalone test functions (2066-3300 in old file) may need manual migration

## For Future Development

When adding new tests:
1. Identify the feature area (employees, tasks, webhooks, etc.)
2. Add tests to the appropriate `tests/test_*.py` file
3. If creating new fixtures, add them to `tests/conftest.py`
4. Run `pytest tests/<module>.py -v` to verify

## Test Count by Module

- test_employees.py: ~50 tests (Employee CRUD, validation, edge cases)
- test_projects.py: ~40 tests (Project CRUD, team assignments, descriptions)
- test_tasks.py: ~60 tests (Task CRUD, Kanban, database, integration)
- test_webhooks.py: ~35 tests (WhatsApp integration, button responses, deduplication)
- test_messages.py: ~70 tests (Message status, history, clarifications, mentions, bug fixes)
- test_dashboard.py: ~25 tests (Dashboard service, API, attention items, edge cases)
- test_health.py: ~3 tests (Health check endpoint)

**Total: 245+ tests**
