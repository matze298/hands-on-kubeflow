# GPU Smoke Test

This page verifies that GPU workloads are possible from containers and, where supported, from local Kubernetes.

The tutorial targets a Linux or WSL2 Linux development machine with an NVIDIA GPU.

## What You Will Build

You will run two smoke tests:

1. GPU visibility inside a Docker container
2. GPU visibility inside a Kubernetes pod

The first test is required for GPU readiness.

The second test depends on your local Kubernetes setup. It is the bridge toward GPU-enabled Kubeflow components.

If the Kubernetes test is not possible on your machine yet, the container-level checks still establish the baseline you need for the later GPU chapter.

## Why This Matters

ML engineers often test code directly on the host GPU:

```bash
python train.py
```

Kubeflow will not run your code that way.

Kubeflow runs a container inside Kubernetes. For GPU training to work, the GPU must be visible at multiple layers:

```text
host NVIDIA driver
  ↓
container runtime GPU support
  ↓
Kubernetes device plugin
  ↓
pod resource request
  ↓
PyTorch sees CUDA
```

If any layer is broken, the training component may fail or silently fall back to CPU.

That layered check is useful because it tells you where to fix the problem instead of guessing.

## Step 1: Host GPU Check

Run:

```bash
nvidia-smi
```

Expected result:

```text
NVIDIA-SMI ...
GPU Name ...
```

If this fails, fix the host or WSL2 NVIDIA setup first.

## Step 2: Container GPU Check

Run:

```bash
docker run --rm --gpus all nvidia/cuda:12.6.0-base-ubuntu24.04 nvidia-smi
```

Expected result:

```text
NVIDIA-SMI ...
```

If this fails, fix NVIDIA Container Toolkit or Docker Desktop WSL2 integration.

## Step 3: PyTorch CUDA Container Check

Run:

```bash
docker run --rm --gpus all pytorch/pytorch:2.7.1-cuda12.6-cudnn9-runtime python - <<'PY'
import torch

print(f"torch={torch.__version__}")
print(f"cuda_available={torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"device_count={torch.cuda.device_count()}")
    print(f"device_name={torch.cuda.get_device_name(0)}")
PY
```

Expected result:

```text
cuda_available=True
```

## Step 4: Install the NVIDIA Kubernetes Device Plugin

Kubernetes does not expose GPUs to pods automatically. It needs a device plugin.

Apply the NVIDIA device plugin:

```bash
kubectl apply -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.17.1/deployments/static/nvidia-device-plugin.yml
```

Wait for it:

```bash
kubectl -n kube-system rollout status daemonset/nvidia-device-plugin-daemonset --timeout=120s
```

Check:

```bash
kubectl -n kube-system get pods -l name=nvidia-device-plugin-ds
```

!!! note

    Local GPU support with `kind` can be more fragile than GPU support on a real Linux Kubernetes node. If this step does not work on your machine, keep the Docker GPU check as the required local baseline and revisit Kubernetes GPU support in the dedicated local GPU chapter.

This is still a valuable result: the container path tells you whether your host, runtime, and CUDA image are working even when the Kubernetes device plugin path is not ready yet.

## Step 5: Check Node GPU Capacity

Run:

```bash
kubectl describe nodes | grep -A5 -B5 "nvidia.com/gpu" || true
```

If GPU capacity is exposed, you should see something like:

```text
nvidia.com/gpu: 1
```

If you do not see GPU capacity, the Kubernetes device plugin is not successfully exposing the GPU.

## Step 6: Run a GPU Pod

Create a GPU pod:

```bash
mkdir -p infra/k8s
cat > infra/k8s/gpu-smoke-test.yaml <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: gpu-smoke-test
  namespace: kubeflow-by-doing
spec:
  restartPolicy: Never
  containers:
    - name: cuda
      image: nvidia/cuda:12.6.0-base-ubuntu24.04
      command: ["nvidia-smi"]
      resources:
        limits:
          nvidia.com/gpu: 1
EOF

kubectl apply -f infra/k8s/gpu-smoke-test.yaml
```

Watch:

```bash
kubectl get pod gpu-smoke-test -w
```

When it completes:

```bash
kubectl logs gpu-smoke-test
```

Expected result:

```text
NVIDIA-SMI ...
```

## Step 7: Run a PyTorch CUDA Pod

```bash
cat > infra/k8s/pytorch-gpu-smoke-test.yaml <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: pytorch-gpu-smoke-test
  namespace: kubeflow-by-doing
spec:
  restartPolicy: Never
  containers:
    - name: torch
      image: pytorch/pytorch:2.7.1-cuda12.6-cudnn9-runtime
      command:
        - python
        - -c
        - |
          import torch
          print(f"torch={torch.__version__}")
          print(f"cuda_available={torch.cuda.is_available()}")
          if torch.cuda.is_available():
              print(f"device_count={torch.cuda.device_count()}")
              print(f"device_name={torch.cuda.get_device_name(0)}")
      resources:
        limits:
          nvidia.com/gpu: 1
EOF

kubectl apply -f infra/k8s/pytorch-gpu-smoke-test.yaml
```

Inspect logs:

```bash
kubectl logs pytorch-gpu-smoke-test
```

Expected output:

```text
cuda_available=True
```

## Common Problems

### Docker sees the GPU, Kubernetes does not

This means container-level GPU support works, but Kubernetes device plugin support is missing or not compatible with the local cluster setup.

Check:

```bash
kubectl -n kube-system get pods
kubectl -n kube-system logs -l name=nvidia-device-plugin-ds
kubectl describe nodes | grep nvidia.com/gpu
```

### GPU pod stays `Pending`

Describe it:

```bash
kubectl describe pod gpu-smoke-test
```

Look for:

```text
Insufficient nvidia.com/gpu
```

This usually means the node does not advertise GPU capacity.

### PyTorch says `cuda_available=False`

Possible causes:

- wrong PyTorch image
- CUDA/runtime mismatch
- GPU was not requested in pod resources
- Kubernetes did not assign a GPU
- NVIDIA runtime is not configured correctly

### WSL2 host works but Docker fails

Check:

- WSL2 GPU support
- Docker Desktop version
- WSL2 integration
- NVIDIA Container Toolkit
- Docker restart after install

## Cleanup

```bash
kubectl delete pod gpu-smoke-test --ignore-not-found
kubectl delete pod pytorch-gpu-smoke-test --ignore-not-found
```

Keep the NVIDIA device plugin installed if the GPU tests worked and you plan to continue with GPU workloads.

If you are continuing through the tutorial, leave the cluster in the state that best matches your next chapter. This page is a smoke test, not a permanent cluster change.

To remove it:

```bash
kubectl delete -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.17.1/deployments/static/nvidia-device-plugin.yml
```

## What You Learned

You verified the GPU path from host to container and, where supported, from Kubernetes pod to PyTorch.

This is the foundation for GPU-enabled Kubeflow training components later.

## References

- [NVIDIA Container Toolkit installation guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
- [CUDA on WSL user guide](https://docs.nvidia.com/cuda/wsl-user-guide/index.html)
- [NVIDIA Kubernetes device plugin](https://github.com/NVIDIA/k8s-device-plugin)
- [Kubernetes device plugins](https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/device-plugins/)
- [Kubernetes GPU scheduling](https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/)

## Acceptance Criteria

You are done when:

- `nvidia-smi` works on the host
- `docker run --gpus all ... nvidia-smi` works
- a PyTorch CUDA container reports `cuda_available=True`
- either a Kubernetes GPU pod succeeds, or you have documented that your local kind setup does not expose the GPU yet
- you understand that Kubeflow GPU training depends on Kubernetes GPU scheduling, not only PyTorch CUDA support

## Next Step

Continue with Chapter 2: Kubeflow Pipelines.
