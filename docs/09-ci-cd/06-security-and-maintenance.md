# Security and Maintenance

This page defines the minimum CI/CD safety rules for the tutorial.

## Why This Matters

CI/CD has access to valuable capabilities:

- pushing images
- submitting pipeline runs
- reading secrets
- creating pull requests
- deploying models
- triggering cloud cost

So CI/CD must be intentionally scoped.

## Rule 1: Do Not Put Secrets in Git

Do not commit:

```text
.env.cloud
.env.stackit
.kube/
*.generated.yaml with real secrets
registry credentials
object storage keys
KFP tokens
```

## Rule 2: Use Environments for Dangerous Actions

Use GitHub environments for:

```text
pipeline submission
GPU jobs
cloud deployments
promotion
```

Examples:

```text
kfp-dev
kfp-stackit
kfp-gpu
production
```

Add manual approvals for expensive or sensitive environments.

## Rule 3: Push Images Only from Trusted Events

Good:

```text
push to main
manual workflow_dispatch
release tag
```

Be careful with:

```text
pull_request from forks
```

Do not expose registry credentials to untrusted pull requests.

## Rule 4: Keep GPU Jobs Manual

GPU jobs can be expensive.

Keep GPU pipeline submission manual:

```yaml
workflow_dispatch:
```

and gate it with an environment approval.

## Rule 5: Prefer Short-Lived Credentials

Prefer:

- GitHub OIDC to cloud provider
- workload identity
- short-lived tokens
- environment-scoped secrets

Avoid long-lived static keys where possible.

For the tutorial, static credentials may be used in local examples, but mark them as disposable.

## Rule 6: Pin Important Actions

The chapter examples use major-version pins such as:

```yaml
uses: actions/checkout@v4
uses: docker/build-push-action@v6
```

For stricter supply-chain control, pin to commit SHAs.

That is noisier for a tutorial, but appropriate for sensitive repositories.

## Dependency Maintenance

Use:

```bash
uv lock --upgrade
uv run pytest
uv run mkdocs build --strict
```

Review lockfile changes.

Do not let dependency upgrades silently change KFP compilation outputs without review.

## Workflow Maintenance

CI workflows are code.

Review changes to:

```text
.github/workflows/
ci/
deploy/
```

with the same care as application code.

## Minimal Required CI/CD State

A good final tutorial state has:

```text
CI checks on every PR
image builds on trusted events
pipeline compilation on every PR
pipeline submission manual
promotion PR workflow manual
cleanup documented
```

## Final Acceptance Criteria

You are done with Chapter 9 when:

- images are built in CI
- pipeline definitions are compiled in CI
- tests and type checks run automatically
- docs build runs automatically
- optional pipeline submission is manual and gated
- promotion can be represented as a Git-tracked change
- secrets are not committed
- expensive cloud/GPU actions are not automatic by default

## References

- [GitHub Actions security hardening](https://docs.github.com/actions/security-guides/security-hardening-for-github-actions)
- [GitHub Actions secrets](https://docs.github.com/actions/security-guides/using-secrets-in-github-actions)
- [GitHub Actions environments](https://docs.github.com/actions/deployment/targeting-different-environments/using-environments-for-deployment)
- [Docker build with GitHub Actions](https://docs.docker.com/build/ci/github-actions/)

## Next Step

Continue with Chapter 10: Capstone.
