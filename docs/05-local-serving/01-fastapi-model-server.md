# FastAPI Model Server

This page creates a small FastAPI application that loads a trained model and exposes prediction endpoints.

## What You Will Build

You will create:

```text
src/kubeflow_by_doing/serve.py
src/kubeflow_by_doing/client.py
```

The server exposes:

```text
GET  /healthz
POST /predict
```

The client sends a tiny JSON request and prints the prediction.

## Why This Matters

Before using Kubernetes or KServe, the model should be servable as a normal HTTP application.

This gives us a simple development loop:

```text
load model locally
  ↓
start FastAPI
  ↓
send request
  ↓
verify prediction
  ↓
containerize
  ↓
deploy to Kubernetes
```

If serving fails locally, Kubernetes will not make it easier.

## Add Dependencies

Add FastAPI and Uvicorn:

```bash
uv add fastapi uvicorn pydantic
```

## Request and Response Shape

The model in Chapter 3 expects a single-channel image tensor.

For serving, we use a simple JSON payload:

```json
{
  "pixels": [[0.1, 0.2], [0.3, 0.4]]
}
```

The response shape is:

```json
{
  "class_id": 1,
  "confidence": 0.83
}
```

## Create `serve.py`

Create `src/kubeflow_by_doing/serve.py`:

```python
from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated

import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from kubeflow_by_doing.model import TinyImageClassifier


class PredictionRequest(BaseModel):
    pixels: Annotated[
        list[list[float]],
        Field(description="Single-channel image pixels as a 2D array."),
    ]


class PredictionResponse(BaseModel):
    class_id: int
    confidence: float


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_path: str


class ModelServer:
    def __init__(self, model_path: Path, device: str = "cpu") -> None:
        self.model_path = model_path
        self.device = torch.device(device)
        self.model: TinyImageClassifier | None = None
        self.image_size: int | None = None
        self.n_classes: int | None = None

    def load(self) -> None:
        if not self.model_path.exists():
            raise FileNotFoundError(f"model file does not exist: {self.model_path}")

        checkpoint = torch.load(self.model_path, map_location=self.device)
        self.image_size = int(checkpoint["image_size"])
        self.n_classes = int(checkpoint["n_classes"])

        model = TinyImageClassifier(
            image_size=self.image_size,
            n_classes=self.n_classes,
        ).to(self.device)
        model.load_state_dict(checkpoint["model_state_dict"])
        model.eval()

        self.model = model

    def predict(self, pixels: list[list[float]]) -> PredictionResponse:
        if self.model is None or self.image_size is None:
            raise RuntimeError("model is not loaded")

        tensor = torch.tensor(pixels, dtype=torch.float32)

        if tensor.ndim != 2:
            raise ValueError("pixels must be a 2D array")

        if tensor.shape != (self.image_size, self.image_size):
            raise ValueError(f"expected image shape {(self.image_size, self.image_size)}, got {tuple(tensor.shape)}")

        x = tensor.unsqueeze(0).unsqueeze(0).to(self.device)

        with torch.no_grad():
            logits = self.model(x)
            probabilities = torch.softmax(logits, dim=1)
            confidence, class_id = torch.max(probabilities, dim=1)

        return PredictionResponse(
            class_id=int(class_id.item()),
            confidence=float(confidence.item()),
        )


def create_app() -> FastAPI:
    model_path = Path(os.environ.get("KBD_MODEL_PATH", "outputs/local-train/model.pt"))
    device = os.environ.get("KBD_SERVE_DEVICE", "cpu")

    server = ModelServer(model_path=model_path, device=device)

    app = FastAPI(title="Kubeflow by Doing Model Server")

    @app.on_event("startup")
    def load_model() -> None:
        server.load()

    @app.get("/healthz", response_model=HealthResponse)
    def healthz() -> HealthResponse:
        return HealthResponse(
            status="ok",
            model_loaded=server.model is not None,
            model_path=str(server.model_path),
        )

    @app.post("/predict", response_model=PredictionResponse)
    def predict(request: PredictionRequest) -> PredictionResponse:
        try:
            return server.predict(request.pixels)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    return app


app = create_app()
```

!!! note

    `@app.on_event("startup")` is simple and readable for a first tutorial server. Codex can later modernize this to FastAPI lifespan handlers if desired.

## Create `client.py`

Create `src/kubeflow_by_doing/client.py`:

```python
from __future__ import annotations

import json
from pathlib import Path
import urllib.request

import typer


app = typer.Typer(no_args_is_help=True)


@app.command()
def predict(
    endpoint: str = typer.Option("http://localhost:8000/predict"),
    image_size: int = typer.Option(16),
) -> None:
    pixels = [[0.75 for _ in range(image_size)] for _ in range(image_size)]
    payload = json.dumps({"pixels": pixels}).encode("utf-8")

    request = urllib.request.Request(
        endpoint,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=10) as response:
        body = response.read().decode("utf-8")

    typer.echo(body)


@app.command()
def predict_from_file(
    pixels_path: Path,
    endpoint: str = typer.Option("http://localhost:8000/predict"),
) -> None:
    payload = pixels_path.read_text(encoding="utf-8").encode("utf-8")

    request = urllib.request.Request(
        endpoint,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=10) as response:
        body = response.read().decode("utf-8")

    typer.echo(body)


if __name__ == "__main__":
    app()
```

## Add a CLI Entry Point

Update `pyproject.toml`:

```toml
[project.scripts]
kbd = "kubeflow_by_doing.cli:app"
kbd-client = "kubeflow_by_doing.client:app"
```

If `[project.scripts]` already exists, add only the new `kbd-client` line.

Then sync:

```bash
uv sync
```

## Train a Local Model

If you do not already have a local model:

```bash
mkdir -p outputs/local-train

uv run kbd train-model \
  --output-dir outputs/local-train \
  --epochs 2 \
  --learning-rate 0.001 \
  --seed 42 \
  --device cpu
```

Verify:

```bash
ls -lh outputs/local-train/model.pt
```

## Start the Server Locally

```bash
KBD_MODEL_PATH=outputs/local-train/model.pt \
KBD_SERVE_DEVICE=cpu \
uv run uvicorn kubeflow_by_doing.serve:app --host 0.0.0.0 --port 8000
```

## Check Health

In another terminal:

```bash
curl http://localhost:8000/healthz
```

Expected shape:

```json
{
  "status": "ok",
  "model_loaded": true,
  "model_path": "outputs/local-train/model.pt"
}
```

## Send a Prediction

Use the client:

```bash
uv run kbd-client predict --endpoint http://localhost:8000/predict --image-size 16
```

Or use Python:

```bash
uv run python - <<'PY'
import json
import urllib.request

pixels = [[0.75 for _ in range(16)] for _ in range(16)]
payload = json.dumps({"pixels": pixels}).encode("utf-8")

request = urllib.request.Request(
    "http://localhost:8000/predict",
    data=payload,
    headers={"Content-Type": "application/json"},
    method="POST",
)

with urllib.request.urlopen(request, timeout=10) as response:
    print(response.read().decode("utf-8"))
PY
```

Expected shape:

```json
{
  "class_id": 1,
  "confidence": 0.8
}
```

Exact values can differ.

## Common Problems

### `model file does not exist`

Check:

```bash
ls -lh outputs/local-train/model.pt
```

Then restart the server with the correct path.

### Shape mismatch

The request image must match the model's `image_size`, usually `16 x 16`.

### Import error for FastAPI or Uvicorn

Run:

```bash
uv add fastapi uvicorn pydantic
uv sync
```

## Cleanup

Stop the server with `Ctrl+C`.

Local model outputs can be removed with:

```bash
rm -rf outputs/local-train
```

## Acceptance Criteria

You are done when:

- `serve.py` exists
- `client.py` exists
- `uv run uvicorn kubeflow_by_doing.serve:app ...` starts successfully
- `GET /healthz` returns `model_loaded: true`
- `POST /predict` returns a class ID and confidence
- `uv run kbd-client predict ...` works

## References

- [FastAPI documentation](https://fastapi.tiangolo.com/)
- [Uvicorn documentation](https://www.uvicorn.org/)
- [Pydantic documentation](https://docs.pydantic.dev/)

## Next Step

Continue with [Containerize Serving](02-containerize-serving.md).
