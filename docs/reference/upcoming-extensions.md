# Upcoming Extensions

This page records larger optional extensions that are intentionally not part of the current core path.

The current tutorial already covers local Kubernetes, standalone Kubeflow Pipelines, local ML workflow, artifacts, tracking, serving, GPU, cloud expansion, CI/CD, capstone, Flyte, and KServe. The extensions below are useful next steps, but they should stay separate until the existing tutorial has been followed end to end.

## Full Kubeflow Platform Operations

Goal:

Move from standalone Kubeflow Pipelines to a fuller Kubeflow platform experience.

Why it matters:

Standalone KFP is enough to learn pipelines, artifacts, and Kubernetes-native execution. A shared platform introduces more concerns:

- central dashboard
- profiles and namespaces
- multi-user isolation
- notebooks or web IDEs
- authentication
- authorization
- component integration
- platform lifecycle and upgrades

Suggested chapter shape:

```text
why standalone KFP was used first
  -> install or inspect a full Kubeflow distribution
  -> create a user profile
  -> compare profile namespace isolation with the tutorial namespace
  -> inspect dashboard, notebooks, and KFP access
  -> map tutorial workloads into the multi-user model
  -> document cleanup and operational tradeoffs
```

Acceptance criteria for a future extension:

- the reader can explain what full Kubeflow adds beyond standalone KFP
- profile and namespace behavior is concrete
- authentication and authorization are described without turning the chapter into an enterprise IAM tutorial
- notebooks remain optional and do not replace the script/container/pipeline core path
- cleanup is explicit

Do not add this to the core path unless multiple users or platform operations become a primary tutorial goal.

## Observability and Model Monitoring

Goal:

Add an operations-focused extension for repeated runs, serving health, and model behavior over time.

Why it matters:

The current tutorial teaches debugging with `kubectl`, logs, events, smoke tests, metrics files, MLflow, and explicit reports. A longer-lived platform needs broader operational visibility:

- cluster health
- pipeline run health
- pod resource usage
- endpoint latency and errors
- model request and response shape
- data drift
- prediction drift
- alerting
- incident review

Suggested chapter shape:

```text
define observability goals
  -> add basic cluster metrics
  -> add service metrics for the model endpoint
  -> record prediction payload summaries
  -> compare metrics, logs, and traces
  -> add a simple drift report
  -> define alert thresholds for tutorial services
  -> document cleanup and cost
```

Possible tools:

- Prometheus for metrics
- Grafana for dashboards
- OpenTelemetry for traces and logs
- Evidently or similar tools for drift reports
- KServe inference observability features for the optional KServe path

Acceptance criteria for a future extension:

- observability is tied to tutorial services and runs, not generic dashboard setup
- the reader can debug a failed run, a slow endpoint, and a drift warning
- monitoring does not require cloud resources by default
- any always-on components have explicit cleanup steps

Do not add this before the tutorial has a verified end-to-end capstone run. Observability is most useful once there is something stable to operate repeatedly.

## Extension Policy

Add an extension when it meets all of these conditions:

- it builds on a completed core workflow
- it teaches one clear platform concern
- it has concrete local verification steps
- it does not require expensive resources by default
- it can be skipped without breaking later chapters
- it has cleanup instructions

Keep extensions out of the core path unless they are required for the minimum local MLOps workflow.
