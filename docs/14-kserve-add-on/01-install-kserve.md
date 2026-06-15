# Install KServe

This page installs KServe into the local `MicroK8s` cluster.

The install is optional and separate from the core path. Do not add it until the Chapter 5 serving workflow and Chapter 10 capstone are clear.

## What You Will Build

You will create:

```text
infra/kserve/
└── README.md
```

and install KServe Standard mode into:

```text
kserve
```

## Prerequisites

Use the `MicroK8s` context:

```bash
kubectl config use-context microk8s
kubectl config current-context
kubectl get nodes -o wide
```

KServe 0.18 requires Kubernetes 1.32 or newer. Check your server version:

```bash
kubectl version --output=json
```

If your local `MicroK8s` version is older than the KServe requirement, stop here and keep the KServe chapter as reading material until you upgrade the local cluster. Do not break the working core tutorial just to force this optional add-on.

You also need:

```bash
helm version
kubectl get namespace kubeflow-by-doing
```

## Create the KServe Folder

```bash
mkdir -p infra/kserve
```

Create `infra/kserve/README.md`:

```markdown
# KServe Add-On

This folder contains optional KServe manifests for the local tutorial cluster.

The core tutorial uses FastAPI plus normal Kubernetes Deployments first. KServe is an optional serving platform layer used after the core workflow is understood.
```

## Choose Standard Mode

KServe has multiple deployment modes. This tutorial uses Standard mode because it keeps the generated resources close to normal Kubernetes concepts:

```text
InferenceService
  ↓
Deployment
  ↓
Service
  ↓
Ingress or Gateway API route
```

That is easier to debug locally than adding Knative serverless behavior at the same time.

## Install with the Pinned Quickstart Script

For this optional local chapter, use the pinned KServe quickstart script:

```bash
export KSERVE_VERSION=v0.18.0

curl -fsSL "https://github.com/kserve/kserve/releases/download/${KSERVE_VERSION}/kserve-standard-mode-full-install-with-manifests.sh" | bash
```

This is a local tutorial shortcut. For a shared or production cluster, use the KServe administrator guide and review every dependency explicitly before applying it.

## Verify the Install

Check the controller namespace:

```bash
kubectl get pods -n kserve
kubectl get svc -n kserve
```

Check the CRDs:

```bash
kubectl get crd | grep serving.kserve.io
```

Expected shape:

```text
inferenceservices.serving.kserve.io
servingruntimes.serving.kserve.io
clusterservingruntimes.serving.kserve.io
```

Check the default runtimes:

```bash
kubectl get clusterservingruntime
```

Look for runtimes such as:

```text
kserve-sklearnserver
kserve-mlserver
kserve-tritonserver
```

Runtime names can change by KServe version. The next page uses the sklearn runtime, so make sure a sklearn-compatible runtime exists before continuing.

## Record the Installed Version

Add a short note to `infra/kserve/README.md` after installation:

```markdown
## Local Version

- KServe: v0.18.0
- mode: Standard
- cluster: MicroK8s
```

This makes later debugging easier when the KServe docs or chart defaults change.

## Common Problems

### Kubernetes version is too old

KServe may install CRDs but fail to run controllers or webhooks correctly if the cluster version is below the documented requirement.

Fix:

- upgrade `MicroK8s`, or
- skip this optional chapter on the current machine.

### Webhook pods are not ready

Inspect:

```bash
kubectl -n kserve get pods
kubectl -n kserve describe pod <pod-name>
kubectl -n kserve logs <pod-name>
```

Most local failures are certificate-manager, webhook, or network-controller readiness issues.

### Existing KServe install conflicts

If you already experimented with KServe, check the existing mode before reinstalling:

```bash
kubectl get namespace kserve
kubectl get configmap -n kserve inferenceservice-config -o yaml
```

Do not mix an old Knative-mode install with this Standard-mode tutorial path.

## Acceptance Criteria

You are done when:

- `kubectl get pods -n kserve` shows running KServe pods
- `kubectl get crd | grep serving.kserve.io` shows KServe CRDs
- `kubectl get clusterservingruntime` shows the default serving runtimes
- `infra/kserve/README.md` records the local KServe version and mode

## References

- [KServe quickstart guide](https://kserve.github.io/website/docs/getting-started/quickstart-guide)
- [KServe Kubernetes deployment installation](https://kserve.github.io/website/docs/admin-guide/kubernetes-deployment)

## Next Step

Continue with [First InferenceService](02-first-inferenceservice.md).
