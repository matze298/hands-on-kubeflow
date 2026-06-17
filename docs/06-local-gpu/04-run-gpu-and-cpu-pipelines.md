# Run GPU and CPU Pipelines

This page runs the persistent Chapter 3 CPU pipeline and the Chapter 6 GPU pipeline side by side.

## What You Will Run

You will run:

```text
compiled/image_classification_pipeline.yaml
compiled/image_classification_gpu_pipeline.yaml
```

The point is to prove that both workflows can coexist:

```text
Chapter 3 CPU pipeline stays runnable
Chapter 6 GPU pipeline requests nvidia.com/gpu
```

## Rebuild Images

If you changed source or dependencies:

```bash
uv sync
uv run ruff format .
uv run ruff check .
uv run ty check
uv run pytest
```

Build CPU image:

```bash
docker build -f Dockerfile -t kubeflow-by-doing/train:local .
```

Build GPU image:

```bash
docker build -f Dockerfile.gpu -t kubeflow-by-doing/train-gpu:local .
```

## Make Images Available to the Cluster

### k3s

Use the repo's chosen k3s image workflow. Because k3s uses Docker as its runtime in this tutorial, locally built images are available to k3s pods:

```bash
docker images kubeflow-by-doing/train:local
docker images kubeflow-by-doing/train-gpu:local
```

Verify:

### kind fallback

```bash
kind load docker-image kubeflow-by-doing/train:local --name kubeflow-by-doing
```

The GPU image path in this chapter is k3s-only in the default tutorial flow. If you stay on `kind`, keep using the CPU fallback run and do not expect the GPU run to work unless you have separately configured a GPU-capable `kind` cluster.

## Compile the Pipelines

```bash
uv run python pipelines/image_classification_pipeline.py
uv run python pipelines/image_classification_gpu_pipeline.py
```

## Run the Chapter 3 CPU Pipeline

Open the KFP UI:

```bash
kubectl -n kubeflow port-forward svc/ml-pipeline-ui 8080:80
```

Upload:

```text
compiled/image_classification_pipeline.yaml
```

Run with:

```text
epochs: 2
learning_rate: 0.001
seed: 42
```

Expected:

```text
train_model runs on CPU
evaluate_model runs on CPU
pipeline succeeds
```

## Run the Chapter 6 GPU Pipeline

This run assumes the k3s GPU-capable path from the earlier chapters.

Upload:

```text
compiled/image_classification_gpu_pipeline.yaml
```

Run with:

```text
epochs: 2
learning_rate: 0.001
seed: 42
```

Expected:

```text
train_model_gpu requests nvidia.com/gpu: 1
train_model_gpu uses device=cuda
evaluate_model runs on CPU
pipeline succeeds
```

## Verify the Training Pod Requested GPU

Find recent pods:

```bash
kubectl get pods -A --sort-by=.metadata.creationTimestamp
```

Find the training pod, then describe it:

```bash
kubectl describe pod -n <namespace> <training-pod>
```

Look for:

```text
Limits:
  nvidia.com/gpu: 1
```

Inspect logs:

```bash
kubectl logs -n <namespace> <training-pod>
```

You should see training summary output containing:

```text
device: cuda
```

or equivalent.

## Common Problems

### CPU run fails after GPU changes

GPU support must be additive.

Check that CPU mode uses:

```text
kubeflow-by-doing/train:local
device=cpu
no nvidia.com/gpu request
```

### GPU run uses CPU image

Check that you uploaded `compiled/image_classification_gpu_pipeline.yaml`, not the Chapter 3 YAML.

### GPU run starts but PyTorch says CUDA is unavailable

Check:

- GPU image
- pod GPU resource request
- node GPU capacity
- container logs

### GPU run stays pending

This is a scheduling failure. Continue to the next page.

## Acceptance Criteria

You are done when:

- Chapter 3 CPU run succeeds
- GPU run succeeds on k3s GPU path
- training pod for GPU run requests `nvidia.com/gpu`
- training logs show CUDA usage
- artifacts are still produced
- both compiled pipeline YAML files remain available

## References

- [KFP run a pipeline](https://www.kubeflow.org/docs/components/pipelines/user-guides/core-functions/run-a-pipeline/)
- [Kubernetes GPU scheduling](https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/)
- [k3s documentation](https://docs.k3s.io/)
- [NVIDIA Kubernetes device plugin](https://github.com/NVIDIA/k8s-device-plugin)

## Next Step

Continue with [Debug GPU Scheduling](05-debug-gpu-scheduling.md).
