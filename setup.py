#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = [
#   "typer>=0.12.5",
# ]
# ///
"""Bootstrap local development for this repository."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import typer

ROOT = Path(__file__).resolve().parent
VENV_DIR = ROOT / ".venv"


def _run(cmd: list[str], *, env: dict[str, str] | None = None) -> None:
    subprocess.run(cmd, cwd=ROOT, check=True, env=env)


def _project_env() -> dict[str, str]:
    """Return an environment that targets the repository's project venv.

    `uv run --script` injects a temporary `VIRTUAL_ENV` for the script's own
    execution environment. We remove it before spawning other `uv` commands so
    they resolve against this repository's `.venv` instead of that temporary
    script environment.
    """
    env = os.environ.copy()
    env.pop("VIRTUAL_ENV", None)
    return env


def ensure_venv() -> None:
    """Create the project virtual environment if it does not exist."""
    if not VENV_DIR.exists():
        _run(["uv", "venv"], env=_project_env())


def ensure_lockfile(lock_path: Path = ROOT / "uv.lock") -> None:
    """Create uv.lock if it does not exist."""
    if not lock_path.exists():
        _run(["uv", "lock"], env=_project_env())


def build_app() -> typer.Typer:
    """Build the Typer CLI used after the venv is available.

    Returns:
        A Typer application with the bootstrap subcommands.
    """
    app = typer.Typer(
        add_completion=False,
        help="Bootstrap and maintain the local development environment.",
        no_args_is_help=False,
    )

    @app.command()
    def sync() -> None:
        """Sync the environment from uv.lock."""
        _run(["uv", "sync", "--all-groups", "--frozen"], env=_project_env())

    @app.command()
    def hooks() -> None:
        """Install prek Git hooks and prepare hook environments."""
        _run(["uv", "run", "prek", "install", "--prepare-hooks"], env=_project_env())

    @app.command(name="all")
    def setup_all() -> None:
        """Run the full local setup."""
        ensure_venv()
        ensure_lockfile()
        sync()
        hooks()

    @app.callback(invoke_without_command=True)
    def main(ctx: typer.Context) -> None:
        if ctx.invoked_subcommand is None:
            setup_all()

    return app


def main() -> None:
    """Entry point for the bootstrap script."""
    app = build_app()
    app()


if __name__ == "__main__":
    main()
