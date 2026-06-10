"""Image classification training pipeline."""

from kfp.compiler.compiler import Compiler
from kfp.dsl.pipeline_context import pipeline

from components.evaluate_model import evaluate_model
from components.train_model import train_model


@pipeline(name="image-classification-local")
def image_classification_pipeline(  # noqa: PLR0913, PLR0917
    epochs: int = 2,
    learning_rate: float = 1e-3,
    seed: int = 42,
    n_train: int = 256,
    n_val: int = 64,
    batch_size: int = 32,
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

    evaluate_model(
        model=train_task.outputs["model"],
        seed=seed,
        n_train=n_train,
        n_val=n_val,
        batch_size=batch_size,
    )


if __name__ == "__main__":
    Compiler().compile(
        pipeline_func=image_classification_pipeline,
        package_path="compiled/image_classification_pipeline.yaml",
    )
