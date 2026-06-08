"""CLI layer calling the model training and evaluation."""

from pathlib import Path

import typer
from rich import print as rprint

from kubeflow_by_doing.evaluate import evaluate
from kubeflow_by_doing.train import train

app = typer.Typer(no_args_is_help=True, help="Local-first Kubeflow tutorial CLI.")


@app.command()
def train_model(  # noqa: PLR0913, PLR0917
    output_dir: str = typer.Option(..., help="Directory for model artifacts."),
    epochs: int = typer.Option(2, help="Number of training epochs."),
    learning_rate: float = typer.Option(1e-3, help="Optimizer learning rate."),
    seed: int = typer.Option(42, help="Random seed."),
    device: str = typer.Option("auto", help="Device: auto, cpu, or cuda."),
    n_train: int = typer.Option(256, help="Number of synthetic training samples."),
    n_val: int = typer.Option(64, help="Number of synthetic validation samples."),
    batch_size: int = typer.Option(32, help="Batch size."),
) -> None:
    """Trains a model."""
    rprint(
        train(
            output_dir=Path(output_dir),
            epochs=epochs,
            learning_rate=learning_rate,
            seed=seed,
            device=device,
            n_train=n_train,
            n_val=n_val,
            batch_size=batch_size,
        )
    )


@app.command()
def evaluate_model(  # noqa: PLR0913, PLR0917
    model_dir: str = typer.Option(..., help="Directory containing model.pt."),
    metrics_path: str = typer.Option(..., help="Path to write metrics JSON."),
    seed: int = typer.Option(42, help="Random seed."),
    device: str = typer.Option("auto", help="Device: auto, cpu, or cuda."),
    n_train: int = typer.Option(256, help="Number of synthetic training samples."),
    n_val: int = typer.Option(64, help="Number of synthetic validation samples."),
    batch_size: int = typer.Option(32, help="Batch size."),
) -> None:
    """Evaluates a model."""
    rprint(
        evaluate(
            model_dir=Path(model_dir),
            metrics_path=Path(metrics_path),
            seed=seed,
            device=device,
            n_train=n_train,
            n_val=n_val,
            batch_size=batch_size,
        )
    )


if __name__ == "__main__":
    app()
