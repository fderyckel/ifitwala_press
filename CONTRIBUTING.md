# Contributing

This repository is an internal-only Frappe control plane for operating hosted Ifitwala_Ed tenants.

Before changing code or docs, read:
- [AGENTS.md](/Users/francois.de/Documents/ifitwala_press/AGENTS.md)
- [README.md](/Users/francois.de/Documents/ifitwala_press/README.md)

## Runtime Baseline

The current project baseline is:
- Python 3.14
- MariaDB 11.4
- Node 24+
- Yarn

Python tooling is defined in [pyproject.toml](/Users/francois.de/Documents/ifitwala_press/pyproject.toml).

## Database Baseline Rule

`MariaDB 11.4` is the current repository baseline.

Treat this as an explicit project decision, not a loose suggestion.

That means:
- do not reintroduce older MariaDB recommendations elsewhere in the repo without an explicit architecture decision
- do not assume generic Frappe guidance overrides this repository baseline automatically
- any rollout plan for Frappe v16 must include a compatibility spike proving site creation, migrations, and app install behavior on MariaDB 11.4 before production rollout

## Runtime Tooling Rule

The application and local dev baseline is:
- Python 3.14
- Node 24+
- Yarn for JavaScript package management

Use Yarn, not npm, for any frontend or asset-install workflow added to this repository.

## Local Setup

Install developer tooling:

```bash
make install-dev
```

Install git hooks:

```bash
make pre-commit-install
```

This installs both:
- a `pre-commit` hook for Ruff, formatter, hygiene checks, and Desk/page JavaScript syntax checks
- a `pre-push` hook for `pytest`
- if Node is not available locally, the pre-commit JS syntax hook skips with a warning; the strict JS gate still runs in `make ci` and GitHub CI

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

Hook behavior:
- `git commit` runs the repo pre-commit gate
- `git push` runs the repo `pytest` pre-push gate
- `make ci` remains the full explicit merge gate and still includes `js-check`

## Pre-Merge Procedure

Treat merge readiness as stricter than "tests passed on my machine."

Before merging:

1. Rebase or merge the latest target branch into your branch and resolve conflicts intentionally.
2. Run the full local gate:

```bash
make ci
```

3. If you changed Desk routes, workspace metadata, page assets, form JS, or CSS for `ifitwala_press`, run the target-site update flow on `press.ifitwala.com` before merge:

```bash
bench --site press.ifitwala.com migrate
bench build --app ifitwala_press
bench restart
```

4. Smoke-check the affected operator surface on `press.ifitwala.com`.
   For the current control-plane work, this includes:
   - the `Control Plane Home` page
   - the `Ifitwala Press` workspace
   - any changed form/list action surface
5. Confirm GitHub CI is green on the branch or pull request.
6. Confirm tests and docs were updated for any behavior, workflow, permission, or operator-surface change.

Do not merge while GitHub CI is red, while required docs are stale, or while a Desk/workspace change has not been migrated and smoke-checked on `press.ifitwala.com`.

## Contribution Rules

- Do not bypass the control-plane model.
- Do not merge tenant identity and environment state.
- Do not invent lifecycle states, DocTypes, or workflows without grounding them in the current architecture docs.
- Prefer server-authoritative actions over manual status editing.
- Keep provider-specific infrastructure details out of phase-1 core models unless they are operationally necessary.
- Keep Google Cloud Storage and Google Cloud DNS as the default storage and DNS contracts unless an explicit architecture change is made.
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
