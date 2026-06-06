"""Submission script for the hello-pipeline."""

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from kfp import compiler
from kfp.client import Client

if TYPE_CHECKING:
    from kfp.client.client import RunPipelineResult

from pipelines.hello_pipeline import hello_pipeline

_LOGGER = logging.getLogger(name=__name__)

PIPELINE_PACKAGE = Path("compiled/hello_pipeline.yaml")


def main() -> None:
    """Submits a compiled pipeline to KubeFlow via the Python API."""
    PIPELINE_PACKAGE.parent.mkdir(parents=True, exist_ok=True)

    compiler.Compiler().compile(
        pipeline_func=hello_pipeline,
        package_path=str(PIPELINE_PACKAGE),
    )

    client = Client(host="http://localhost:8888")

    run: RunPipelineResult = client.create_run_from_pipeline_package(
        pipeline_file=str(PIPELINE_PACKAGE),
        arguments={"name": "submitted-from-python"},
        run_name="hello-pipeline-from-python",
    )

    _LOGGER.info(f"submitted run_id={run.run_id}")


if __name__ == "__main__":
    main()
