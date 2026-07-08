# Error Handling

TaskFlow API returns errors as JSON objects with a consistent shape:

```
{
  "error": {
    "code": "task_not_found",
    "message": "No task exists with the given id",
    "request_id": "a1b2c3d4"
  }
}
```

## Error codes

- `validation_error` (400) — request body failed schema validation; the response
  includes a `fields` array describing each invalid field
- `unauthorized` (401) — missing or invalid authentication token
- `forbidden` (403) — authenticated but not permitted to perform this action
- `task_not_found` (404) — the requested task id does not exist or was deleted
- `rate_limited` (429) — too many requests; see the `Retry-After` header
- `internal_error` (500) — unexpected server error; the `request_id` should be included
  when filing a bug report

## Logging

Every request is assigned a `request_id` (a UUID) that is included in both the response
and the structured logs, making it possible to trace a single request across services.
Logs are shipped to a centralized ELK stack and retained for 90 days.

## Retry guidance

Clients should retry `500` and `429` responses using exponential backoff with jitter,
starting at 500ms and capping at 30 seconds. `400`, `401`, `403`, and `404` responses
should not be retried without changing the request.
