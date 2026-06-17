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

ensure_k3s_running() {
  need_cmd k3s

  log "Checking k3s service"
  if command -v systemctl >/dev/null 2>&1; then
    if ! run_sudo systemctl is-active --quiet k3s; then
      run_sudo systemctl start k3s
    fi
  fi
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
