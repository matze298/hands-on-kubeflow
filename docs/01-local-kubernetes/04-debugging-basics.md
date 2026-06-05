# Kubernetes Debugging Basics

Kubeflow debugging is often Kubernetes debugging.

Before installing Kubeflow Pipelines, you should be comfortable answering four questions:

1. Did Kubernetes create a pod?
2. Is the pod running, waiting, completed, or failed?
3. What did the container log?
4. What do the Kubernetes events say?

## What You Will Build

You will intentionally create broken workloads and debug them.

This page covers:

- image pull failures
- crashing containers
- resource-related pending pods
- missing environment variables
- basic event inspection

## Why This Matters

When a Kubeflow component fails, the UI may show that a step failed. But the real reason is usually in Kubernetes:

```text
KFP step failed
  ↓
pod failed
  ↓
container log or event explains why
```

The commands in this page are used throughout the rest of the tutorial.

The goal is not to memorize every failure mode. The goal is to build a repeatable habit: inspect the pod, read the logs, check the events, and then decide whether the fix belongs in the image, the manifest, or the cluster.

## Core Debugging Commands

Use these constantly:

```bash
kubectl get pods
kubectl get jobs
kubectl logs <pod-name>
kubectl logs job/<job-name>
kubectl describe pod <pod-name>
kubectl get events --sort-by=.lastTimestamp
```

For all namespaces:

```bash
kubectl get pods -A
```

## Failure 1: Image Pull Error

Create a job with a nonexistent image:

```bash
cat > infra/kind/broken-image-job.yaml <<'EOF'
apiVersion: batch/v1
kind: Job
metadata:
  name: broken-image-job
  namespace: kubeflow-by-doing
spec:
  backoffLimit: 0
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: broken
          image: does-not-exist.example.com/ml/train:missing
          command: ["python", "-c", "print('this will not run')"]
EOF

kubectl apply -f infra/kind/broken-image-job.yaml
```

Inspect:

```bash
kubectl get pods --selector=job-name=broken-image-job

POD=$(kubectl get pod --selector=job-name=broken-image-job -o jsonpath='{.items[0].metadata.name}')
kubectl describe pod "$POD"
```

Look for:

```text
ErrImagePull
ImagePullBackOff
Failed to pull image
```

Fix:

```bash
kubectl delete job broken-image-job
```

## Failure 2: Crashing Container

Create a job that starts but exits with an error:

```bash
cat > infra/kind/crashing-job.yaml <<'EOF'
apiVersion: batch/v1
kind: Job
metadata:
  name: crashing-job
  namespace: kubeflow-by-doing
spec:
  backoffLimit: 0
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: crash
          image: python:3.12-slim
          command:
            - python
            - -c
            - |
              print("starting")
              raise RuntimeError("simulated training failure")
EOF

kubectl apply -f infra/kind/crashing-job.yaml
```

Inspect:

```bash
kubectl get pods --selector=job-name=crashing-job
kubectl logs job/crashing-job
kubectl describe job crashing-job
```

Expected log:

```text
starting
RuntimeError: simulated training failure
```

Fix:

```bash
kubectl delete job crashing-job
```

## Failure 3: Missing Environment Variable

Create a job that expects an environment variable:

```bash
cat > infra/kind/missing-env-job.yaml <<'EOF'
apiVersion: batch/v1
kind: Job
metadata:
  name: missing-env-job
  namespace: kubeflow-by-doing
spec:
  backoffLimit: 0
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: train
          image: python:3.12-slim
          command:
            - python
            - -c
            - |
              import os
              print(os.environ["DATASET_URI"])
EOF

kubectl apply -f infra/kind/missing-env-job.yaml
```

Inspect:

```bash
kubectl logs job/missing-env-job
```

Expected error:

```text
KeyError: 'DATASET_URI'
```

This is common in ML workflows: the code assumes a path, URI, token, or config value that was never passed into the container.

Fix:

```bash
kubectl delete job missing-env-job
```

## Failure 4: Too Much Memory Requested

Create a pod that asks for more memory than your local cluster likely has:

```bash
cat > infra/kind/too-large-pod.yaml <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: too-large-pod
  namespace: kubeflow-by-doing
spec:
  restartPolicy: Never
  containers:
    - name: too-large
      image: python:3.12-slim
      command: ["python", "-c", "print('hello')"]
      resources:
        requests:
          cpu: "32"
          memory: "256Gi"
        limits:
          cpu: "32"
          memory: "256Gi"
EOF

kubectl apply -f infra/kind/too-large-pod.yaml
```

Inspect:

```bash
kubectl get pod too-large-pod
kubectl describe pod too-large-pod
```

Look for:

```text
Pending
Insufficient cpu
Insufficient memory
```

Fix:

```bash
kubectl delete pod too-large-pod
```

## Events Are Often the Answer

Show recent events:

```bash
kubectl get events --sort-by=.lastTimestamp
```

Events are especially useful for:

- image pull failures
- scheduling failures
- missing volumes
- failed mounts
- GPU scheduling failures

## Debugging Checklist

When a workload fails, use this sequence:

```bash
kubectl get pods
kubectl get jobs
kubectl describe pod <pod>
kubectl logs <pod>
kubectl get events --sort-by=.lastTimestamp
```

For jobs:

```bash
kubectl logs job/<job-name>
kubectl describe job <job-name>
```

## How This Maps to Kubeflow

Later, Kubeflow Pipelines will create pods for pipeline steps.

When a step fails:

1. open the KFP UI
2. find the failed step
3. identify the pod or component name
4. use `kubectl get pods`
5. inspect logs and events

The UI is useful, but Kubernetes remains the source of truth.

That means the same debugging sequence will work whether the failure comes from a hand-written manifest or from a Kubeflow component generated later in the tutorial.

## Cleanup

```bash
kubectl delete job broken-image-job --ignore-not-found
kubectl delete job crashing-job --ignore-not-found
kubectl delete job missing-env-job --ignore-not-found
kubectl delete pod too-large-pod --ignore-not-found
```

## What You Learned

You debugged common Kubernetes failures that also appear in Kubeflow:

- missing images
- crashed containers
- missing environment variables
- unschedulable resource requests

## References

- [Kubernetes debugging applications](https://kubernetes.io/docs/tasks/debug/debug-application/)
- [Kubernetes events](https://kubernetes.io/docs/reference/kubernetes-api/cluster-resources/event-v1/)
- [Kubernetes resource management](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)
- [Kubernetes Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/)

## Acceptance Criteria

You are done when:

- you have created and debugged an `ImagePullBackOff`
- you have created and debugged a crashing job
- you have created and debugged a missing environment variable
- you have created and debugged an unschedulable pod
- you can explain when to use logs, describe, and events

## Next Step

Continue with [GPU Smoke Test](05-gpu-smoke-test.md).
