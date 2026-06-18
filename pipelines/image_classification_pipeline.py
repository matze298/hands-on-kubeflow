"""Image classification training pipeline."""

import sys
from pathlib import Path

from kfp.compiler.compiler import Compiler
from kfp.dsl.pipeline_context import pipeline
from kfp.dsl.tasks_group import If

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from components.evaluate_model import evaluate_model
from components.promote_model import promote_model, read_accuracy
from components.train_model import train_model


@pipeline(name="image-classification-local")
def image_classification_pipeline(  # noqa: PLR0913, PLR0917
    epochs: int = 2,
    learning_rate: float = 1e-3,
    seed: int = 42,
    n_train: int = 256,
    n_val: int = 64,
    batch_size: int = 32,
    min_accuracy: float = 0.8,
) -> None:
    """Define the local image classification pipeline."""
    train_task = train_model(
        epochs=epochs,
        learning_rate=learning_rate,
        seed=seed,
        n_train=n_train,
        n_val=n_val,
        batch_size=batch_size,
    )

    evaluate_task = evaluate_model(
        model=train_task.outputs["model"],
        seed=seed,
        n_train=n_train,
        n_val=n_val,
        batch_size=batch_size,
    )

    accuracy_task = read_accuracy(metrics=evaluate_task.outputs["metrics_artifact"])

    with If(accuracy_task.output >= min_accuracy):
        promote_model(model=train_task.outputs["model"], accuracy=accuracy_task.output, min_accuracy=min_accuracy)


if __name__ == "__main__":
    Compiler().compile(
        pipeline_func=image_classification_pipeline,
        package_path="compiled/image_classification_pipeline.yaml",
    )
