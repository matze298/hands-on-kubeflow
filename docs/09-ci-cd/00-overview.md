# CI/CD Expansion

In this expansion section, we automate builds, checks, and pipeline compilation.

The local and cloud chapters deliberately used manual commands first:

```text
uv run pytest
docker build
kubectl apply
compile pipeline
upload run
```

Chapter 9 moves the repeatable parts into CI/CD.

## What You Will Build

You will create GitHub Actions workflows for:

```text
checks
image builds
pipeline compilation
optional pipeline submission
GitOps-style model promotion
```

Target files:

```text
.github/workflows/
├── ci.yaml
├── build-images.yaml
├── compile-pipelines.yaml
├── submit-pipeline.yaml
└── promote-model.yaml

ci/
├── README.md
├── env.example
├── compile_pipeline.py
├── submit_pipeline.py
├── render_promotion.py
└── promotion-schema.md

deploy/
├── environments/
│   ├── local/
│   │   └── promoted-model.yaml
│   ├── stackit/
│   │   └── promoted-model.yaml
│   └── generic-cloud/
│       └── promoted-model.yaml
└── README.md
```

## Why This Matters

A reproducible workflow should not depend on manual laptop state.

CI/CD moves build and validation steps into repeatable automation:

```text
push / pull request
  ↓
format, lint, type check, tests
  ↓
build images
  ↓
compile pipeline YAML
  ↓
optionally submit run
  ↓
represent promotion as Git-tracked state
```

## What CI/CD Should Automate

Automate:

- Python checks
- tests
- documentation build
- Docker image build
- pipeline compilation
- artifact upload
- optional pipeline submission
- promotion manifest creation

Do not automate blindly:

- public deployment
- expensive GPU jobs
- cloud cluster creation
- production promotion

Those should remain explicit until the repository has a mature release process.

## CI/CD Philosophy

Keep the pipeline code provider-neutral.

CI/CD supplies:

```text
image tags
registry login
KFP endpoint
KFP credentials
artifact upload location
promotion target
```

The pipeline itself should not know whether CI runs against:

```text
local minikube
STACKIT SKE
generic managed Kubernetes
```

## Chapter Files

```text
docs/09-ci-cd/
├── 00-overview.md
├── 01-ci-checks.md
├── 02-build-images.md
├── 03-compile-pipelines.md
├── 04-submit-pipelines.md
├── 05-gitops-promotion.md
└── 06-security-and-maintenance.md
```

## Acceptance Criteria

You are done with Chapter 9 when:

- tests and type checks run automatically
- docs build runs automatically
- images are built in CI
- pipeline definitions are compiled in CI
- compiled pipeline artifacts are uploaded by CI
- optional pipeline submission is gated and manual
- promotion can be represented as a Git-tracked change
- secrets are kept out of the repository

## References

- [GitHub Actions workflow syntax](https://docs.github.com/actions/using-workflows/workflow-syntax-for-github-actions)
- [Docker build with GitHub Actions](https://docs.docker.com/build/ci/github-actions/)
- [Publishing Docker images with GitHub Actions](https://docs.github.com/actions/guides/publishing-docker-images)
- [Kubeflow Pipelines SDK reference](https://www.kubeflow.org/docs/components/pipelines/reference/sdk/)

## Next Step

Start with [CI Checks](01-ci-checks.md).
