#!/usr/bin/env bash
set -euo pipefail

sudo microk8s status --wait-ready
sudo microk8s enable dns storage registry
sudo microk8s enable gpu --gpu-operator-set-as-default-runtime

mkdir -p "$HOME/.kube"
sudo microk8s config > "$HOME/.kube/microk8s-config"

if [ -f "$HOME/.kube/config" ]; then
  KUBECONFIG="$HOME/.kube/config:$HOME/.kube/microk8s-config" kubectl config view --flatten > "$HOME/.kube/config.merged"
  mv "$HOME/.kube/config.merged" "$HOME/.kube/config"
else
  cp "$HOME/.kube/microk8s-config" "$HOME/.kube/config"
fi

kubectl config use-context microk8s
kubectl create namespace kubeflow-by-doing --dry-run=client -o yaml | kubectl apply -f -
kubectl config set-context --current --namespace=kubeflow-by-doing

kubectl get nodes -o wide
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{" allocatable gpu="}{.status.allocatable.nvidia\.com/gpu}{"\n"}{end}'
