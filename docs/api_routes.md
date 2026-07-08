# API Routes

All routes are prefixed with `/api/v1`. Responses are JSON. Pagination uses `limit` and
`offset` query parameters, defaulting to `limit=20`.

## Tasks

- `GET /api/v1/tasks` — list tasks, filterable by `status`, `assignee_id`, `project_id`
- `POST /api/v1/tasks` — create a task; requires `title` and `project_id`
- `GET /api/v1/tasks/{id}` — retrieve a single task
- `PATCH /api/v1/tasks/{id}` — partially update a task
- `DELETE /api/v1/tasks/{id}` — soft-deletes a task (sets `deleted_at`, does not remove
  the row)

## Projects

- `GET /api/v1/projects` — list all projects the current user is a member of
- `POST /api/v1/projects` — create a project; the creator is automatically made owner

## Webhooks

- `POST /api/v1/webhooks` — register a webhook URL to receive `task.created`,
  `task.updated`, and `task.completed` events
- Webhook payloads are signed with HMAC-SHA256 using a per-webhook secret; verify the
  `X-TaskFlow-Signature` header before trusting the payload

## Rate limiting

Each API key is limited to 600 requests per minute using a token-bucket algorithm.
Exceeding the limit returns `429 Too Many Requests` with a `Retry-After` header
indicating how many seconds to wait.
