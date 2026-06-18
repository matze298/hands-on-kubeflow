#!/usr/bin/env bash
set -euo pipefail

SOURCE_KUBECONFIG="$(mktemp)"
MERGED_KUBECONFIG="$(mktemp)"
trap 'rm -f "${SOURCE_KUBECONFIG}" "${MERGED_KUBECONFIG}"' EXIT

printf '\n[deploy_cluster.sh] Preparing the local k3s Kubeflow cluster\n'

# Start k3s if systemd is available and the service is currently stopped.
printf '\n[deploy_cluster.sh] Checking the k3s service\n'
if command -v systemctl >/dev/null 2>&1; then
  if ! sudo systemctl is-active --quiet k3s; then
    sudo systemctl start k3s
  fi
fi

# Export the root-owned k3s kubeconfig into a temporary file the user can read.
printf '\n[deploy_cluster.sh] Preparing the k3s-kubeflow kubeconfig context\n'
sudo k3s kubectl config view --raw --flatten > "${SOURCE_KUBECONFIG}"

# Rename k3s' generic default entries to the tutorial's stable context name.
sed -i \
  -e "s/name: default/name: k3s-kubeflow/g" \
  -e "s/cluster: default/cluster: k3s-kubeflow/g" \
  -e "s/user: default/user: k3s-kubeflow/g" \
  -e "s/current-context: default/current-context: k3s-kubeflow/g" \
  "${SOURCE_KUBECONFIG}"

# Merge k3s-kubeflow into the normal ~/.kube/config alongside any existing contexts.
printf '\n[deploy_cluster.sh] Merging k3s-kubeflow into %s/.kube/config\n' "${HOME}"
mkdir -p "${HOME}/.kube"
if [ -f "${HOME}/.kube/config" ]; then
  export KUBECONFIG="${SOURCE_KUBECONFIG}:${HOME}/.kube/config"
else
  export KUBECONFIG="${SOURCE_KUBECONFIG}"
fi
kubectl config view --flatten > "${MERGED_KUBECONFIG}"

mv "${MERGED_KUBECONFIG}" "${HOME}/.kube/config"
chmod 600 "${HOME}/.kube/config"

# From here on, use the normal kubeconfig.
export KUBECONFIG="${HOME}/.kube/config"
kubectl config use-context k3s-kubeflow >/dev/null

# Wait until the k3s node and core system pods are ready.
printf '\n[deploy_cluster.sh] Waiting for the k3s node and core pods\n'
kubectl wait --for=condition=Ready node --all --timeout=240s
kubectl -n kube-system rollout status deployment/coredns --timeout=240s
kubectl -n kube-system rollout status deployment/local-path-provisioner --timeout=240s

# Wait until flannel has written its subnet file. Without this, pod networking is not ready yet.
printf '\n[deploy_cluster.sh] Waiting for flannel networking\n'
flannel_wait_started="$(date +%s)"
while ! sudo test -f /run/flannel/subnet.env; do
  if [ "$(( $(date +%s) - flannel_wait_started ))" -ge 120 ]; then
    printf '[deploy_cluster.sh] ERROR: timed out waiting for /run/flannel/subnet.env\n' >&2
    exit 1
  fi
  sleep 3
done

# Install the NVIDIA device plugin so Kubernetes can expose nvidia.com/gpu.
printf '\n[deploy_cluster.sh] Installing the NVIDIA device plugin\n'
kubectl apply -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.19.2/deployments/static/nvidia-device-plugin.yml
kubectl -n kube-system rollout status daemonset/nvidia-device-plugin-daemonset --timeout=240s

# Wait until at least one node reports GPU capacity that pods can request.
printf '\n[deploy_cluster.sh] Waiting for allocatable nvidia.com/gpu capacity\n'
gpu_wait_started="$(date +%s)"
while true; do
  kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{" capacity="}{.status.capacity.nvidia\.com/gpu}{" allocatable="}{.status.allocatable.nvidia\.com/gpu}{"\n"}{end}'
  printf '\n'

  if kubectl get nodes -o jsonpath='{range .items[*]}{.status.allocatable.nvidia\.com/gpu}{"\n"}{end}' | grep -Eq '^[1-9][0-9]*$'; then
    break
  fi

  if [ "$(( $(date +%s) - gpu_wait_started ))" -ge 240 ]; then
    kubectl logs -n kube-system -l name=nvidia-device-plugin-ds --tail=120 || true
    printf '[deploy_cluster.sh] ERROR: no allocatable nvidia.com/gpu found on any node\n' >&2
    exit 1
  fi

  sleep 5
done

# Create the tutorial namespace and make it the default namespace on this context.
kubectl create namespace kubeflow-by-doing --dry-run=client -o yaml | kubectl apply -f -
kubectl config set-context --current --namespace=kubeflow-by-doing >/dev/null

printf '\n[deploy_cluster.sh] Current context: k3s-kubeflow\n'
printf '[deploy_cluster.sh] k3s GPU cluster is ready\n'
