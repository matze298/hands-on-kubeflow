#!/usr/bin/env sh
set -eu

# Build the kubeflow-by-doing training image.
docker build -t kubeflow-by-doing/train:local .
