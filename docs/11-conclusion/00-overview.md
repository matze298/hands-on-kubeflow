# Conclusion and Future Reading

You now have the core workflow this tutorial set out to build:

```text
local Kubernetes
  ↓
Kubeflow Pipelines
  ↓
containerized training
  ↓
durable artifacts
  ↓
tracking and lineage
  ↓
promotion
  ↓
serving
  ↓
CI/CD and cloud mapping
```

The capstone is intentionally small, but the platform shape is real. You can now reason about what runs in Kubernetes, where artifacts live, how promotion decisions are made, how serving fits into the workflow, and what changes when the same design moves to a cloud provider.

This page points to the next topics worth studying. They are not required for the core tutorial. Treat them as future work.

## Topics

- [Serving and inference](#production-serving-with-kserve)
- [Lifecycle, tuning, and training](#model-lifecycle-with-kubeflow-hub-and-model-registry)
- [Scheduling and accelerators](#gpu-and-batch-scheduling-with-kueue)
- [Platform operations](#full-kubeflow-platform-operations)
- [Data systems](#data-versioning-and-reproducibility)
- [Observability and policy](#observability-monitoring-and-drift)
- [Deployment and applications](#gitops-controllers)

## How to Choose the Next Topic

Pick the next step based on the bottleneck you actually have:

| If you need... | Study next |
|---|---|
| production-grade model serving | KServe |
| inference-aware LLM traffic routing | AI gateways and Gateway API inference work |
| a real model lifecycle system | Kubeflow Hub / Model Registry |
| automated hyperparameter search | Katib |
| distributed training or LLM fine-tuning | Kubeflow Trainer |
| distributed Python services or non-KFP compute | Ray and KubeRay |
| quota-aware GPU scheduling | Kueue |
| flexible accelerator allocation or partitioned devices | Kubernetes Dynamic Resource Allocation |
| shared Kubeflow environments | full Kubeflow platform operations |
| AI platform compatibility across vendors | Kubernetes AI conformance |
| versioned datasets and reruns | data versioning and reproducibility |
| stronger dataset contracts | data quality frameworks |
| large-scale data preparation | Kubeflow Spark Operator |
| training/serving feature consistency | Feast |
| operational visibility | observability and monitoring |
| LLM traces, prompts, and retrieval telemetry | GenAI observability standards |
| supply-chain controls | image signing, provenance, and policy |
| production credential handling | secret management and identity |
| reconciled deployments | Argo CD or Flux |
| RAG or AI application workflows | GenAI application layer |

## Production Serving with KServe

Chapter 5 used a plain FastAPI `Deployment` and `Service` because that path is transparent and easy to debug.

The next serving step is KServe. KServe adds `InferenceService` resources, standardized model runtimes, rollout behavior, storage integration, and production-style inference protocols.

Study KServe when you need:

- standardized inference deployments
- canary or progressive rollout patterns
- scale-to-zero or autoscaling behavior
- reusable serving runtimes
- Open Inference or OpenAI-compatible protocols
- LLM serving with optimized runtimes such as vLLM

References:

- [KServe introduction](https://kserve.github.io/website/docs/intro)
- [KServe InferenceService documentation](https://kserve.github.io/website/docs/model-serving/predictive-inference/frameworks/overview)
- [KServe generative inference runtime overview](https://kserve.github.io/website/docs/model-serving/generative-inference/overview)
- [KServe installation guide](https://kserve.github.io/website/docs/admin-guide/kubernetes-deployment)

## AI Gateways and Inference-Aware Routing

KServe gives you a model-serving abstraction. High-throughput LLM serving adds another problem: the route to the model can matter as much as the model endpoint itself.

Modern inference systems may need routing that understands request cost, model placement, accelerator pressure, KV-cache locality, batching, streaming responses, and multi-model serving. This area is moving toward Kubernetes-native gateway standards and inference-specific extensions rather than one-off ingress rules.

Study AI gateways and inference-aware routing when you need:

- high-throughput LLM endpoints
- request routing based on inference capacity
- better GPU utilization for serving
- streaming-aware gateway behavior
- separation between application traffic policy and model runtime details
- a path from normal Gateway API concepts into AI-specific routing

References:

- [Gateway API Inference Extension](https://gateway-api-inference-extension.sigs.k8s.io/)
- [Kubernetes AI Gateway Working Group announcement](https://kubernetes.io/blog/2026/03/09/announcing-ai-gateway-wg/)
- [llm-d project](https://llm-d.ai/)
- [NVIDIA Dynamo Kubernetes deployment](https://docs.nvidia.com/dynamo/getting-started/kubernetes-deployment)

## Model Lifecycle with Kubeflow Hub and Model Registry

This tutorial records promotion and lineage explicitly in object storage. That is enough for learning the platform mechanics.

In a larger system, promoted models should be queryable through a model registry. Kubeflow now presents this area as Kubeflow Hub, which includes Model Registry and Model Catalog capabilities. Model Registry is the part that tracks model metadata, versions, artifacts, and serving-related information through APIs and UI workflows.

Study Kubeflow Hub / Model Registry when you need:

- a canonical list of model versions
- ownership and metadata around promoted models
- links between model artifacts, evaluation results, and serving endpoints
- integration between promotion and KServe deployment

References:

- [Kubeflow Hub overview](https://www.kubeflow.org/docs/components/hub/overview/)
- [Kubeflow Model Registry getting started](https://www.kubeflow.org/docs/components/model-registry/getting-started/)
- [Kubeflow Model Registry installation](https://www.kubeflow.org/docs/components/model-registry/installation/)
- [Kubeflow Hub architecture](https://www.kubeflow.org/docs/components/hub/reference/architecture/)

## Hyperparameter Tuning with Katib

Chapter 3 and Chapter 10 pass training parameters into pipelines manually.

Katib is the Kubeflow component for automated hyperparameter tuning, early stopping, and AutoML-style search. It can run trials as Kubernetes workloads and optimize metrics produced by training jobs.

Study Katib when you need:

- many training trials with different parameters
- objective metrics and search spaces
- early stopping
- random search, Bayesian optimization, Hyperband, or other algorithms
- tuning on top of Kubernetes-native training jobs

References:

- [Kubeflow Katib overview](https://www.kubeflow.org/docs/components/katib/overview/)
- [Katib getting started](https://www.kubeflow.org/docs/components/katib/getting-started/)
- [Katib architecture](https://www.kubeflow.org/docs/components/katib/reference/architecture/)
- [Katib algorithm configuration](https://www.kubeflow.org/docs/components/katib/user-guides/hp-tuning/configure-algorithm/)

## Distributed Training with Kubeflow Trainer

This tutorial keeps training small and mostly single-node. That is the right shape for learning KFP, artifacts, and promotion.

Kubeflow Trainer is the next step when training itself becomes the platform problem. It targets distributed AI workloads, including PyTorch, Hugging Face, DeepSpeed, JAX, XGBoost, and LLM fine-tuning patterns.

Study Kubeflow Trainer when you need:

- multi-node or multi-GPU training
- `TrainJob` APIs instead of ad-hoc training pods
- reusable training runtimes
- LLM fine-tuning on Kubernetes
- scheduling integration for large training jobs

References:

- [Kubeflow Trainer overview](https://www.kubeflow.org/docs/components/trainer/overview/)
- [Kubeflow Trainer getting started](https://www.kubeflow.org/docs/components/trainer/getting-started/)
- [Kubeflow Trainer built-in trainer overview](https://www.kubeflow.org/docs/components/trainer/user-guides/builtin-trainer/overview/)
- [Kubeflow Trainer local execution mode](https://www.kubeflow.org/docs/components/trainer/user-guides/local-execution-mode/overview/)

## Distributed Python and AI Services with Ray

Kubeflow Pipelines is the workflow orchestrator in this tutorial. Kubeflow Trainer is the Kubeflow-native direction for training jobs.

Ray is adjacent to that path. It is useful when the main problem is distributed Python execution, model-serving applications, reinforcement learning, batch inference, or custom distributed workloads that do not fit naturally into a KFP component graph.

Study Ray and KubeRay when you need:

- distributed Python tasks and actors
- custom distributed serving applications
- batch inference at scale
- reinforcement learning workloads
- an application framework that can run on Kubernetes but is not itself a Kubeflow component

References:

- [Ray on Kubernetes](https://docs.ray.io/en/latest/cluster/kubernetes/index.html)
- [KubeRay project repository](https://github.com/ray-project/kuberay)

## GPU and Batch Scheduling with Kueue

The tutorial uses direct Kubernetes resource requests such as `nvidia.com/gpu`.

That is enough for a single-user local cluster. It is not enough for a shared GPU platform where jobs must queue, respect quotas, and avoid starving other users.

Kueue is the Kubernetes-native project to study when batch scheduling becomes a platform concern.

Study Kueue when you need:

- queueing for expensive jobs
- quota-aware admission
- priority between workloads
- shared GPU capacity
- integration with training operators and batch workloads

References:

- [Kueue overview](https://kueue.sigs.k8s.io/docs/overview/)
- [Kueue concepts](https://kueue.sigs.k8s.io/docs/concepts/)
- [Kubeflow Trainer job scheduling](https://www.kubeflow.org/docs/components/trainer/operator-guides/job-scheduling/)

## Accelerator Allocation with Kubernetes DRA

Kueue decides when queued workloads should be admitted. Kubernetes Dynamic Resource Allocation is a lower-level Kubernetes mechanism for how workloads request specialized devices.

The tutorial uses `nvidia.com/gpu` because it is the simplest way to learn GPU scheduling. Shared production GPU platforms may need richer device selection: partitioned devices, topology-aware allocation, driver-specific attributes, and claims that describe what a workload needs instead of only asking for a raw GPU count.

Study DRA when you need:

- `ResourceClaim` or `ResourceClaimTemplate` based accelerator requests
- GPU partitioning or device attributes
- topology-aware accelerator placement
- a migration path beyond opaque extended resources
- platform-level accelerator policy across heterogeneous nodes

References:

- [Kubernetes v1.36 DRA update](https://kubernetes.io/blog/2026/05/07/kubernetes-v1-36-dra-136-updates/)
- [Kubernetes DRA task documentation](https://kubernetes.io/docs/tasks/configure-pod-container/assign-resources/allocate-devices-dra/)
- [NVIDIA DRA Driver for GPUs](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/dra-intro-install.html)

## Full Kubeflow Platform Operations

This tutorial installs standalone Kubeflow Pipelines first. That keeps the core workflow visible.

The full Kubeflow platform adds more platform concerns: central dashboard, profiles, multi-user isolation, notebooks, authentication, authorization, and component integration.

Study full Kubeflow platform operations when you need:

- multiple users or teams
- profile and namespace isolation
- shared notebooks or web IDEs
- dashboard-based platform workflows
- production authentication and authorization
- an integrated Kubeflow installation instead of standalone KFP

References:

- [Kubeflow Profiles and Namespaces](https://www.kubeflow.org/docs/components/central-dash/profiles/)
- [Kubeflow Pipelines multi-user isolation](https://www.kubeflow.org/docs/components/pipelines/operator-guides/multi-user/)
- [Kubeflow Notebooks](https://www.kubeflow.org/docs/components/notebooks/)
- [Kubeflow components](https://www.kubeflow.org/docs/components/)

## Kubernetes AI Platform Conformance

This tutorial teaches you how to reason about the pieces of an AI platform. In production, you may also need to evaluate whether a Kubernetes distribution or managed platform exposes the capabilities AI workloads expect.

The CNCF Certified Kubernetes AI Conformance Program is the community effort to define and validate common capabilities for AI workloads on Kubernetes. Treat it as a platform-evaluation topic, not as something you need for the local tutorial.

Study AI conformance when you need:

- a vendor-neutral way to compare AI-capable Kubernetes platforms
- portability expectations for AI workloads
- procurement or platform-readiness criteria
- a shared vocabulary for accelerator, scheduling, and workload support

References:

- [CNCF Certified Kubernetes AI Conformance Program announcement](https://www.cncf.io/announcements/2025/11/11/cncf-launches-certified-kubernetes-ai-conformance-program-to-standardize-ai-workloads-on-kubernetes/)

## Data Versioning and Reproducibility

This tutorial makes artifacts durable and records lineage. That answers where outputs live and how a run was produced.

The next reproducibility step is data versioning. A real platform should also answer which dataset version was used, whether reruns reuse cached outputs, and how immutable object-storage data is managed over time.

Study data versioning and reproducibility when you need:

- stable dataset versions
- repeatable reruns
- explicit cache behavior
- immutable object-storage inputs
- data snapshots across training, validation, and serving tests

References:

- [Kubeflow Pipelines caching](https://www.kubeflow.org/docs/components/pipelines/user-guides/core-functions/caching/)
- [Kubeflow Pipelines runs and recurring runs](https://www.kubeflow.org/docs/components/pipelines/concepts/run/)
- [DVC data files](https://dvc.org/doc/user-guide/project-structure/dvc-files)
- [DVC cloud versioning](https://dvc.org/doc/user-guide/data-management/cloud-versioning)
- [lakeFS project overview](https://docs.lakefs.io/latest/project/)

## Data Quality Frameworks

The capstone validates data explicitly with tutorial-owned code. That keeps the validation logic visible.

Larger systems often need reusable data contracts, richer validation reports, and checks that can be shared across ingestion, training, and batch-scoring jobs. Data quality frameworks are the next step once the validation logic becomes repeated or team-owned.

Study data quality frameworks when you need:

- schema checks for tabular data
- reusable expectations across datasets
- validation reports for failed pipeline runs
- checks that can run before training, evaluation, or batch inference
- a clearer contract between data producers and ML workloads

References:

- [Great Expectations validation documentation](https://docs.greatexpectations.io/docs/core/run_validations/)
- [Pandera documentation](https://pandera.readthedocs.io/en/stable/)
- [Pandera DataFrame schemas](https://pandera.readthedocs.io/en/latest/dataframe_schemas.html)

## Distributed Data Processing with Spark Operator

The tutorial keeps data preparation small enough to run in normal Python components.

That is intentional. Once data preparation becomes the bottleneck, the next platform question is not always a bigger training job. It may be a distributed data processing system that prepares datasets before KFP training starts.

Study Kubeflow Spark Operator when you need:

- large ETL or feature preparation jobs
- Spark workloads managed as Kubernetes resources
- data preparation that is too large for single-pod Python components
- a clean boundary between data processing and model training

References:

- [Kubeflow Spark Operator](https://www.kubeflow.org/docs/components/spark-operator/)
- [Kubeflow AI reference platform 26.03](https://www.kubeflow.org/docs/kubeflow-platform/releases/kubeflow-26.03/)

## Feature Stores with Feast

This tutorial uses synthetic and file-based data so the data path stays simple.

Production ML systems often need a stricter feature contract: the same feature definitions should be used for training and low-latency inference. Feast is the common open source feature-store project to study next.

Study Feast when you need:

- reusable feature definitions
- offline features for training
- online features for serving
- point-in-time-correct training data
- feature lineage and ownership

References:

- [Kubeflow Feast introduction](https://www.kubeflow.org/docs/ecosystem/feast/introduction/)
- [Feast documentation](https://docs.feast.dev/)
- [Feast getting started](https://docs.feast.dev/getting-started)

## Observability, Monitoring, and Drift

This tutorial teaches debugging through `kubectl`, logs, events, smoke tests, metrics files, and explicit reports.

Production systems need a broader view:

- cluster health
- pipeline health
- endpoint latency and error rates
- model input/output statistics
- data drift
- prediction drift
- alerting and incident workflows

Study observability after the capstone works and you need to operate it repeatedly.

References:

- [Kubernetes observability](https://kubernetes.io/docs/concepts/cluster-administration/observability/)
- [Prometheus getting started](https://prometheus.io/docs/tutorials/getting_started/)
- [OpenTelemetry with Kubernetes](https://opentelemetry.io/docs/platforms/kubernetes/)
- [OpenTelemetry Kubernetes getting started](https://opentelemetry.io/docs/platforms/kubernetes/getting-started/)
- [Evidently data drift documentation](https://docs.evidentlyai.com/metrics/preset_data_drift)

## GenAI Observability Standards

Normal service telemetry tells you whether an endpoint is healthy. GenAI applications also need visibility into prompts, tool calls, retrieval steps, model calls, token usage, streaming behavior, and evaluation results.

This area is moving toward OpenTelemetry-compatible conventions and instrumentation rather than one-off logging formats. Keep it separate from the core Kubeflow workflow until you actually build LLM or RAG applications.

Study GenAI observability standards when you need:

- traces across retrieval, model calls, and tool calls
- prompt and response evaluation workflows
- telemetry that can move between observability backends
- shared attributes for GenAI spans and metrics
- debugging for agentic or RAG applications

References:

- [OpenTelemetry GenAI semantic conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/)
- [OpenInference documentation](https://arize-ai.github.io/openinference/)
- [Phoenix documentation](https://arize.com/docs/phoenix)

## Supply Chain and Policy

Chapter 9 builds and tags images. That is the first CI/CD step.

Production platforms usually need stronger guarantees:

- signed container images
- image provenance
- SBOMs
- admission policies
- allowed registries
- required image digests
- vulnerability and dependency scanning

Study supply-chain hardening when images move from local development into shared or production clusters.

References:

- [Sigstore Cosign documentation](https://docs.sigstore.dev/cosign/)
- [Cosign container signing](https://docs.sigstore.dev/cosign/signing/signing_with_containers/)
- [SLSA provenance](https://slsa.dev/provenance)
- [Kyverno image verification](https://kyverno.io/docs/policy-types/cluster-policy/verify-images/overview/)
- [Kyverno ImageValidatingPolicy](https://kyverno.io/docs/policy-types/image-validating-policy/)

## Secret Management and Identity

The tutorial uses Kubernetes `Secret` objects and local generated manifests because they are easy to inspect while learning.

Production systems need a stronger model for credentials. Static generated YAML files do not scale well across teams, environments, or cloud providers. You should understand where secrets are stored, who can read them, how they are rotated, and whether workloads can use identity instead of long-lived access keys.

Study secret management and identity when you need:

- external secret managers
- secret rotation
- workload identity
- cloud IAM integration
- reduced use of static access keys
- clear RBAC around who can read credentials

References:

- [Kubernetes Secrets](https://kubernetes.io/docs/concepts/configuration/secret/)
- [External Secrets Operator](https://external-secrets.io/)
- [Kubernetes RBAC](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)
- [Kubernetes service accounts](https://kubernetes.io/docs/concepts/security/service-accounts/)

## GitOps Controllers

Chapter 9 represents promotion as a Git-tracked state change, but it does not require a GitOps controller.

The next step is to let a controller reconcile desired state from Git into the cluster. Argo CD and Flux are the two common projects to study.

Study GitOps controllers when you need:

- continuous reconciliation from Git
- environment-specific deployment state
- auditability for deployment changes
- rollback through Git history
- separation between CI and cluster deployment

References:

- [Argo CD getting started](https://argo-cd.readthedocs.io/en/stable/getting_started/)
- [Argo CD core concepts](https://argo-cd.readthedocs.io/en/stable/core_concepts/)
- [Flux documentation](https://fluxcd.io/docs/)
- [Flux getting started](https://fluxcd.io/flux/get-started/)

## GenAI Application Layer

KServe and Kubeflow Trainer cover important infrastructure for LLM serving and fine-tuning. They do not, by themselves, define the whole application layer.

If your next project is a retrieval-augmented generation application, the next questions are different:

- how documents are chunked and embedded
- which vector store or retrieval backend is used
- how retrieval quality is measured
- how generated answers are evaluated
- how prompts, models, and retrieval settings are versioned
- how safety checks and guardrails fit into the serving path

Treat this as adjacent to Kubeflow. Kubeflow can orchestrate training, evaluation, deployment, and infrastructure, but the RAG application logic usually lives in application frameworks and evaluation systems above the platform layer.

References:

- [KServe generative inference runtime overview](https://kserve.github.io/website/docs/model-serving/generative-inference/overview)
- [LangChain retrieval documentation](https://docs.langchain.com/oss/python/langchain/retrieval)
- [LangSmith RAG evaluation tutorial](https://docs.langchain.com/langsmith/evaluate-rag-tutorial)
- [LlamaIndex question-answering / RAG documentation](https://docs.llamaindex.ai/en/v0.10.34/use_cases/q_and_a/)

## Suggested Learning Order

A practical order after this tutorial is:

1. Run the capstone again from a clean checkout.
2. Move the capstone to one cloud provider.
3. Add KServe for production-style serving.
4. Add AI gateway and inference-aware routing only when serving traffic becomes a bottleneck.
5. Add Model Registry for model lifecycle metadata.
6. Add data versioning, data quality, distributed data processing, and reproducibility controls.
7. Add full Kubeflow platform operations if multiple users need the platform.
8. Add observability, GenAI telemetry, and drift checks.
9. Add secret management, identity, and supply-chain controls.
10. Add Katib, Trainer, Kueue, DRA, or Ray when training, accelerators, and distributed compute become bottlenecks.
11. Add Feast when feature reuse becomes a real data problem.
12. Check AI conformance only when evaluating a shared or managed AI platform.
13. Add GenAI/RAG application tooling only when the product requires it.

Do not add all of these at once. Each one introduces a new platform boundary.

## Final Checkpoint

You have finished the tutorial when you can explain:

- how a local training script becomes a containerized Kubeflow component
- how KFP runs map to Kubernetes workloads
- where artifacts, metrics, and lineage records live
- how model promotion changes serving behavior
- how GPU scheduling differs from CPU scheduling
- what changes when moving from local Kubernetes to a managed cloud cluster
- which advanced platform component solves which next problem

The important result is not the tiny model. The important result is that the workflow is no longer hidden inside a notebook or a local script. It is visible as containers, Kubernetes resources, pipeline steps, artifacts, and deployment state.
