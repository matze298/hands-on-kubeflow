#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

run_sudo() {
  if [ "$(id -u)" -eq 0 ]; then
    "$@"
  else
    sudo "$@"
  fi
}

refresh_user_kubeconfig() {
  local target_user
  local target_home
  local kubeconfig

  target_user="${SUDO_USER:-${USER}}"
  target_home="$(getent passwd "${target_user}" | cut -d: -f6)"
  if [ -z "${target_home}" ]; then
    printf '[bootstrap-gpu-cluster.sh] ERROR: Could not resolve home directory for %s\n' "${target_user}" >&2
    exit 1
  fi
  kubeconfig="${target_home}/.kube/k3s-kubeflow.yaml"

  mkdir -p "${target_home}/.kube"
  run_sudo cp /etc/rancher/k3s/k3s.yaml "${kubeconfig}"
  run_sudo chown "${target_user}:" "${target_home}/.kube" "${kubeconfig}"

  KUBECONFIG="${kubeconfig}" kubectl config rename-context default k3s-kubeflow >/dev/null 2>&1 || true
  KUBECONFIG="${kubeconfig}" kubectl config use-context k3s-kubeflow >/dev/null

  printf '\n[bootstrap-gpu-cluster.sh] Refreshed kubeconfig: %s\n' "${kubeconfig}"
  printf '[bootstrap-gpu-cluster.sh] Use it with: export KUBECONFIG=%s\n' "${kubeconfig}"
}

"${SCRIPT_DIR}/test-gpu-k3s.sh" \
  --raise-limits \
  --configure-docker \
  --reinstall

refresh_user_kubeconfig
