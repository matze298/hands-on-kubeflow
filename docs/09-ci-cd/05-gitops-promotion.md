# GitOps Promotion

This page represents model promotion as a Git-tracked change.

## What You Will Build

You will create:

```text
deploy/README.md
deploy/environments/local/promoted-model.yaml
deploy/environments/stackit/promoted-model.yaml
deploy/environments/generic-cloud/promoted-model.yaml
ci/promotion-schema.md
ci/render_promotion.py
.github/workflows/promote-model.yaml
```

## Why This Matters

Promotion should be reviewable.

Instead of silently deploying a model from CI, represent the promotion as a file change:

```text
model_uri changed
metrics_uri changed
lineage_uri changed
git_sha changed
image_tag changed
```

Then review it like normal code.

## Create Deployment Folders

```bash
mkdir -p deploy/environments/local
mkdir -p deploy/environments/stackit
mkdir -p deploy/environments/generic-cloud
```

## Create `deploy/README.md`

```markdown
# Deployment State

This folder stores Git-tracked deployment state for tutorial environments.

A promoted model is represented as YAML.

The CI/CD chapter uses this to demonstrate a GitOps-style promotion flow:

```text
pipeline run passes
  ↓
promotion data is rendered
  ↓
pull request updates promoted-model.yaml
  ↓
deployment controller or human applies the change
```

This is a concept chapter, not a production GitOps controller setup.
```

## Create Initial Promotion Files

Create `deploy/environments/local/promoted-model.yaml`:

```yaml
apiVersion: kubeflow-by-doing.dev/v1alpha1
kind: PromotedModel
metadata:
  name: tiny-image-classifier
  environment: local
spec:
  runId: ""
  modelUri: ""
  metricsUri: ""
  lineageUri: ""
  imageTag: ""
  gitSha: ""
  promotedAt: ""
```

Copy to other environments:

```bash
cp deploy/environments/local/promoted-model.yaml deploy/environments/stackit/promoted-model.yaml
cp deploy/environments/local/promoted-model.yaml deploy/environments/generic-cloud/promoted-model.yaml
```

Then edit `metadata.environment`.

## Create `ci/promotion-schema.md`

```markdown
# Promotion Schema

Promotion is represented by `PromotedModel`.

## Fields

- `runId`: tutorial or KFP run identifier
- `modelUri`: durable model artifact URI
- `metricsUri`: durable metrics artifact URI
- `lineageUri`: lineage JSON URI
- `imageTag`: image used to train or serve the model
- `gitSha`: source commit
- `promotedAt`: UTC timestamp

## Rule

A promotion is a Git-tracked change, not an implicit side effect.
```

## Create `ci/render_promotion.py`

```python
from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path

import yaml


def env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"missing required environment variable: {name}")
    return value


def main() -> None:
    environment = env("KBD_PROMOTION_ENV")
    output_path = Path(f"deploy/environments/{environment}/promoted-model.yaml")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    document = {
        "apiVersion": "kubeflow-by-doing.dev/v1alpha1",
        "kind": "PromotedModel",
        "metadata": {
            "name": "tiny-image-classifier",
            "environment": environment,
        },
        "spec": {
            "runId": env("KBD_RUN_ID"),
            "modelUri": env("KBD_MODEL_URI"),
            "metricsUri": env("KBD_METRICS_URI"),
            "lineageUri": env("KBD_LINEAGE_URI"),
            "imageTag": env("KBD_IMAGE_TAG"),
            "gitSha": env("KBD_GIT_SHA"),
            "promotedAt": datetime.now(timezone.utc).isoformat(),
        },
    }

    output_path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    print(f"wrote {output_path}")


if __name__ == "__main__":
    main()
```

Add dependency:

```bash
uv add pyyaml
```

## Test Locally

```bash
export KBD_PROMOTION_ENV=local
export KBD_RUN_ID=local-001
export KBD_MODEL_URI=s3://kubeflow-by-doing/runs/local-001/models/model.pt
export KBD_METRICS_URI=s3://kubeflow-by-doing/runs/local-001/metrics/metrics.json
export KBD_LINEAGE_URI=s3://kubeflow-by-doing/runs/local-001/lineage/lineage.json
export KBD_IMAGE_TAG=kubeflow-by-doing/train:local
export KBD_GIT_SHA="$(git rev-parse --short HEAD)"

uv run python ci/render_promotion.py
cat deploy/environments/local/promoted-model.yaml
```

## Create `.github/workflows/promote-model.yaml`

```yaml
name: Promote Model

on:
  workflow_dispatch:
    inputs:
      environment:
        description: "Target environment"
        type: choice
        options:
          - local
          - stackit
          - generic-cloud
        required: true
      run_id:
        description: "Run ID"
        type: string
        required: true
      model_uri:
        description: "Model URI"
        type: string
        required: true
      metrics_uri:
        description: "Metrics URI"
        type: string
        required: true
      lineage_uri:
        description: "Lineage URI"
        type: string
        required: true
      image_tag:
        description: "Image tag"
        type: string
        required: true
      git_sha:
        description: "Git SHA"
        type: string
        required: true

permissions:
  contents: write
  pull-requests: write

jobs:
  promote:
    name: Render promotion and open PR
    runs-on: ubuntu-latest

    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v5
        with:
          enable-cache: true

      - name: Set up Python
        run: uv python install 3.12

      - name: Sync dependencies
        run: uv sync --all-extras --dev

      - name: Render promotion
        env:
          KBD_PROMOTION_ENV: ${{ inputs.environment }}
          KBD_RUN_ID: ${{ inputs.run_id }}
          KBD_MODEL_URI: ${{ inputs.model_uri }}
          KBD_METRICS_URI: ${{ inputs.metrics_uri }}
          KBD_LINEAGE_URI: ${{ inputs.lineage_uri }}
          KBD_IMAGE_TAG: ${{ inputs.image_tag }}
          KBD_GIT_SHA: ${{ inputs.git_sha }}
        run: uv run python ci/render_promotion.py

      - name: Create promotion pull request
        uses: peter-evans/create-pull-request@v7
        with:
          branch: promote/${{ inputs.environment }}/${{ inputs.run_id }}
          title: "Promote model ${{ inputs.run_id }} to ${{ inputs.environment }}"
          commit-message: "Promote model ${{ inputs.run_id }} to ${{ inputs.environment }}"
          body: |
            Promotes model run `${{ inputs.run_id }}` to `${{ inputs.environment }}`.

            - Model: `${{ inputs.model_uri }}`
            - Metrics: `${{ inputs.metrics_uri }}`
            - Lineage: `${{ inputs.lineage_uri }}`
            - Image: `${{ inputs.image_tag }}`
            - Git SHA: `${{ inputs.git_sha }}`
          add-paths: |
            deploy/environments/${{ inputs.environment }}/promoted-model.yaml
```

## GitOps Controller Note

This tutorial does not require Argo CD, Flux, or another controller.

The concept is:

```text
promotion is a Git change
```

Later, a GitOps controller could reconcile:

```text
deploy/environments/<env>/promoted-model.yaml
```

into:

```text
model-server ConfigMap
InferenceService
deployment manifest
```

## Common Problems

### Workflow cannot create PR

Check permissions:

```yaml
permissions:
  contents: write
  pull-requests: write
```

Also check repository settings for GitHub Actions PR creation.

### `pyyaml` missing

Run:

```bash
uv add pyyaml
uv sync
```

### Promotion file is overwritten accidentally

That is expected if you promote a new model to the same environment.

The Git diff is the review mechanism.

## Acceptance Criteria

You are done when:

- promotion schema exists
- promotion files exist per environment
- render script exists
- local render works
- promote workflow can create a PR
- promotion is represented as a Git-tracked YAML change

## References

- [GitHub Actions workflow dispatch](https://docs.github.com/actions/using-workflows/events-that-trigger-workflows#workflow_dispatch)
- [GitHub Actions permissions](https://docs.github.com/actions/security-guides/automatic-token-authentication)
- [GitOps principles](https://opengitops.dev/)

## Next Step

Continue with [Security and Maintenance](06-security-and-maintenance.md).
