# Submit Pipelines

This page adds an optional, manually triggered pipeline submission workflow.

## What You Will Build

You will create:

```text
ci/submit_pipeline.py
.github/workflows/submit-pipeline.yaml
```

The workflow is manual by default.

## Why This Matters

Submitting a pipeline run from CI is powerful but potentially expensive.

It may trigger:

- cloud compute
- GPU jobs
- object storage writes
- model deployment

So this tutorial makes pipeline submission explicit and gated.

## Create `ci/submit_pipeline.py`

```python
from __future__ import annotations

import os
from pathlib import Path

from kfp import Client


def env(name: str, default: str | None = None) -> str:
    value = os.environ.get(name, default)
    if value is None:
        raise RuntimeError(f"missing required environment variable: {name}")
    return value


def main() -> None:
    pipeline_path = Path(env("KBD_PIPELINE_PATH", "compiled/image_classification_pipeline.yaml"))
    if not pipeline_path.exists():
        raise FileNotFoundError(pipeline_path)

    client = Client(host=env("KFP_ENDPOINT"))

    arguments = {
        "run_id": env("KBD_RUN_ID"),
        "accelerator": env("KBD_ACCELERATOR", "cpu"),
        "gpu_count": int(env("KBD_GPU_COUNT", "0")),
        "cpu_image": env("KBD_TRAIN_IMAGE"),
        "gpu_image": env("KBD_GPU_TRAIN_IMAGE", env("KBD_TRAIN_IMAGE")),
        "min_accuracy": float(env("KBD_MIN_ACCURACY", "0.5")),
        "dataset_uri": env("KBD_DATASET_URI", "synthetic://tiny-image-classification"),
        "git_sha": env("GITHUB_SHA", "unknown")[:7],
        "image_tag": env("KBD_TRAIN_IMAGE"),
        "deploy_after_promotion": env("KBD_DEPLOY_AFTER_PROMOTION", "false").lower() == "true",
    }

    run = client.create_run_from_pipeline_package(
        pipeline_file=str(pipeline_path),
        arguments=arguments,
        run_name=f"kbd-{arguments['run_id']}",
    )

    print(f"submitted run_id={run.run_id}")


if __name__ == "__main__":
    main()
```

## Create `.github/workflows/submit-pipeline.yaml`

```yaml
name: Submit Pipeline

on:
  workflow_dispatch:
    inputs:
      run_id:
        description: "Tutorial run ID"
        type: string
        required: true
      accelerator:
        description: "cpu or gpu"
        type: choice
        options:
          - cpu
          - gpu
        default: cpu
      gpu_count:
        description: "Number of GPUs"
        type: string
        default: "0"
      min_accuracy:
        description: "Minimum accuracy for promotion"
        type: string
        default: "0.5"
      deploy_after_promotion:
        description: "Deploy model after promotion"
        type: boolean
        default: false

permissions:
  contents: read

jobs:
  submit:
    name: Compile and submit KFP run
    runs-on: ubuntu-latest
    environment: kfp-dev

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

      - name: Compile pipeline
        run: uv run python ci/compile_pipeline.py

      - name: Submit pipeline
        env:
          KFP_ENDPOINT: ${{ secrets.KFP_ENDPOINT }}
          KBD_RUN_ID: ${{ inputs.run_id }}
          KBD_ACCELERATOR: ${{ inputs.accelerator }}
          KBD_GPU_COUNT: ${{ inputs.gpu_count }}
          KBD_MIN_ACCURACY: ${{ inputs.min_accuracy }}
          KBD_DEPLOY_AFTER_PROMOTION: ${{ inputs.deploy_after_promotion }}
          KBD_TRAIN_IMAGE: ${{ vars.KBD_TRAIN_IMAGE }}
          KBD_GPU_TRAIN_IMAGE: ${{ vars.KBD_GPU_TRAIN_IMAGE }}
        run: uv run python ci/submit_pipeline.py
```

## Required Repository Settings

Use GitHub environment `kfp-dev`.

Configure:

Secrets:

```text
KFP_ENDPOINT
```

Variables:

```text
KBD_TRAIN_IMAGE
KBD_GPU_TRAIN_IMAGE
```

If your KFP endpoint requires auth, extend `submit_pipeline.py` with the required authentication mechanism.

## Gating Rules

Keep this workflow manual:

```yaml
workflow_dispatch:
```

Use GitHub environment approvals for cloud or GPU environments.

Recommended environments:

```text
kfp-local
kfp-stackit
kfp-cloud
kfp-gpu
```

## Network Reality Check

GitHub-hosted runners cannot reach a private KFP API unless it is exposed or connected through a tunnel/VPN/self-hosted runner.

Options:

```text
self-hosted runner inside network
temporary secured endpoint
manual local submission
CI only compiles, human submits
```

For a tutorial, it is acceptable for CI to compile and for local/manual submission to remain the default.

## Common Problems

### CI cannot reach KFP endpoint

Use a self-hosted runner or keep submission local.

Do not expose KFP publicly without authentication and network controls.

### Missing image variables

Set repository or environment variables:

```text
KBD_TRAIN_IMAGE
KBD_GPU_TRAIN_IMAGE
```

### Pipeline submits but pods fail

CI submission only starts the run. Runtime failures still require KFP and Kubernetes debugging.

## Acceptance Criteria

You are done when:

- submit script exists
- submit workflow exists
- submission is manual
- pipeline compilation runs before submission
- image names are supplied by environment variables
- private KFP networking constraints are documented

## References

- [Kubeflow Pipelines run a pipeline](https://www.kubeflow.org/docs/components/pipelines/user-guides/core-functions/run-a-pipeline/)
- [GitHub Actions environments](https://docs.github.com/actions/deployment/targeting-different-environments/using-environments-for-deployment)
- [GitHub Actions secrets](https://docs.github.com/actions/security-guides/using-secrets-in-github-actions)

## Next Step

Continue with [GitOps Promotion](05-gitops-promotion.md).
