# Create a Local Kubernetes Cluster

In this page, you create the local Kubernetes cluster used for the rest of the tutorial.

We use `kind` as the starter cluster backend for the initial Kubernetes exercises.

This page also shows the `k3s` Docker-runtime path that becomes the GPU-capable local ML platform for the later chapters.

## What You Will Build

You will create a local cluster named:

```text
kubeflow-by-doing
```

You will also create a namespace named:

```text
kubeflow-by-doing
```

The cluster is disposable. If it breaks, delete it and recreate it.

## Why This Matters

Kubeflow workloads run inside Kubernetes.

A local cluster gives you a cheap, fast, and inspectable place to learn:

- how workloads are scheduled
- how containers run
- how logs are collected
- how services are exposed
- how failures appear
- how Kubeflow later maps pipelines to pods

## Create a kind Config

Create this file:

```bash
mkdir -p infra/kind
cat > infra/kind/kubeflow-by-doing.yaml <<'EOF'
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: kubeflow-by-doing
nodes:
  - role: control-plane
    extraPortMappings:
      - containerPort: 30080
        hostPort: 8080
        protocol: TCP
      - containerPort: 30443
        hostPort: 8443
        protocol: TCP
  - role: worker
EOF
```

This creates:

- one control-plane node
- one worker node
- two optional port mappings for later local services

This is the starter CPU-safe baseline cluster for the tutorial.

## Create the Cluster

```bash
kind create cluster --config infra/kind/kubeflow-by-doing.yaml
```

Verify:

```bash
kubectl cluster-info
kubectl get nodes -o wide
```

Expected result:

```text
NAME                              STATUS   ROLES           AGE   VERSION
kubeflow-by-doing-control-plane   Ready    control-plane   ...
kubeflow-by-doing-worker          Ready    <none>          ...
```

## Create the GPU-Capable Local Cluster

If you want Kubernetes pods to request `nvidia.com/gpu` locally on WSL2, use `k3s` with Docker runtime instead of trying to retrofit GPU passthrough into the `kind` starter cluster.

GPU support for Kubernetes-on-WSL2 is still something you validate on your own machine before continuing. The tutorial uses this k3s path because it starts from the Docker GPU runtime that you already checked in the toolchain page.

The toolchain page already installed k3s with Docker runtime and configured Docker's default runtime as NVIDIA. That avoids relying on a Kubernetes `RuntimeClass` handler that is not supported by the Docker-backed k3s path.

In practice, this script does four things:

- checks that the k3s service is running
- installs the NVIDIA device plugin
- verifies `nvidia.com/gpu` is allocatable
- refreshes the user kubeconfig and tutorial namespace

Create the deployment script:

```bash
mkdir -p infra/k3s
cat > infra/k3s/deploy_cluster.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_NAME="$(basename "$0")"

NVIDIA_DEVICE_PLUGIN_VERSION="${NVIDIA_DEVICE_PLUGIN_VERSION:-v0.19.2}"
TUTORIAL_NAMESPACE="${TUTORIAL_NAMESPACE:-kubeflow-by-doing}"
KUBE_CONTEXT="${KUBE_CONTEXT:-k3s-kubeflow}"

log() {
  printf '\n[%s] %s\n' "${SCRIPT_NAME}" "$*"
}

die() {
  printf '\n[%s] ERROR: %s\n' "${SCRIPT_NAME}" "$*" >&2
  exit 1
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Missing required command: $1"
}

run_sudo() {
  if [ "$(id -u)" -eq 0 ]; then
    "$@"
  else
    sudo "$@"
  fi
}

kubectl_k3s() {
  run_sudo k3s kubectl "$@"
}

wait_for_path() {
  local path="$1"
  local timeout_seconds="${2:-120}"
  local started
  started="$(date +%s)"

  while true; do
    if run_sudo test -f "${path}"; then
      return
    fi
    if [ "$(( $(date +%s) - started ))" -ge "${timeout_seconds}" ]; then
      die "Timed out waiting for ${path}"
    fi
    sleep 3
  done
}

wait_for_cluster() {
  log "Waiting for k3s node readiness"
  kubectl_k3s wait --for=condition=Ready node --all --timeout=240s

  log "Waiting for core kube-system deployments"
  kubectl_k3s -n kube-system rollout status deployment/coredns --timeout=240s
  kubectl_k3s -n kube-system rollout status deployment/local-path-provisioner --timeout=240s

  log "Waiting for flannel networking"
  wait_for_path /run/flannel/subnet.env 120
}

ensure_k3s_running() {
  need_cmd k3s

  log "Checking k3s service"
  if command -v systemctl >/dev/null 2>&1; then
    if ! run_sudo systemctl is-active --quiet k3s; then
      run_sudo systemctl start k3s
    fi
  fi
}

install_device_plugin() {
  local manifest
  manifest="https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/${NVIDIA_DEVICE_PLUGIN_VERSION}/deployments/static/nvidia-device-plugin.yml"

  log "Installing NVIDIA device plugin ${NVIDIA_DEVICE_PLUGIN_VERSION}"
  kubectl_k3s apply -f "${manifest}"
  kubectl_k3s -n kube-system rollout status daemonset/nvidia-device-plugin-daemonset --timeout=240s
}

wait_for_gpu_capacity() {
  local timeout_seconds="${1:-240}"
  local started
  started="$(date +%s)"

  log "Waiting for nvidia.com/gpu allocatable capacity"
  while true; do
    kubectl_k3s get nodes -o jsonpath='{range .items[*]}{.metadata.name}{" capacity="}{.status.capacity.nvidia\.com/gpu}{" allocatable="}{.status.allocatable.nvidia\.com/gpu}{"\n"}{end}'
    printf '\n'

    if kubectl_k3s get nodes -o jsonpath='{range .items[*]}{.status.allocatable.nvidia\.com/gpu}{"\n"}{end}' | grep -Eq '^[1-9][0-9]*$'; then
      return
    fi

    if [ "$(( $(date +%s) - started ))" -ge "${timeout_seconds}" ]; then
      kubectl_k3s logs -n kube-system -l name=nvidia-device-plugin-ds --tail=120 || true
      die "No allocatable nvidia.com/gpu found on any node"
    fi
    sleep 5
  done
}

refresh_user_kubeconfig() {
  local target_user
  local target_home
  local kubeconfig

  target_user="${SUDO_USER:-${USER}}"
  target_home="$(getent passwd "${target_user}" | cut -d: -f6)"
  if [ -z "${target_home}" ]; then
    die "Could not resolve home directory for ${target_user}"
  fi

  kubeconfig="${target_home}/.kube/${KUBE_CONTEXT}.yaml"

  log "Refreshing user kubeconfig ${kubeconfig}"
  mkdir -p "${target_home}/.kube"
  run_sudo cp /etc/rancher/k3s/k3s.yaml "${kubeconfig}"
  run_sudo chown "${target_user}:" "${target_home}/.kube" "${kubeconfig}"

  KUBECONFIG="${kubeconfig}" kubectl config rename-context default "${KUBE_CONTEXT}" >/dev/null 2>&1 || true
  KUBECONFIG="${kubeconfig}" kubectl config use-context "${KUBE_CONTEXT}" >/dev/null
  KUBECONFIG="${kubeconfig}" kubectl create namespace "${TUTORIAL_NAMESPACE}" --dry-run=client -o yaml | KUBECONFIG="${kubeconfig}" kubectl apply -f -
  KUBECONFIG="${kubeconfig}" kubectl config set-context --current --namespace="${TUTORIAL_NAMESPACE}" >/dev/null

  printf '\n[%s] Refreshed kubeconfig: %s\n' "${SCRIPT_NAME}" "${kubeconfig}"
  printf '[%s] Use it with: export KUBECONFIG=%s\n' "${SCRIPT_NAME}" "${kubeconfig}"
}

main() {
  need_cmd kubectl
  if [ "$(id -u)" -ne 0 ]; then
    need_cmd sudo
  fi

  ensure_k3s_running
  wait_for_cluster
  install_device_plugin
  wait_for_gpu_capacity
  refresh_user_kubeconfig

  log "k3s GPU cluster is ready"
}

main "$@"
EOF

chmod +x infra/k3s/deploy_cluster.sh
```

This script:

- starts k3s if systemd reports it is stopped
- waits for k3s networking and storage
- installs the NVIDIA device plugin
- verifies `nvidia.com/gpu` is allocatable
- writes `~/.kube/k3s-kubeflow.yaml`
- creates the tutorial namespace

Then bootstrap the GPU-ready cluster:

```bash
bash infra/k3s/deploy_cluster.sh
```

Verify:

```bash
export KUBECONFIG=~/.kube/k3s-kubeflow.yaml
kubectl config current-context
kubectl get pods -n kube-system
kubectl get pods -A | grep -i nvidia
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{" capacity gpu="}{.status.capacity.nvidia\.com/gpu}{" allocatable gpu="}{.status.allocatable.nvidia\.com/gpu}{"\n"}{end}'
```

Expected result:

- k3s reports one `Ready` node
- core `kube-system` pods are `Running` or `Completed`
- the NVIDIA device plugin is `Running`
- at least one node reports `allocatable gpu=1` or another non-empty GPU count

Confirm the tutorial namespace on the k3s context:

```bash
kubectl get namespace kubeflow-by-doing
kubectl get nodes -o wide
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{" capacity gpu="}{.status.capacity.nvidia\.com/gpu}{" allocatable gpu="}{.status.allocatable.nvidia\.com/gpu}{"\n"}{end}'
```

If `kube-system` is unhealthy or `allocatable gpu=` is blank, stop the GPU path here and debug the k3s setup before moving on to pod specs or Kubeflow workloads.

## Create the Tutorial Namespace

Before creating the namespace, make sure `kubectl` points at the cluster you want to prepare:

- use `kind-kubeflow-by-doing` for the starter Kubernetes path
- use `k3s-kubeflow` for the GPU-capable ML path

```bash
kubectl create namespace kubeflow-by-doing
```

Set it as the default namespace for the current context:

```bash
kubectl config set-context --current --namespace=kubeflow-by-doing
```

Verify:

```bash
kubectl config view --minify --output 'jsonpath={..namespace}'
echo
```

Expected output:

```text
kubeflow-by-doing
```

## Inspect the Cluster

Show all pods:

```bash
kubectl get pods -A
```

Show namespaces:

```bash
kubectl get namespaces
```

Show node details:

```bash
kubectl describe nodes
```

You do not need to understand every line. For now, notice:

- node names
- allocatable CPU and memory
- labels
- conditions
- events

## Optional: Create a Basic Resource Quota

A local cluster can still be overwhelmed. Add a small quota to make resource use explicit:

Create this file:

```bash
cat > infra/kind/kubeflow-by-doing-quota.yaml <<'EOF'
apiVersion: v1
kind: ResourceQuota
metadata:
  name: tutorial-quota
  namespace: kubeflow-by-doing
spec:
  hard:
    requests.cpu: "8"
    requests.memory: 16Gi
    limits.cpu: "8"
    limits.memory: 16Gi
    pods: "50"
EOF
```

Then apply it:

```bash
kubectl apply -f infra/kind/kubeflow-by-doing-quota.yaml
```

Verify:

```bash
kubectl describe resourcequota tutorial-quota
```

If your machine has less memory, adjust the quota or skip this step.

If you are working on the GPU-capable `k3s` path, apply the same namespace and quota manifests there after switching context.

## Common Problems

### `kind create cluster` fails because the name already exists

Delete the old cluster:

```bash
kind delete cluster --name kubeflow-by-doing
```

Then recreate it:

```bash
kind create cluster --config infra/kind/kubeflow-by-doing.yaml
```

### `kubectl get nodes` points to the wrong cluster

List contexts:

```bash
kubectl config get-contexts
```

Switch to the kind context:

```bash
kubectl config use-context kind-kubeflow-by-doing
```

### Nodes stay `NotReady`

Check all pods:

```bash
kubectl get pods -A
```

Then inspect node events:

```bash
kubectl describe nodes
```

For local clusters, the fastest fix is often to delete and recreate.

### Docker is out of resources

Increase Docker Desktop or Docker daemon resources.

As a practical default, reserve at least:

```text
CPU: 8 cores if possible
Memory: 8 GiB minimum for the local k3s path, 16–32 GiB better for heavier Kubeflow workloads
Disk: 50+ GiB free
```

### The `kind` starter cluster cannot request GPUs

That is expected. The `kind` starter cluster is the baseline path for the Kubernetes and Kubeflow basics.

If you want local Kubernetes GPU scheduling on WSL2, use the `k3s` path from this page instead of continuing to debug `kind` node runtime wiring.

### `k3s` core pods are unhealthy

Before installing Kubeflow Pipelines, make sure the cluster itself is healthy:

```bash
kubectl get pods -n kube-system
kubectl get pods -A | grep -i nvidia || true
```

If `coredns`, `local-path-provisioner`, or the NVIDIA device plugin are in `CrashLoopBackOff`, do not continue to Chapter 2 yet.

### `k3s` exits with `too many open files`

On WSL2, k3s can fail during startup with inotify errors such as:

```text
Failed to start cAdvisor
inotify_init: too many open files
```

Raise the inotify limits and reinstall the local cluster:

```bash
sudo sysctl -w fs.inotify.max_user_instances=1024
sudo sysctl -w fs.inotify.max_user_watches=1048576
sudo systemctl restart k3s
bash infra/k3s/deploy_cluster.sh
```

The bootstrap script uses the same limits. If you set them manually, use:

```bash
sudo sysctl -w fs.inotify.max_user_instances=1024
sudo sysctl -w fs.inotify.max_user_watches=1048576
```

### Flannel is not ready yet

If early pods report this event:

```text
failed to load flannel 'subnet.env' file: open /run/flannel/subnet.env: no such file or directory
```

wait for `kube-system` to settle before debugging the workload itself:

```bash
kubectl get pods -n kube-system
sudo test -f /run/flannel/subnet.env && echo ready
```

The k3s test script waits for this file because GPU and device-plugin pods can be scheduled before networking is fully initialized.

### NVIDIA device plugin logs `ERROR_LIBRARY_NOT_FOUND`

If the device plugin crashes and logs:

```text
Failed to initialize NVML: ERROR_LIBRARY_NOT_FOUND
If this is a GPU node, did you set the docker default runtime to `nvidia`?
```

Docker can run GPU containers, but k3s pods are not getting the NVIDIA runtime by default. Reapply the toolchain setup and restart k3s:

```bash
sudo nvidia-ctk runtime configure --runtime=docker --set-as-default
sudo systemctl restart docker
sudo systemctl restart k3s
bash infra/k3s/deploy_cluster.sh
```

This is why the tutorial configures Docker with `--set-as-default` before installing k3s.

### The GPU pod says `RuntimeHandler "nvidia" not supported`

With k3s installed using `--docker`, the GPU pod should rely on Docker's default NVIDIA runtime. Do not add `runtimeClassName: nvidia` for this local path unless you have separately configured that handler.

Omit `runtimeClassName` and let the pod use the Docker runtime path that was already verified.

### The device plugin is running, but `nvidia.com/gpu` is blank

The node capacity can lag briefly after the NVIDIA device plugin starts. Check the plugin logs and wait for the kubelet registration:

```bash
kubectl logs -n kube-system -l name=nvidia-device-plugin-ds --tail=120
kubectl describe node "$(kubectl get nodes -o jsonpath='{.items[0].metadata.name}')" | grep -A20 -E "Capacity|Allocatable"
```

If the logs show `Detected platform: wsl`, `Registered device plugin`, and the node later reports `nvidia.com/gpu: 1`, continue. If registration never appears, rerun the k3s bootstrap with Docker runtime configuration.

## Cleanup

To delete the cluster:

```bash
kind delete cluster --name kubeflow-by-doing
```

To reset the GPU-ready cluster:

```bash
sudo k3s-uninstall.sh
curl -sfL https://get.k3s.io | sudo env INSTALL_K3S_EXEC="--docker --write-kubeconfig-mode 644" sh -
bash infra/k3s/deploy_cluster.sh
```

Do not delete it yet if you are continuing the tutorial.

## What You Learned

You created a local Kubernetes cluster and a namespace for tutorial workloads.

You also learned that local Kubernetes should be treated as disposable infrastructure.

You also saw that the tutorial separates the `kind` starter baseline from the GPU-capable `k3s` path used by the later ML chapters.

## References

- [kind quick start](https://kind.sigs.k8s.io/docs/user/quick-start/)
- [kind configuration](https://kind.sigs.k8s.io/docs/user/configuration/)
- [k3s documentation](https://docs.k3s.io/)
- [NVIDIA Kubernetes device plugin](https://github.com/NVIDIA/k8s-device-plugin)
- [Kubernetes namespaces](https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/)
- [Kubernetes resource quotas](https://kubernetes.io/docs/concepts/policy/resource-quotas/)

## Acceptance Criteria

You are done when:

- `kubectl get nodes` shows ready nodes
- `kubectl config view --minify` points to the cluster you are preparing
- the default namespace is `kubeflow-by-doing`
- `kubectl get pods -A` works
- you know how to delete and recreate the cluster
- if you use the GPU-ready `k3s` path, `kubectl get nodes -o jsonpath=...` shows a non-empty `nvidia.com/gpu`

## Next Step

Continue with [First Kubernetes Job](03-first-kubernetes-job.md).
