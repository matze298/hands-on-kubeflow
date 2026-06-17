"""GPU image classification training pipeline."""

import sys
from pathlib import Path

from kfp.compiler.compiler import Compiler
from kfp.dsl.pipeline_context import pipeline

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from components.evaluate_model import evaluate_model
from components.train_model_gpu import train_model_gpu


@pipeline(name="image-classification-gpu")
def image_classification_gpu_pipeline(  # noqa: PLR0913, PLR0917
    epochs: int = 2,
    learning_rate: float = 1e-3,
    seed: int = 42,
    n_train: int = 256,
    n_val: int = 64,
    batch_size: int = 32,
) -> None:
    """Define the GPU image classification pipeline."""
    train_task = train_model_gpu(
        epochs=epochs,
        learning_rate=learning_rate,
        seed=seed,
        n_train=n_train,
        n_val=n_val,
        batch_size=batch_size,
    )
    train_task.set_accelerator_type("nvidia.com/gpu")
    train_task.set_accelerator_limit(1)
    train_task.set_cpu_request("2")
    train_task.set_memory_request("4Gi")
    train_task.set_memory_limit("8Gi")

    evaluate_model(
        model=train_task.outputs["model"],
        seed=seed,
        n_train=n_train,
        n_val=n_val,
        batch_size=batch_size,
    )


if __name__ == "__main__":
    Compiler().compile(
        pipeline_func=image_classification_gpu_pipeline,
        package_path="compiled/image_classification_gpu_pipeline.yaml",
    )
