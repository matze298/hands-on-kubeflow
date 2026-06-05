# First Kubernetes Job

In this page, you run your first ML-shaped workload on Kubernetes.

The workload is intentionally tiny. It does not train a real model yet. It exists to establish the basic execution pattern:

```text
container starts
  ↓
Python script runs
  ↓
logs are emitted
  ↓
job completes
```

That is the same basic pattern used later for Kubeflow training components.

## What You Will Build

You will create a Kubernetes `Job` that runs a short Python command.

You will also see how simple runtime parameters become container environment variables, which is the same pattern used later by pipeline inputs.

## Why This Matters

A training run is often a batch workload:

- start from a clean environment
- read inputs
- run training
- write outputs
- exit with success or failure

In Kubernetes, that shape maps naturally to a `Job`.

Kubeflow Pipelines will later create Kubernetes workloads for you. Before that, you should run one manually.

This chapter is about the operational loop, not the Python snippet itself: create the workload, watch it run, inspect the logs, and rerun it when needed.

## Create the Job

Create the manifest in `infra/k8s/` so it stays in the repository and remains easy to rerun and diff later.

```bash
mkdir -p infra/k8s
cat > infra/k8s/hello-ml-job.yaml <<'EOF'
apiVersion: batch/v1 # Use the batch API group because this manifest defines a Job.
kind: Job # Create a Kubernetes Job, which runs a task to completion.
metadata: # Standard object metadata for naming and organizing the resource.
  name: hello-ml-job # The Job name used by kubectl and Kubernetes events.
  namespace: kubeflow-by-doing # Run the Job in the tutorial namespace.
spec: # Desired behavior of the Job controller.
  backoffLimit: 0 # Do not retry failed Pods; fail immediately for easier debugging.
  template: # Pod template that the Job controller will create.
    spec: # Desired behavior of the Pod started by this Job.
      restartPolicy: Never # Do not restart the container inside the Pod after exit.
      containers: # List of containers that make up the Pod.
        - name: hello # Container name within the Pod.
          image: python:3.12-slim # Base image that provides Python for the demo workload.
          command: # Entrypoint override for the container.
            - python # Executable to run inside the container.
            - -c # Tell Python to execute the following inline script.
            - |
              import platform
              import time

              print("hello from a Kubernetes Job")
              print(f"python={platform.python_version()}")
              print("pretending to train a tiny model...")
              time.sleep(2)
              print("metric.accuracy=0.99")
              print("done")
          resources: # Resource contract for scheduling and runtime enforcement.
            requests: # Minimum resources the scheduler should reserve for this container.
              cpu: "100m" # Request one tenth of a CPU core.
              memory: "128Mi" # Request 128 MiB of memory.
            limits: # Maximum resources the container may use.
              cpu: "500m" # Cap CPU usage at half a core.
              memory: "256Mi" # Cap memory usage at 256 MiB.
EOF

kubectl apply -f infra/k8s/hello-ml-job.yaml
```

## Watch the Job

```bash
kubectl get jobs
kubectl get pods
```

Wait until the job completes:

```bash
kubectl wait --for=condition=complete job/hello-ml-job --timeout=120s
```

## Inspect Logs

```bash
kubectl logs job/hello-ml-job
```

Expected output:

```text
hello from a Kubernetes Job
python=3.12.x
pretending to train a tiny model...
metric.accuracy=0.99
done
```

## Inspect the Job

```bash
kubectl describe job hello-ml-job
```

Notice:

- start time
- completion time
- number of succeeded pods
- events

## Rerun the Job

Kubernetes Jobs are immutable in several fields. For tutorial workflows, delete and recreate:

```bash
kubectl delete job hello-ml-job
kubectl apply -f infra/k8s/hello-ml-job.yaml
```

## Add Environment Variables

ML jobs usually receive parameters.

In Kubernetes, environment variables are a simple way to pass small inputs into a container without baking them into the image.

Create the parameterized variant in the same directory:

```bash
cat > infra/k8s/parameterized-ml-job.yaml <<'EOF'
apiVersion: batch/v1
kind: Job
metadata:
  name: parameterized-ml-job
  namespace: kubeflow-by-doing
spec:
  backoffLimit: 0
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: train
          image: python:3.12-slim
          env:
            - name: EPOCHS
              value: "3"
            - name: LEARNING_RATE
              value: "0.001"
          command:
            - python
            - -c
            - |
              import os

              epochs = int(os.environ["EPOCHS"])
              lr = float(os.environ["LEARNING_RATE"])

              print(f"training for {epochs=} with {lr=}")

              for epoch in range(1, epochs + 1):
                  print(f"epoch={epoch} loss={1.0 / epoch:.4f}")

              print("done")
          resources:
            requests:
              cpu: "100m"
              memory: "128Mi"
            limits:
              cpu: "500m"
              memory: "256Mi"
EOF

kubectl apply -f infra/k8s/parameterized-ml-job.yaml
kubectl wait --for=condition=complete job/parameterized-ml-job --timeout=120s
kubectl logs job/parameterized-ml-job
```

## Common Problems

### Pod is `ImagePullBackOff`

The cluster cannot pull the image.

Debug:

```bash
kubectl describe pod --selector=job-name=hello-ml-job
```

Look for events near the bottom.

### Job does not complete

Inspect pods:

```bash
kubectl get pods --selector=job-name=hello-ml-job
kubectl describe pod --selector=job-name=hello-ml-job
```

Show logs:

```bash
kubectl logs job/hello-ml-job
```

### Command works locally but not in Kubernetes

Common reasons:

- missing files
- missing environment variables
- missing credentials
- different working directory
- package not installed in the image
- no access to local filesystem

This is why containerizing ML code early matters.

## Cleanup

```bash
kubectl delete job hello-ml-job --ignore-not-found
kubectl delete job parameterized-ml-job --ignore-not-found
```

## What You Learned

You ran a batch workload as a Kubernetes `Job`.

This is the simplest mental model for a Kubeflow training component.

## References

- [Kubernetes Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/)
- [Kubernetes Pods](https://kubernetes.io/docs/concepts/workloads/pods/)
- [Kubernetes resource management](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)

## Acceptance Criteria

You are done when:

- `hello-ml-job` completes successfully
- `kubectl logs job/hello-ml-job` shows the expected output
- `parameterized-ml-job` completes successfully
- you can delete and recreate a job
- you can explain why a training run maps naturally to a Kubernetes `Job`

## Next Step

Continue with [Kubernetes Debugging Basics](04-debugging-basics.md).
