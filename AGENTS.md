# Repository Guidance

## Working in This Repo

- Keep changes minimal and targeted to the task.
- Prefer the existing repo conventions over introducing new patterns.
- Use `uv` for dependency management and local commands.
- Keep this repository focused on Kubeflow. Do not import tutorial-specific material from other projects unless it is clearly generic.

## Validation

- Run the relevant `uv run` checks for any files you touch.
- Before claiming a cleanup is done, check `git diff --check` for whitespace and patch issues.
