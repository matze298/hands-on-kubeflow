"""Refactored TinyML pipeline."""

import sys
from pathlib import Path

from kfp import compiler
from kfp.dsl.pipeline_context import pipeline

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from components.evaluate_model_tiny import evaluate_model
from components.generate_dataset import generate_dataset
from components.train_model_tiny import train_model


@pipeline(name="tiny-ml-pipeline")
def tiny_ml_pipeline(
    n_samples: int = 100,
    learning_rate: float = 0.01,
) -> None:
    """Defines the TinyML pipeline."""
    dataset_task = generate_dataset(n_samples=n_samples)
    model_task = train_model(
        dataset=dataset_task.outputs["dataset"],
        learning_rate=learning_rate,
    )
    evaluate_model(model=model_task.outputs["model"])


if __name__ == "__main__":
    compiler.Compiler().compile(
        pipeline_func=tiny_ml_pipeline,
        package_path="compiled/tiny_ml_pipeline_refactored.yaml",
    )
