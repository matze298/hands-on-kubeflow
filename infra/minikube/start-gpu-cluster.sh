#!/usr/bin/env bash
set -euo pipefail

PROFILE="${MINIKUBE_PROFILE:-kubeflow-by-doing-gpu}"
CPUS="${MINIKUBE_CPUS:-8}"
MEMORY="${MINIKUBE_MEMORY:-8162}"

minikube start \
  --profile "$PROFILE" \
  --driver docker \
  --container-runtime docker \
  --gpus all \
  --cpus "$CPUS" \
  --memory "$MEMORY"

minikube addons enable nvidia-device-plugin --profile "$PROFILE"
