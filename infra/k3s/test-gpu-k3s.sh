#!/usr/bin/env bash
set -euo pipefail

# This script is a local viability probe: it verifies whether this WSL/Linux
# machine can run GPU-requesting Kubernetes pods through k3s and Docker.

SCRIPT_NAME="$(basename "$0")"

K3S_INSTALL_URL="${K3S_INSTALL_URL:-https://get.k3s.io}"
NVIDIA_DEVICE_PLUGIN_VERSION="${NVIDIA_DEVICE_PLUGIN_VERSION:-v0.19.2}"
CUDA_IMAGE="${CUDA_IMAGE:-nvidia/cuda:12.9.1-base-ubuntu24.04}"
GPU_NAMESPACE="${GPU_NAMESPACE:-gpu-smoke}"
GPU_POD_NAME="${GPU_POD_NAME:-k3s-gpu-smoke}"
RUNTIME_CLASS="${RUNTIME_CLASS:-docker-default}"
MIN_INOTIFY_INSTANCES="${MIN_INOTIFY_INSTANCES:-1024}"
MIN_INOTIFY_WATCHES="${MIN_INOTIFY_WATCHES:-1048576}"

REINSTALL=0
CLEANUP=0
SKIP_INSTALL=0
RAISE_LIMITS=0
CONFIGURE_DOCKER=0

usage() {
  cat <<EOF
Usage: ${SCRIPT_NAME} [--reinstall] [--cleanup] [--skip-install] [--raise-limits] [--configure-docker]

Tests native k3s GPU viability on WSL/Linux end to end:
  1. host Docker GPU access
  2. k3s with Docker runtime
  3. cluster health and local-path storage
  4. NVIDIA device plugin
  5. a Kubernetes pod requesting nvidia.com/gpu

Options:
  --reinstall    Uninstall an existing k3s before installing.
  --cleanup      Uninstall k3s after the test finishes.
  --skip-install Use the current k3s cluster instead of installing k3s.
  --raise-limits Raise inotify limits for this running WSL/Linux session.
  --configure-docker Configure Docker to use the NVIDIA runtime by default.
  -h, --help     Show this help.

Environment overrides:
  CUDA_IMAGE=${CUDA_IMAGE}
  NVIDIA_DEVICE_PLUGIN_VERSION=${NVIDIA_DEVICE_PLUGIN_VERSION}
  RUNTIME_CLASS=${RUNTIME_CLASS}
  MIN_INOTIFY_INSTANCES=${MIN_INOTIFY_INSTANCES}
  MIN_INOTIFY_WATCHES=${MIN_INOTIFY_WATCHES}

Notes:
  - This script may use sudo.
  - Do not run it on a machine where an existing k3s cluster matters.
  - On WSL, install the Windows NVIDIA driver; do not install a Linux GPU driver.
  - --configure-docker restarts Docker. Use it only on a disposable local tutorial environment.
EOF
}

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

cleanup() {
  if [ "${CLEANUP}" -eq 1 ]; then
    log "Cleaning up k3s"
    if command -v k3s-uninstall.sh >/dev/null 2>&1; then
      run_sudo k3s-uninstall.sh
    elif [ -x /usr/local/bin/k3s-uninstall.sh ]; then
      run_sudo /usr/local/bin/k3s-uninstall.sh
    else
      log "k3s uninstall script not found; leaving cluster in place"
    fi
  else
    log "Leaving k3s running for inspection"
  fi
}

parse_args() {
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --reinstall)
        REINSTALL=1
        ;;
      --cleanup)
        CLEANUP=1
        ;;
      --skip-install)
        SKIP_INSTALL=1
        ;;
      --raise-limits)
        RAISE_LIMITS=1
        ;;
      --configure-docker)
        CONFIGURE_DOCKER=1
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        die "Unknown argument: $1"
        ;;
    esac
    shift
  done
}

sysctl_value() {
  sysctl -n "$1" 2>/dev/null || printf '0'
}

check_host_limits() {
  local instances
  local watches
  instances="$(sysctl_value fs.inotify.max_user_instances)"
  watches="$(sysctl_value fs.inotify.max_user_watches)"

  log "Checking host inotify limits"
  printf 'fs.inotify.max_user_instances=%s\n' "${instances}"
  printf 'fs.inotify.max_user_watches=%s\n' "${watches}"

  if [ "${instances}" -lt "${MIN_INOTIFY_INSTANCES}" ] || [ "${watches}" -lt "${MIN_INOTIFY_WATCHES}" ]; then
    if [ "${RAISE_LIMITS}" -eq 1 ]; then
      log "Raising inotify limits for this running system"
      run_sudo sysctl -w "fs.inotify.max_user_instances=${MIN_INOTIFY_INSTANCES}"
      run_sudo sysctl -w "fs.inotify.max_user_watches=${MIN_INOTIFY_WATCHES}"
    else
      die "Host inotify limits are low for local Kubernetes. Re-run with --raise-limits or run:
  sudo sysctl -w fs.inotify.max_user_instances=${MIN_INOTIFY_INSTANCES}
  sudo sysctl -w fs.inotify.max_user_watches=${MIN_INOTIFY_WATCHES}

If k3s already failed, clean it up first:
  sudo k3s-uninstall.sh"
    fi
  fi
}

configure_docker_for_k3s() {
  if [ "${CONFIGURE_DOCKER}" -ne 1 ]; then
    log "Skipping Docker NVIDIA default-runtime configuration"
    log "Use --configure-docker if the NVIDIA device plugin fails with NVML ERROR_LIBRARY_NOT_FOUND."
    return
  fi

  need_cmd nvidia-ctk
  log "Configuring Docker to use the NVIDIA runtime by default"
  run_sudo nvidia-ctk runtime configure --runtime=docker --set-as-default

  log "Restarting Docker"
  if command -v systemctl >/dev/null 2>&1; then
    run_sudo systemctl restart docker
  else
    run_sudo service docker restart
  fi
}

check_host_gpu() {
  need_cmd docker

  log "Checking host Docker GPU access with ${CUDA_IMAGE}"
  docker run --rm --gpus all "${CUDA_IMAGE}" nvidia-smi -L
}

install_k3s() {
  if [ "${SKIP_INSTALL}" -eq 1 ]; then
    log "Skipping k3s install; using current k3s"
    return
  fi

  if [ "${REINSTALL}" -eq 1 ] && command -v k3s-uninstall.sh >/dev/null 2>&1; then
    log "Reinstall requested; uninstalling existing k3s"
    run_sudo k3s-uninstall.sh
  elif [ "${REINSTALL}" -eq 1 ] && [ -x /usr/local/bin/k3s-uninstall.sh ]; then
    log "Reinstall requested; uninstalling existing k3s"
    run_sudo /usr/local/bin/k3s-uninstall.sh
  fi

  log "Installing k3s with Docker runtime"
  if [ "$(id -u)" -eq 0 ]; then
    curl -sfL "${K3S_INSTALL_URL}" | INSTALL_K3S_EXEC="--docker --write-kubeconfig-mode 644" sh -
  else
    curl -sfL "${K3S_INSTALL_URL}" | sudo env INSTALL_K3S_EXEC="--docker --write-kubeconfig-mode 644" sh -
  fi
}

check_k3s_health() {
  command -v k3s >/dev/null 2>&1 || die "k3s is not installed or not on PATH"

  log "Checking k3s status"
  if command -v systemctl >/dev/null 2>&1; then
    run_sudo systemctl status k3s --no-pager || true
    if ! run_sudo systemctl is-active --quiet k3s; then
      log "k3s is not active; recent service logs"
      run_sudo journalctl -u k3s -n 120 --no-pager -l || true
      die "k3s service is not active"
    fi
  else
    log "systemctl not available; continuing with kubectl checks"
  fi

  log "Waiting for at least one node to register"
  wait_for_k3s_nodes 240

  log "Waiting for node readiness"
  kubectl_k3s wait --for=condition=Ready node --all --timeout=240s

  log "Cluster nodes"
  kubectl_k3s get nodes -o wide

  log "kube-system pods"
  kubectl_k3s get pods -n kube-system -o wide

  wait_for_kube_system

  log "Storage class"
  kubectl_k3s get storageclass
}

wait_for_k3s_nodes() {
  local timeout_seconds="${1:-180}"
  local started
  local node_count
  started="$(date +%s)"

  while true; do
    node_count="$(kubectl_k3s get nodes --no-headers 2>/dev/null | wc -l)"
    if [ "${node_count}" -gt 0 ]; then
      return
    fi

    if [ "$(( $(date +%s) - started ))" -ge "${timeout_seconds}" ]; then
      if command -v systemctl >/dev/null 2>&1; then
        run_sudo journalctl -u k3s -n 160 --no-pager -l || true
      fi
      die "Timed out waiting for a k3s node to register"
    fi
    sleep 5
  done
}

check_nvidia_runtime() {
  log "Checking whether k3s containerd config mentions NVIDIA runtimes"
  if run_sudo test -f /var/lib/rancher/k3s/agent/etc/containerd/config.toml; then
    run_sudo grep -n "nvidia" /var/lib/rancher/k3s/agent/etc/containerd/config.toml || true
  else
    log "containerd config not found; this is expected when k3s is running with --docker"
  fi

  log "Checking RuntimeClass objects"
  kubectl_k3s get runtimeclass || true
}

wait_for_kube_system() {
  log "Waiting for k3s kube-system deployments"
  kubectl_k3s -n kube-system rollout status deployment/coredns --timeout=240s
  kubectl_k3s -n kube-system rollout status deployment/local-path-provisioner --timeout=240s

  log "Waiting for flannel subnet config"
  wait_for_path /run/flannel/subnet.env 120
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
      kubectl_k3s get pods -n kube-system -o wide || true
      die "Timed out waiting for ${path}"
    fi
    sleep 3
  done
}

install_device_plugin() {
  local manifest
  manifest="https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/${NVIDIA_DEVICE_PLUGIN_VERSION}/deployments/static/nvidia-device-plugin.yml"

  log "Installing NVIDIA device plugin ${NVIDIA_DEVICE_PLUGIN_VERSION}"
  kubectl_k3s apply -f "${manifest}"

  log "Waiting for NVIDIA device plugin daemonset"
  kubectl_k3s -n kube-system rollout status daemonset/nvidia-device-plugin-daemonset --timeout=240s

  log "Device plugin pods"
  kubectl_k3s get pods -n kube-system -l name=nvidia-device-plugin-ds -o wide || true
}

check_allocatable_gpu() {
  log "Checking allocatable nvidia.com/gpu"
  wait_for_allocatable_gpu 240
}

wait_for_allocatable_gpu() {
  local timeout_seconds="${1:-120}"
  local started
  started="$(date +%s)"

  while true; do
    kubectl_k3s get nodes -o jsonpath='{range .items[*]}{.metadata.name}{" capacity="}{.status.capacity.nvidia\.com/gpu}{" allocatable="}{.status.allocatable.nvidia\.com/gpu}{"\n"}{end}'
    printf '\n'

    if kubectl_k3s get nodes -o jsonpath='{range .items[*]}{.status.allocatable.nvidia\.com/gpu}{"\n"}{end}' | grep -Eq '^[1-9][0-9]*$'; then
      return
    fi

    if [ "$(( $(date +%s) - started ))" -ge "${timeout_seconds}" ]; then
      log "NVIDIA device plugin logs"
      kubectl_k3s logs -n kube-system -l name=nvidia-device-plugin-ds --tail=120 || true
      die "No allocatable nvidia.com/gpu found on any node"
    fi
    sleep 5
  done
}

wait_for_gpu_pod() {
  local timeout_seconds="${1:-180}"
  local started
  local phase
  started="$(date +%s)"

  log "Waiting for GPU pod to finish"
  while true; do
    phase="$(kubectl_k3s get pod -n "${GPU_NAMESPACE}" "${GPU_POD_NAME}" -o jsonpath='{.status.phase}' 2>/dev/null || true)"
    case "${phase}" in
      Succeeded)
        return
        ;;
      Failed)
        kubectl_k3s describe pod -n "${GPU_NAMESPACE}" "${GPU_POD_NAME}" || true
        die "GPU pod failed"
        ;;
    esac

    if [ "$(( $(date +%s) - started ))" -ge "${timeout_seconds}" ]; then
      kubectl_k3s describe pod -n "${GPU_NAMESPACE}" "${GPU_POD_NAME}" || true
      die "Timed out waiting for GPU pod to finish"
    fi
    sleep 5
  done
}

run_gpu_pod() {
  local runtime_class_line
  runtime_class_line=""

  if [ "${RUNTIME_CLASS}" = "docker-default" ]; then
    log "Using Docker default runtime; omitting runtimeClassName"
  elif [ "${RUNTIME_CLASS}" = "auto" ]; then
    if kubectl_k3s get runtimeclass nvidia >/dev/null 2>&1; then
      runtime_class_line="  runtimeClassName: nvidia"
      log "Using detected RuntimeClass: nvidia"
    else
      log "No RuntimeClass named nvidia detected; omitting runtimeClassName"
    fi
  elif [ -n "${RUNTIME_CLASS}" ] && [ "${RUNTIME_CLASS}" != "none" ]; then
    runtime_class_line="  runtimeClassName: ${RUNTIME_CLASS}"
    log "Using requested RuntimeClass: ${RUNTIME_CLASS}"
  else
    log "RUNTIME_CLASS=none; omitting runtimeClassName"
  fi

  log "Running GPU smoke pod"
  kubectl_k3s create namespace "${GPU_NAMESPACE}" --dry-run=client -o yaml | kubectl_k3s apply -f -
  kubectl_k3s delete pod -n "${GPU_NAMESPACE}" "${GPU_POD_NAME}" --ignore-not-found

  cat <<EOF | kubectl_k3s apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: ${GPU_POD_NAME}
  namespace: ${GPU_NAMESPACE}
spec:
  restartPolicy: Never
${runtime_class_line}
  containers:
    - name: cuda
      image: ${CUDA_IMAGE}
      command: ["nvidia-smi", "-L"]
      resources:
        limits:
          nvidia.com/gpu: 1
EOF

  wait_for_gpu_pod 180

  log "GPU pod status"
  kubectl_k3s get pod -n "${GPU_NAMESPACE}" "${GPU_POD_NAME}" -o wide

  log "GPU pod logs"
  kubectl_k3s logs -n "${GPU_NAMESPACE}" "${GPU_POD_NAME}"
}

main() {
  parse_args "$@"
  trap cleanup EXIT

  need_cmd curl
  if [ "$(id -u)" -ne 0 ]; then
    need_cmd sudo
  fi
  check_host_limits
  configure_docker_for_k3s
  check_host_gpu
  install_k3s
  check_k3s_health
  check_nvidia_runtime
  install_device_plugin
  check_allocatable_gpu
  run_gpu_pod

  log "k3s GPU smoke test completed"
}

main "$@"
