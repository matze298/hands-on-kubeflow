"""Container component for GPU training."""

from kfp.dsl import Model, Output
from kfp.dsl.container_component_decorator import container_component
from kfp.dsl.structures import ContainerSpec


@container_component
def train_model_gpu(  # noqa: PLR0913, PLR0917
    model: Output[Model],
    epochs: int = 2,
    learning_rate: float = 1e-3,
    seed: int = 42,
    n_train: int = 256,
    n_val: int = 64,
    batch_size: int = 32,
) -> ContainerSpec:
    """Container component for GPU training.

    Returns:
        ContainerSpec defining the GPU training stage.
    """
    return ContainerSpec(
        image="kubeflow-by-doing/train-gpu:local",
        command=["uv", "run", "kbd"],
        args=[  # ty: ignore[invalid-argument-type]
            "train-model",
            "--output-dir",
            model.path,
            "--epochs",
            epochs,
            "--learning-rate",
            learning_rate,
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
