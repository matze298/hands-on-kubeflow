# GPU Smoke Test

This page verifies that GPU workloads are possible from containers and, on the default GPU-capable local cluster path, from local Kubernetes.

The tutorial targets a Linux or WSL2 Linux development machine with an NVIDIA GPU.

## What You Will Build

You will run two smoke tests:

1. GPU visibility inside a Docker container
2. GPU visibility inside a Kubernetes pod

The first test is required for GPU readiness.

The second test depends on your local Kubernetes backend. In this tutorial, the `kind` cluster is the CPU-safe starter baseline and the `minikube` Docker-driver profile on WSL2 is the GPU-capable path for Kubernetes GPU scheduling.

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
docker run --rm -i --gpus all pytorch/pytorch:2.7.1-cuda12.6-cudnn9-runtime python - <<'PY'
import torch

print(f"torch={torch.__version__}")
print(f"cuda_available={torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"device_count={torch.cuda.device_count()}")
    print(f"device_name={torch.cuda.get_device_name(0)}")
PY
```

The `-i` flag keeps standard input attached so `python -` can read the heredoc content inside the container.

Expected result:

```text
cuda_available=True
```

## Step 4: Switch to the GPU-Capable Local Cluster

Before continuing, make sure you are on the GPU-capable `minikube` profile from the cluster setup chapter:

```bash
kubectl config current-context
```

Expected:

```text
kubeflow-gpu
```

If this still points at `kind-kubeflow-by-doing`, switch now:

```bash
kubectl config use-context kubeflow-gpu
kubectl create namespace kubeflow-by-doing --dry-run=client -o yaml | kubectl apply -f -
kubectl config set-context --current --namespace=kubeflow-by-doing
```

Check:

```bash
minikube addons list -p kubeflow-gpu | grep -i nvidia
kubectl get pods -A | grep -i nvidia
```

## Step 5: Check Node GPU Capacity

Run:

```bash
kubectl describe nodes | grep -A5 -B5 "nvidia.com/gpu" || true
```

If GPU capacity is exposed, you should see something like:

```text
nvidia.com/gpu: 1
```

If you do not see any output, the GPU-capable local cluster path is not successfully exposing the GPU on your node.

Treat this as a hard gate:

- if `nvidia.com/gpu` appears, continue with Steps 6 and 7
- if `nvidia.com/gpu` does not appear, do not expect Kubernetes GPU pods or Kubeflow GPU jobs to work yet

The next two pod-based steps depend on `nvidia.com/gpu` being visible on the node first.

### If `nvidia.com/gpu` Does Not Appear

The GPU-capable `minikube` cluster is not ready yet. Before debugging pod specs, re-check the cluster setup itself:

```bash
kubectl get pods -n kube-system
kubectl get pods -A | grep -i nvidia || true
minikube addons list -p kubeflow-gpu | grep -i nvidia
kubectl get nodes -o json | rg "nvidia.com/gpu"
```

If that still shows nothing:

- verify that `nvidia-smi` works on the host
- verify that `docker run --rm --gpus all nvidia/cuda:12.6.0-base-ubuntu24.04 nvidia-smi` works
- verify that `minikube status -p kubeflow-gpu` succeeds
- try `minikube addons enable nvidia-device-plugin -p kubeflow-gpu`
- rerun `bash infra/minikube/bootstrap-gpu-cluster.sh`
- if the `minikube` GPU path still cannot expose GPUs on this machine, stop the Kubernetes GPU path instead of continuing to debug pod specs

Only continue once `kubectl describe nodes | grep -A5 -B5 "nvidia.com/gpu"` shows GPU capacity.

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
        requests:
          cpu: "100m"
          memory: "128Mi"
        limits:
          cpu: "500m"
          memory: "256Mi"
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
        requests:
          cpu: "100m"
          memory: "128Mi"
        limits:
          cpu: "500m"
          memory: "256Mi"
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

This means container-level GPU support works, but the minikube NVIDIA device plugin path is missing or not healthy.

Check:

```bash
kubectl -n kube-system get pods
kubectl get pods -A | grep -i nvidia || true
minikube addons list -p kubeflow-gpu | grep -i nvidia
kubectl describe nodes | grep nvidia.com/gpu
```

If `kubectl describe nodes | grep nvidia.com/gpu` shows nothing, Kubernetes is not advertising a GPU resource. In that state, the pod examples in Steps 6 and 7 are expected to stay pending or fail scheduling.

If the NVIDIA device plugin logs an initialization or runtime mismatch, the node runtime itself is the problem. Recreate or fix the `minikube` GPU setup before spending more time on pod specs.
If the NVIDIA device plugin pod is crashing, fix the `minikube` GPU add-on before spending more time on pod specs.

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

Keep the GPU addon installed if the GPU tests worked and you plan to continue with GPU workloads.

If you are continuing through the tutorial, leave the cluster in the state that best matches your next chapter. This page is a smoke test, not a permanent cluster change.

To reset the GPU-specific cluster state:

```bash
minikube delete -p kubeflow-gpu
bash infra/minikube/bootstrap-gpu-cluster.sh
```

## What You Learned

You verified the GPU path from host to container and, where supported, from Kubernetes pod to PyTorch.

This is the foundation for GPU-enabled Kubeflow training components later.

## References

- [NVIDIA Container Toolkit installation guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
- [CUDA on WSL user guide](https://docs.nvidia.com/cuda/wsl-user-guide/index.html)
- [minikube NVIDIA GPU tutorial](https://minikube.sigs.k8s.io/docs/tutorials/nvidia_gpu/)
- [Kubernetes device plugins](https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/device-plugins/)
- [Kubernetes GPU scheduling](https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/)

## Acceptance Criteria

You are done when:

- `nvidia-smi` works on the host
- `docker run --gpus all ... nvidia-smi` works
- a PyTorch CUDA container reports `cuda_available=True`
- either a Kubernetes GPU pod succeeds on the minikube GPU path, or you have explicitly deferred the Kubernetes GPU path for this machine
- you understand that Kubeflow GPU training depends on Kubernetes GPU scheduling, not only PyTorch CUDA support

## Next Step

Continue with Chapter 2: Kubeflow Pipelines.
