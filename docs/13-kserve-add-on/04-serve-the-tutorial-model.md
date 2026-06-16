# Serve the Tutorial Model

This page serves the tutorial model through KServe.

The built-in KServe runtimes are useful when your artifact format matches a supported model server. The tutorial's model checkpoint is a PyTorch checkpoint loaded by tutorial-owned Python code, so this page uses KServe's custom predictor pattern.

## What You Will Build

You will create:

```text
src/kubeflow_by_doing/kserve_model.py
Dockerfile.kserve
infra/kserve/tutorial-model.yaml
```

The KServe predictor will:

1. receive model files downloaded by the KServe storage initializer
2. load `/mnt/models/model.pt`
3. expose a KServe-compatible prediction endpoint
4. return the same class and confidence shape used by the FastAPI server

## Add the KServe SDK

Add the KServe Python package:

```bash
uv add kserve
```

This is only needed if you follow the optional KServe custom predictor path.

## Create the KServe Predictor

Create `src/kubeflow_by_doing/kserve_model.py`:

```python
from __future__ import annotations

from pathlib import Path
from typing import Any

import kserve
import torch
from kserve import Model, ModelServer

from kubeflow_by_doing.model import TinyImageClassifier


class TinyImageClassifierModel(Model):
    def __init__(self, name: str, model_dir: Path) -> None:
        super().__init__(name)
        self.name = name
        self.model_dir = model_dir
        self.model: TinyImageClassifier | None = None
        self.image_size: int | None = None
        self.ready = False
        self.load()

    def load(self) -> bool:
        model_path = self.model_dir / "model.pt"
        checkpoint = torch.load(model_path, map_location="cpu")
        self.image_size = int(checkpoint["image_size"])
        n_classes = int(checkpoint["n_classes"])

        model = TinyImageClassifier(image_size=self.image_size, n_classes=n_classes)
        model.load_state_dict(checkpoint["model_state_dict"])
        model.eval()

        self.model = model
        self.ready = True
        return self.ready

    async def predict(
        self,
        payload: dict[str, Any],
        headers: dict[str, str] | None = None,
        response_headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        if self.model is None or self.image_size is None:
            raise RuntimeError("model is not loaded")

        pixels = payload["instances"][0]["pixels"]
        tensor = torch.tensor(pixels, dtype=torch.float32)

        if tensor.shape != (self.image_size, self.image_size):
            raise ValueError(f"expected image shape {(self.image_size, self.image_size)}, got {tuple(tensor.shape)}")

        x = tensor.unsqueeze(0).unsqueeze(0)

        with torch.no_grad():
            logits = self.model(x)
            probabilities = torch.softmax(logits, dim=1)
            confidence, class_id = torch.max(probabilities, dim=1)

        return {
            "predictions": [
                {
                    "class_id": int(class_id.item()),
                    "confidence": float(confidence.item()),
                }
            ]
        }


if __name__ == "__main__":
    parser = kserve.model_server.parser
    args, _ = parser.parse_known_args()
    model_dir = Path("/mnt/models")
    model = TinyImageClassifierModel(name=args.model_name, model_dir=model_dir)
    ModelServer().start([model])
```

This file is separate from `serve.py` because it implements the KServe model-server contract. The Chapter 5 FastAPI app stays useful for transparent local serving.

## Create the KServe Image

Create `Dockerfile.kserve`:

```dockerfile
# syntax=docker/dockerfile:1.7

FROM python:3.14-slim

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    pip install --no-cache-dir uv \
    && uv sync --frozen --no-dev --no-install-project

COPY README.md ./
COPY src/ ./src/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

CMD ["uv", "run", "python", "-m", "kubeflow_by_doing.kserve_model", "--model_name=tutorial-image-classifier", "--http_port=8080"]
```

Build:

```bash
docker build -f Dockerfile.kserve -t kubeflow-by-doing/kserve:local .
```

Load into minikube:

```bash
minikube image load kubeflow-by-doing/kserve:local -p kubeflow-gpu
```

## Prepare a Model Artifact

Use a run that uploaded a model to MinIO. If you need one:

```bash
kubectl -n minio port-forward svc/minio 9000:9000
```

In another terminal:

```bash
export AWS_ACCESS_KEY_ID=minioadmin
export AWS_SECRET_ACCESS_KEY=minioadmin123
export AWS_DEFAULT_REGION=us-east-1
export KBD_S3_ENDPOINT_URL=http://localhost:9000
export KBD_ARTIFACT_BUCKET=kubeflow-by-doing
export RUN_ID=kserve-local-001

mkdir -p outputs/kserve-train

uv run kbd train-model \
  --output-dir outputs/kserve-train \
  --epochs 2 \
  --learning-rate 0.001 \
  --seed 42 \
  --device cpu \
  --run-id "$RUN_ID" \
  --upload-artifacts
```

Expected model prefix:

```text
s3://kubeflow-by-doing/runs/kserve-local-001/models/
```

## Create the Tutorial InferenceService

Create `infra/kserve/tutorial-model.yaml`:

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: tutorial-image-classifier
  namespace: kubeflow-by-doing
spec:
  predictor:
    serviceAccountName: kserve-minio-reader
    containers:
      - name: kserve-container
        image: kubeflow-by-doing/kserve:local
        imagePullPolicy: IfNotPresent
        env:
          - name: STORAGE_URI
            value: s3://kubeflow-by-doing/runs/kserve-local-001/models/
        ports:
          - name: http1
            containerPort: 8080
            protocol: TCP
        resources:
          requests:
            cpu: "500m"
            memory: "1Gi"
          limits:
            cpu: "1"
            memory: "2Gi"
```

KServe's storage initializer uses `STORAGE_URI` with custom predictors. It downloads the objects to `/mnt/models` before the model server starts.

Apply:

```bash
kubectl apply -f infra/kserve/tutorial-model.yaml
```

## Watch the Predictor

```bash
kubectl -n kubeflow-by-doing get inferenceservice tutorial-image-classifier
kubectl -n kubeflow-by-doing get pods | grep tutorial-image-classifier
```

Wait for:

```text
READY=True
```

## Send a Prediction

Create a request payload:

```bash
uv run python - <<'PY'
import json
from pathlib import Path

Path("outputs").mkdir(exist_ok=True)
pixels = [[0.75 for _ in range(16)] for _ in range(16)]
Path("outputs/kserve-input.json").write_text(json.dumps({"instances": [{"pixels": pixels}]}, indent=2), encoding="utf-8")
PY
```

Capture the service hostname:

```bash
export SERVICE_HOSTNAME="$(kubectl -n kubeflow-by-doing get inferenceservice tutorial-image-classifier -o jsonpath='{.status.url}' | cut -d / -f 3)"
echo "$SERVICE_HOSTNAME"
```

If local ingress is reachable on `localhost:80`:

```bash
curl -H "Host: ${SERVICE_HOSTNAME}" \
  -H "Content-Type: application/json" \
  --data @outputs/kserve-input.json \
  "http://localhost/v1/models/tutorial-image-classifier:predict"
```

If you need a port-forward, first find the generated service:

```bash
kubectl -n kubeflow-by-doing get svc | grep tutorial-image-classifier
```

Then:

```bash
kubectl -n kubeflow-by-doing port-forward svc/<tutorial-image-classifier-service-name> 8082:80
```

In another terminal:

```bash
curl -H "Host: ${SERVICE_HOSTNAME}" \
  -H "Content-Type: application/json" \
  --data @outputs/kserve-input.json \
  "http://localhost:8082/v1/models/tutorial-image-classifier:predict"
```

Expected shape:

```json
{
  "predictions": [
    {
      "class_id": 0,
      "confidence": 0.54
    }
  ]
}
```

The exact class and confidence are not important for this tutorial model. The platform check is that KServe loaded the model from object storage and routed a request to the custom predictor.

## Acceptance Criteria

You are done when:

- `Dockerfile.kserve` builds
- `kubeflow-by-doing/kserve:local` is available to minikube
- `tutorial-image-classifier` reaches `READY=True`
- the predictor reads model files from MinIO
- a prediction request returns `class_id` and `confidence`

## References

- [KServe custom predictor guide](https://kserve.github.io/website/docs/model-serving/predictive-inference/frameworks/custom-predictor)
- [KServe S3 storage provider](https://kserve.github.io/website/docs/model-serving/storage/providers/s3)

## Next Step

Continue with [Verify and Debug](05-verify-and-debug.md).
