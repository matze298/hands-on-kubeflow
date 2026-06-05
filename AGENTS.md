# Repository Guidance

## Working in This Repo

- Keep changes minimal and targeted to the task.
- Prefer the existing repo conventions over introducing new patterns.
- Use `uv` for dependency management and local commands.
- Keep this repository focused on Kubeflow. Do not import tutorial-specific material from other projects unless it is clearly generic.
- Treat the tutorial as build-along content: prose, commands, and repo state should agree.

## Chapter Workflow

Use this workflow for new chapters or chapter revisions:

1. Start with the current tutorial map:
   - `README.md`
   - `docs/index.md`
   - `mkdocs.yml`
   - the adjacent chapters in the same section
2. Ask ChatGPT for the first complete draft when generating chapter prose.
3. Use Codex to refine and harden the draft:
   - tighten wording
   - align commands with the repo setup
   - check that the tutorial promise matches the actual files and scripts
   - integrate concrete code, manifest, and test contents into the chapter when they are introduced
4. Keep edits scoped to the chapter and the files it directly depends on.
5. Ask questions if you need clarification.
6. Update `docs/index.md` and `mkdocs.yml` together when chapter order, names, or status labels change.
7. Keep the tutorial local-first and Kubeflow-focused. Expansion chapters should stay clearly separated from the core path.

## Chapter Standards

- Prefer concise, practical prose over long theory sections.
- This repository is docs-first. Readers are expected to create implementation files as they work through the chapters.
- When a chapter introduces code, prefer to show the concrete file contents inline in Markdown and direct readers to create the files in tracked repository paths.
- Treat checked-in implementation files, when they exist, as reference implementations created while following the tutorial, not as a requirement that every chapter's target files already exist ahead of time.
- When docs show manifest, config, or YAML contents inline, direct readers to create the file in a tracked repository path such as `infra/`; do not send them to `/tmp` or other ephemeral directories.
- Add inline comments to code or YAML snippets only when a concept, field, or command appears for the first time in the tutorial flow; avoid re-explaining repeated structure in later chapters.
- Avoid notebooks in the core path. Prefer scripts, containers, and pipelines.
- Use `uv`, `ruff`, `ty`, `pytest`, and `mkdocs-material` as the default tooling vocabulary.
- When a chapter introduces commands, verify they work from the repo root and match the bootstrap flow.
- If a command writes into a repository path, include the required `mkdir -p` step unless an earlier chapter in the same flow has already established that path as a prerequisite.
- If a chapter claims something exists, check that the repository actually contains it.
- If a chapter is only specifying a target implementation, say so explicitly.

## Validation

- Run the relevant `uv run` checks for any files you touch.
- Before claiming a cleanup is done, check `git diff --check` for whitespace and patch issues.
- For docs changes, run `uv run mkdocs build --strict` or explain why a narrower validation was the right substitute before handing the work back.
- When a chapter affects navigation or course structure, verify the links and section order against `docs/index.md` and `mkdocs.yml`.

## Local Setup Notes

- `./setup.py` is the bootstrap entrypoint.
- `.envrc` should activate the local venv when present.
- `uv.lock` should be created on first setup if it does not already exist.
