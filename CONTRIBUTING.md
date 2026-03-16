# Contributing

This repository is an internal-only Frappe control plane for operating hosted Ifitwala_Ed tenants.

Before changing code or docs, read:
- [AGENTS.md](/Users/francois.de/Documents/ifitwala_press/AGENTS.md)
- [README.md](/Users/francois.de/Documents/ifitwala_press/README.md)

## Runtime Baseline

The current project baseline is:
- Python 3.13
- MariaDB 11.8
- Node 24+

Python tooling is defined in [pyproject.toml](/Users/francois.de/Documents/ifitwala_press/pyproject.toml).

## Local Setup

Install developer tooling:

```bash
make install-dev
```

Install git hooks:

```bash
make pre-commit-install
```

## Required Checks

Run the local CI command set before opening or updating a PR:

```bash
make ci
```

You can also run commands individually:

```bash
make lint
make format
make format-check
make test
make pre-commit-run
```

## Contribution Rules

- Do not bypass the control-plane model.
- Do not merge tenant identity and environment state.
- Do not invent lifecycle states, DocTypes, or workflows without grounding them in the current architecture docs.
- Prefer server-authoritative actions over manual status editing.
- Keep provider-specific infrastructure details out of phase-1 core models unless they are operationally necessary.
- Treat auditability, recoverability, and operator clarity as first-class constraints.

## Scope Discipline

Good contributions strengthen:
- tenant and environment modeling
- lifecycle governance
- policy-driven actions
- usage, cost, subscription, and health visibility
- operator usability

Out of scope unless explicitly approved:
- unrelated Ifitwala_Ed product features
- generic PaaS abstractions
- premature infrastructure automation
- provider-specific control-surface modeling that the platform does not yet need

## Testing Guidance

- Add or update tests for behavior you change.
- Keep tests realistic for the current repo stage.
- Do not introduce fake completeness; small smoke tests are acceptable when deeper integration coverage is not yet feasible.
- If a change cannot be fully validated locally, state that clearly in the PR or handoff.

## Pull Requests

- Keep changes scoped.
- Prefer small, reviewable patches.
- Update docs when architecture, workflow, or operator expectations change.
- Make sure local checks are green before asking for review.
