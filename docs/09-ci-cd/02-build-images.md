# Build Images

This page adds CI image builds.

## What You Will Build

You will create:

```text
.github/workflows/build-images.yaml
ci/env.example
```

The workflow builds and optionally pushes:

```text
training image
serving image
optional GPU training image
```

## Why This Matters

A Kubeflow pipeline cannot depend on local Docker image state.

The cluster needs images available from a registry:

```text
CI builds image
  ↓
CI pushes image
  ↓
KFP task pulls image
```

## Create `ci/env.example`

```bash
# Registry image names used by CI/CD and cloud chapters.
export KBD_REGISTRY="ghcr.io/<owner>/<repo>"
export KBD_TRAIN_IMAGE="$KBD_REGISTRY/kubeflow-by-doing-train"
export KBD_SERVE_IMAGE="$KBD_REGISTRY/kubeflow-by-doing-serve"
export KBD_GPU_TRAIN_IMAGE="$KBD_REGISTRY/kubeflow-by-doing-train-gpu"
```

## Image Tag Strategy

Use at least two tags:

```text
sha-<short-sha>
latest for main branch only
```

For example:

```text
ghcr.io/org/repo/kubeflow-by-doing-train:sha-a1b2c3d
ghcr.io/org/repo/kubeflow-by-doing-train:latest
```

Do not use `latest` as the only reproducibility tag.

## Create `.github/workflows/build-images.yaml`

```yaml
name: Build Images

on:
  push:
    branches:
      - main
  pull_request:
  workflow_dispatch:
    inputs:
      push_images:
        description: "Push images to registry"
        type: boolean
        default: false

permissions:
  contents: read
  packages: write

env:
  REGISTRY: ghcr.io
  IMAGE_NAMESPACE: ${{ github.repository }}

jobs:
  build:
    name: Build container images
    runs-on: ubuntu-latest

    strategy:
      fail-fast: false
      matrix:
        include:
          - name: train
            dockerfile: Dockerfile
            image_suffix: kubeflow-by-doing-train
          - name: serve
            dockerfile: Dockerfile.serve
            image_suffix: kubeflow-by-doing-serve
          - name: train-gpu
            dockerfile: Dockerfile.gpu
            image_suffix: kubeflow-by-doing-train-gpu

    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Set image metadata
        id: meta
        run: |
          short_sha="${GITHUB_SHA::7}"
          image="${REGISTRY}/${IMAGE_NAMESPACE}/${{ matrix.image_suffix }}"
          echo "short_sha=${short_sha}" >> "$GITHUB_OUTPUT"
          echo "image=${image}" >> "$GITHUB_OUTPUT"

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to registry
        if: github.event_name == 'push' || inputs.push_images == true
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build image
        uses: docker/build-push-action@v6
        with:
          context: .
          file: ${{ matrix.dockerfile }}
          push: ${{ github.event_name == 'push' || inputs.push_images == true }}
          tags: |
            ${{ steps.meta.outputs.image }}:sha-${{ steps.meta.outputs.short_sha }}
            ${{ steps.meta.outputs.image }}:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

## Notes on Pull Requests

For pull requests, this workflow builds images but does not push by default.

This avoids publishing untrusted or experimental images.

## Notes on GPU Images

The GPU image can be large and slow to build.

If that becomes too expensive, split GPU image builds into a separate manual workflow:

```text
workflow_dispatch only
```

## Provider Registries

For non-GHCR registries, change:

```yaml
REGISTRY: ghcr.io
```

and use provider-specific login credentials.

Examples:

```text
AWS ECR
Azure ACR
Google Artifact Registry
STACKIT Container Registry
generic OCI registry
```

Keep the image names as pipeline parameters.

## Common Problems

### `packages: write` permission missing

GitHub Container Registry pushes require package write permission.

### Dockerfile missing

If the chapter has not created `Dockerfile.gpu`, remove the GPU matrix entry or make it conditional.

### Pull request from fork cannot push

That is expected. Do not push images from untrusted forks.

## Acceptance Criteria

You are done when:

- image build workflow exists
- training image builds in CI
- serving image builds in CI
- GPU image build is included or explicitly made manual
- images are tagged with commit SHA
- images are pushed only on trusted events

## References

- [Docker GitHub Actions documentation](https://docs.docker.com/build/ci/github-actions/)
- [Docker build-push-action](https://github.com/docker/build-push-action)
- [Publishing Docker images with GitHub Actions](https://docs.github.com/actions/guides/publishing-docker-images)
- [GitHub packages permissions](https://docs.github.com/packages/learn-github-packages/about-permissions-for-github-packages)

## Next Step

Continue with [Compile Pipelines](03-compile-pipelines.md).
