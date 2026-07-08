# Database Setup

TaskFlow API uses PostgreSQL 15 as its primary datastore, accessed through SQLAlchemy 2.0
with async sessions via `asyncpg`.

## Connection configuration

The database URL is read from the `DATABASE_URL` environment variable in the format
`postgresql+asyncpg://user:password@host:5432/dbname`. Connection pooling is configured
with a pool size of 20 and a max overflow of 10.

## Running migrations

Migrations are managed with Alembic. To apply all pending migrations:

```
alembic upgrade head
```

To create a new migration after changing a model:

```
alembic revision --autogenerate -m "describe your change"
```

## Core tables

- `users` — account records, including hashed passwords and role
- `tasks` — the primary task entity, with `status`, `priority`, `assignee_id`, and
  `due_date` columns
- `projects` — groups tasks together; each task belongs to exactly one project
- `audit_log` — append-only table recording every mutation for compliance

## Indexing strategy

`tasks.assignee_id` and `tasks.status` are indexed together as a composite index since
the most common query pattern filters by both fields simultaneously (e.g. "show me all
open tasks assigned to me").

## Backups

Automated daily snapshots are taken at 03:00 UTC and retained for 30 days. Point-in-time
recovery is enabled, allowing restoration to any second within the retention window.
