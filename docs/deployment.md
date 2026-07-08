# Deployment

TaskFlow API is packaged as a Docker container and deployed to a Kubernetes cluster.

## Building the image

```
docker build -t taskflow-api:latest .
```

The Dockerfile uses a multi-stage build: dependencies are installed in a `builder` stage,
then only the compiled artifacts and virtual environment are copied into a slim
`python:3.11-slim` runtime image, keeping the final image under 250MB.

## Environment variables

Required environment variables at runtime: `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`,
and `WEBHOOK_SIGNING_KEY`. These are injected via Kubernetes Secrets, never baked into
the image.

## Rolling deployments

Deployments use a rolling update strategy with `maxSurge: 1` and `maxUnavailable: 0`,
ensuring zero downtime. A readiness probe hits `/health` and must return `200` before a
pod receives traffic.

## Scaling

A Horizontal Pod Autoscaler scales between 3 and 12 replicas based on CPU utilization,
targeting 65% average CPU across pods.

## Rollbacks

If a deployment's error rate exceeds 5% within the first 5 minutes, the deployment
pipeline automatically rolls back to the previous stable image tag.
