"""Container component for evaluating a model."""

from kfp.dsl import Input, Model, OutputPath
from kfp.dsl.container_component_decorator import container_component
from kfp.dsl.structures import ContainerSpec


@container_component
def evaluate_model(  # noqa: PLR0913, PLR0917
    model: Input[Model],
    metrics_artifact: OutputPath("Dataset"),  # ty: ignore[invalid-type-form]
    seed: int = 42,
    n_train: int = 256,
    n_val: int = 64,
    batch_size: int = 32,
) -> ContainerSpec:
    """Container component for evaluating a model.

    Returns:
        ContainerSpec defining the evaluation stage.
    """
    return ContainerSpec(
        image="kubeflow-by-doing/train:local",
        args=[  # ty: ignore[invalid-argument-type]
            "evaluate-model",
            "--model-dir",
            model.path,
            "--metrics-path",
            metrics_artifact,
            "--seed",
            seed,
            "--device",
            "cuda",
            "--n-train",
            n_train,
            "--n-val",
            n_val,
            "--batch-size",
            batch_size,
        ],
    )
