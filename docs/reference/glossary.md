# Glossary and Concept Map

Use this page as a quick translation layer between ML, Kubernetes, Kubeflow, serving, and orchestration terms used in the tutorial.

## Concept Map

```text
local Python code
  -> package and CLI
  -> container image
  -> Kubernetes workload
  -> Kubeflow Pipeline task
  -> durable artifacts
  -> evaluation and promotion
  -> model serving
```

The tutorial keeps these layers visible so you can debug the system from either direction: from a failed pipeline step down to a pod, or from a model artifact up to a served endpoint.

## Core Kubernetes Terms

| Term | Meaning in this tutorial |
|---|---|
| Cluster | The Kubernetes environment running tutorial workloads. `k3s` is the default local ML cluster, while `kind` is the starter and CPU fallback. |
| Context | The kubeconfig target selected by `kubectl`. Check it before applying manifests. |
| Namespace | A logical boundary for related Kubernetes resources. The tutorial mainly uses `kubeflow-by-doing`, `kubeflow`, `minio`, `kserve`, and `flyte`. |
| Pod | The smallest runnable unit in Kubernetes. Pipeline steps, serving containers, MinIO, MLflow, and KServe predictors all run in pods. |
| Container | A process and filesystem packaged from an image. The tutorial builds training, serving, GPU, Flyte, and KServe images. |
| Image | The packaged runtime used by Kubernetes to start containers. On the default k3s path, local Docker images are visible to the cluster. On `kind`, local images must be loaded into the cluster. |
| Job | A Kubernetes workload that runs to completion. It is the closest raw Kubernetes shape to a training run. |
| Deployment | A Kubernetes workload that keeps long-running pods available. The Chapter 5 model server uses a Deployment. |
| Service | A stable in-cluster network endpoint for pods. Port-forwarding usually targets Services. |
| ConfigMap | Non-secret configuration stored in Kubernetes. The serving chapter uses it for model server settings. |
| Secret | Sensitive configuration stored in Kubernetes. The tutorial uses Secrets for S3-compatible credentials and image pulls. |
| PVC | PersistentVolumeClaim. A request for persistent storage. MinIO uses a PVC for local object data. |
| Resource request | The CPU, memory, or GPU amount a pod asks Kubernetes to reserve. |
| Resource limit | The maximum CPU, memory, or GPU amount a container is allowed to use. |
| Taint | A node scheduling rule that keeps pods away unless they have a matching toleration. GPU nodes often use taints. |
| Toleration | A pod setting that allows scheduling onto a tainted node. |

## Kubeflow Pipelines Terms

| Term | Meaning in this tutorial |
|---|---|
| KFP | Kubeflow Pipelines. The workflow engine used for the core tutorial. |
| Standalone KFP | Kubeflow Pipelines installed without the full Kubeflow platform. This is the default tutorial path. |
| Pipeline | A directed workflow made of tasks. The tutorial compiles pipelines to YAML under `compiled/`. |
| Component | A reusable pipeline step. Components wrap Python functions or container commands. |
| Task | A component invocation inside a pipeline graph. At runtime, tasks become Kubernetes workloads. |
| Parameter | A small typed value passed into a pipeline or component, such as `epochs` or `run_id`. |
| Artifact | A file or directory passed between tasks or stored outside the pod filesystem. |
| Metrics | Numeric evaluation outputs used to inspect or gate a run. |
| Pipeline root | The artifact location KFP uses for pipeline outputs. |
| Compiler | The KFP SDK tool that turns Python pipeline definitions into YAML. |
| Run | One execution of a compiled pipeline. Runs are visible in the KFP UI. |
| Evaluation gate | A pipeline branch that promotes a model only if metrics meet a threshold. |
| Promotion | The decision that a model artifact is good enough to be recorded, deployed, or used by the next stage. |

## Artifact and Tracking Terms

| Term | Meaning in this tutorial |
|---|---|
| Object storage | Durable S3-compatible storage for models, metrics, reports, and lineage. Locally this is MinIO. |
| Bucket | The top-level object-storage container. The local bucket is `kubeflow-by-doing`. |
| Artifact layout | The predictable object key structure under `runs/<run_id>/...`. |
| Run ID | A stable identifier that ties artifacts, metrics, lineage, and serving state together. |
| Lineage | A record of what inputs, code, image, parameters, and outputs produced a model. |
| MLflow | The local experiment tracker used for parameters, metrics, tags, and artifact references. |
| Registry record | A lightweight JSON record for promoted models. The tutorial uses this before introducing a full model registry. |

## Serving Terms

| Term | Meaning in this tutorial |
|---|---|
| FastAPI server | The transparent first serving implementation in Chapter 5. It loads `model.pt` and exposes `/healthz` and `/predict`. |
| Smoke test | A small request that proves the server is reachable and can return a prediction. |
| KServe | Optional Kubernetes-native model serving layer introduced after the core serving path. |
| InferenceService | KServe's user-facing serving resource. KServe reconciles it into lower-level Kubernetes resources. |
| ServingRuntime | A KServe runtime that knows how to serve a model format. |
| Storage initializer | A KServe init container that downloads model artifacts before the predictor starts. |
| `storageUri` | The model artifact location used by KServe built-in runtimes. |
| Custom predictor | A user-owned serving container that follows KServe's model server contract. |
| Host header | The HTTP header often required by KServe ingress or gateway routing. |

## GPU Terms

| Term | Meaning in this tutorial |
|---|---|
| NVIDIA Container Toolkit | Host/runtime support that lets containers use NVIDIA GPUs. |
| GPU Operator | Kubernetes operator that can configure NVIDIA GPU support on clusters that use the operator. The local k3s path in this tutorial installs the NVIDIA device plugin directly instead. |
| Device plugin | Kubernetes integration that advertises GPU resources such as `nvidia.com/gpu`. |
| `nvidia.com/gpu` | The Kubernetes extended resource requested by GPU pods. |
| CUDA image | A container image with CUDA runtime libraries. |
| GPU-aware component | A KFP component that requests GPU resources and uses a GPU-capable image. |

## Cloud and CI/CD Terms

| Term | Meaning in this tutorial |
|---|---|
| Registry | A container image store reachable by the cluster. Local k3s chapters use host Docker images; `kind` fallback chapters use image loading; cloud chapters use a registry. |
| Overlay | Provider-specific configuration layered over provider-neutral pipeline code. |
| Image pull secret | Kubernetes Secret that lets the cluster pull private images. |
| Workload identity | Cloud-native identity for pods. It can replace static object-storage credentials in mature setups. |
| GitOps-style promotion | Representing deployment or model promotion state as files in Git. |
| Guarded workflow | A CI/CD job that requires manual approval before spending cloud/GPU resources or submitting runs. |

## Orchestration Alternatives

| Term | Meaning in this tutorial |
|---|---|
| Flyte | Optional workflow orchestrator comparison after the Kubeflow path. |
| Airflow | Scheduled DAG orchestrator often used for data engineering. |
| Dagster | Asset-centric orchestrator for data platform workflows. |
| Argo Workflows | Lower-level Kubernetes-native workflow engine. KFP uses Kubernetes workflow concepts under the hood. |

## Reading Tip

When debugging, translate the symptom to the layer that owns it:

| Symptom | Usually start with |
|---|---|
| pipeline does not compile | KFP component annotations and imports |
| pipeline task failed | KFP task logs, then Kubernetes pod logs |
| pod is pending | Kubernetes scheduling, resources, taints, image pulls |
| model artifact missing | object-storage prefix, credentials, run ID |
| serving request fails | service, route, host header, model server logs |
| GPU run does not start | node GPU allocatable, device plugin, pod resource requests |
