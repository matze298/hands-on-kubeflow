# Local Serving

In this section, we serve a trained model locally and then inside Kubernetes.

## What You Will Build

- FastAPI model server
- containerized inference image
- Kubernetes Deployment and Service
- smoke test endpoint
- simple promotion-to-serving path

## Why This Matters

Training is only half the platform. The tutorial should show how a promoted model becomes something callable.

## Acceptance Criteria

You are done with this section when:

- the model server runs locally
- the model server runs inside Kubernetes
- a prediction request succeeds
- the served model version can be connected back to a pipeline run
