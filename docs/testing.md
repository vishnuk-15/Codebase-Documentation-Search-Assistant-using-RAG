# Testing

TaskFlow API uses `pytest` with `pytest-asyncio` for async test support. Test coverage is
tracked with `coverage.py` and enforced at a minimum of 85% in CI.

## Running the test suite

```
pytest -v --cov=app --cov-report=term-missing
```

## Test database

Tests run against a separate PostgreSQL database created fresh for each test session
using `pytest` fixtures. Each test runs inside a transaction that is rolled back at the
end, so tests never leave residual data behind.

## Fixtures

- `client` — an `httpx.AsyncClient` configured against the FastAPI app for making test
  requests
- `db_session` — an isolated async SQLAlchemy session scoped to a single test
- `authenticated_user` — creates a user and returns a valid access token, useful for
  testing protected routes

## Mocking external services

Webhook delivery and email sending are mocked in tests using `unittest.mock.patch` so
tests never make real network calls. The Redis token blocklist is replaced with an
in-memory fake during the test session.

## Continuous integration

Every pull request triggers a GitHub Actions workflow that runs linting (`ruff`), type
checking (`mypy`), and the full test suite before allowing a merge.
