# Authentication

TaskFlow API uses JSON Web Tokens (JWT) for authentication. Every request to a protected
endpoint must include an `Authorization` header in the form `Bearer <token>`.

## Obtaining a token

Send a POST request to `/auth/login` with a JSON body containing `email` and `password`.
On success, the response contains an `access_token` valid for 15 minutes and a
`refresh_token` valid for 30 days.

```
POST /auth/login
{
  "email": "user@example.com",
  "password": "hunter2"
}
```

## Refreshing a token

When the access token expires, call `POST /auth/refresh` with the refresh token in the
request body to receive a new access token without requiring the user to log in again.

## Revoking a token

Tokens can be revoked by calling `POST /auth/logout`. Revoked tokens are added to a
blocklist stored in Redis with a TTL matching the token's remaining lifetime, so the
blocklist never grows unbounded.

## Password requirements

Passwords must be at least 10 characters and include one number and one symbol. Passwords
are hashed with bcrypt using a work factor of 12 before being stored.

## Common errors

- `401 Unauthorized` — missing or invalid token
- `403 Forbidden` — valid token but insufficient permissions for the requested resource
- `419 Token Expired` — access token has expired; call the refresh endpoint
