#!/usr/bin/env bash
set -euo pipefail

docker run --rm --gpus all nvidia/cuda:12.6.0-base-ubuntu24.04 nvidia-smi

minikube delete -p kubeflow-gpu || true

minikube start \
  -p kubeflow-gpu \
  --driver=docker \
  --container-runtime=docker \
  --gpus all \
  --cpus=8 \
  --memory=16384 \
  --disk-size=80g

kubectl config use-context kubeflow-gpu
kubectl create namespace kubeflow-by-doing --dry-run=client -o yaml | kubectl apply -f -
kubectl config set-context --current --namespace=kubeflow-by-doing

kubectl get nodes -o wide
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{" capacity gpu="}{.status.capacity.nvidia\.com/gpu}{" allocatable gpu="}{.status.allocatable.nvidia\.com/gpu}{"\n"}{end}'

if ! kubectl get nodes -o jsonpath='{range .items[*]}{.status.allocatable.nvidia\.com/gpu}{end}' | grep -q '[0-9]'; then
  minikube addons enable nvidia-device-plugin -p kubeflow-gpu
  kubectl rollout status daemonset/nvidia-device-plugin-daemonset -n kube-system --timeout=180s || true
  kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{" capacity gpu="}{.status.capacity.nvidia\.com/gpu}{" allocatable gpu="}{.status.allocatable.nvidia\.com/gpu}{"\n"}{end}'
fi
