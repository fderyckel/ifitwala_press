# 10_mvp_execution_plan.md

## Purpose

This document turns the locked architecture into an immediate MVP execution plan for **Ifitwala_Press**.

It is intentionally narrow.

It does not replace:
- the control-plane model
- the lifecycle state machine
- the DocType proposal
- the actions-and-services design
- the infra rollout policy

It translates those documents into:
- what to build next
- what to prove first
- what to defer
- which files should appear in the repo first
- what "MVP ready" means for founder mode

---

## 1. Current repo reality

As of this plan:
- architecture and rollout docs are substantially defined
- `Tenant Policy` exists as the first real DocType
- the remaining control-plane backbone is not yet implemented
- lifecycle actions are defined in docs, but not yet embodied in code
- founder-mode deployment is acceptable by policy

This means the next work is not deeper infrastructure automation.

The next work is to make the control-plane backbone real.

---

## 2. Locked MVP posture

The MVP should follow the already-approved founder-mode shape:

- one low-cost shared runtime is acceptable
- one database per site remains mandatory
- manual and semi-automated execution is acceptable
- manual backups and restore discipline are acceptable at small scale
- routing may be manually maintained in phase 1
- full Cloud SQL, Traefik, Redis, and CI/CD automation are not phase-1 blockers

The control plane must still record:
- tenant identity
- environment identity
- lifecycle state
- app bundle intent
- hosting tier
- database mode
- routing intent
- policy
- transition history

---

## 3. Immediate gate before feature build

Before deeper implementation, run a short compatibility spike around the chosen DB baseline.

### Gate

The repository baseline is:
- MariaDB 11.8

### Compatibility spike goals

Prove, in a disposable local or founder-mode environment:
- Frappe v16 starts against MariaDB 11.8
- a site can be created successfully
- migrations run cleanly
- an image containing `ifitwala_ed` and `ifitwala_drive` can be built or pulled cleanly
- `ifitwala_ed` installs successfully
- `ifitwala_drive` installs successfully
- basic CRUD works after setup

### Why this gate exists

If the database baseline is wrong, every later control-plane artifact will be built on unstable assumptions.

The spike must happen before:
- deployment scripts
- managed DB automation
- deeper provisioning logic

---

## 4. MVP build sequence

The implementation sequence for the MVP is:

1. lock and prove the MariaDB 11.8 baseline
2. finish the phase-1 schema backbone
3. implement the workflow backbone
4. make the operator surfaces usable
5. prove one manual end-to-end lifecycle flow
6. only then add subscription, usage, cost, and health follow-ups

This follows the existing build-order rules.

---

## 5. Phase 1A — Schema backbone

Build the minimum viable control-plane records.

### Required DocTypes

- `Tenant Policy` (already present, refine only as needed)
- `Press Tenant`
- `Tenant Environment`
- `Tenant Transition Log`

### Required outcome

By the end of this phase:
- tenant identity is modeled separately from environment reality
- lifecycle state is stored on `Tenant Environment`
- policy can be assigned cleanly
- transition history has a durable append-only record shape
- the environment model has a clear place for app bundle intent even if `App Bundle` lands in phase 1.5

### First file set to add

Create these paths first:

- `/Users/francois.de/Documents/ifitwala_press/ifitwala_press/ifitwala_press/doctype/press_tenant/`
- `/Users/francois.de/Documents/ifitwala_press/ifitwala_press/ifitwala_press/doctype/tenant_environment/`
- `/Users/francois.de/Documents/ifitwala_press/ifitwala_press/ifitwala_press/doctype/tenant_transition_log/`

Within each DocType directory, the initial implementation should at minimum include:
- `__init__.py`
- the DocType JSON definition
- the Python controller if validation logic is needed immediately

### Validation priorities

Only implement validations already locked by the docs:

- unique and normalized tenant slug
- canonical lifecycle states only
- hosting tier and DB mode consistency
- sandbox vs production contradictions blocked
- archive and live contradictions blocked
- transition log treated as append-only

---

## 6. Phase 1B — Workflow backbone

After the schema exists, stop relying on raw status edits.

### Service layer to add

Create:

- `/Users/francois.de/Documents/ifitwala_press/ifitwala_press/ifitwala_press/services/`

Initial service files should include:

- `/Users/francois.de/Documents/ifitwala_press/ifitwala_press/ifitwala_press/services/environment_lifecycle_service.py`
- `/Users/francois.de/Documents/ifitwala_press/ifitwala_press/ifitwala_press/services/transition_log_service.py`

### First actions to implement

Build these first and no more:

1. Create Sandbox
2. Qualify for Production
3. Provision Production
4. Mark Live
5. Suspend Environment
6. Restore Environment
7. Archive Environment

### Required outcome

By the end of this phase:
- lifecycle changes happen through named server actions
- allowed transitions are enforced
- every lifecycle mutation writes a `Tenant Transition Log`
- failure states are visible and not silent

---

## 7. Phase 1B.1 — Role and permission foundation

Permissions should support the workflow early, but should remain simple.

### Roles to establish

- Ifitwala Press Admin
- Ifitwala Press Ops
- Ifitwala Press Support
- Ifitwala Press Sales
- Ifitwala Press Finance

### Practical MVP rule

Do not block the schema/workflow backbone on perfect RBAC detail.

The MVP only needs enough role structure to protect:
- production provisioning
- mark-live authority
- suspension and archive actions
- policy editing
- cost/subscription visibility

---

## 8. Phase 1B.2 — Operator usability

Once actions are real, make the operator surfaces usable.

### Priority surfaces

- `Press Tenant` list
- `Press Tenant` detail
- `Tenant Environment` list
- `Tenant Environment` detail
- transition history section on environment

### Required outcome

Operators should be able to:
- create a tenant
- create a sandbox record through a governed action
- move an environment through the approved lifecycle
- inspect why a state changed
- understand the next valid action without reading raw docs every time

---

## 9. Founder-mode proof flow

Before deeper automation, prove one real lifecycle path end to end.

### Target proof

Run one environment through:

`Lead -> Sandbox Provisioning -> Sandbox Active -> Production Qualification -> Production Provisioning -> Live`

### Founder-mode assumptions

This proof may use:
- one shared VM
- one shared MariaDB 11.8 host or instance
- manual database creation if needed
- manual site creation if needed
- manual routing steps
- manual backup verification

### Required outcome

The goal is not zero-manual work.

The goal is:
- the control-plane records are accurate
- the lifecycle is governed
- the transition history is trustworthy
- the manual runbook matches the control-plane model

---

## 10. What is explicitly deferred

The following should not block MVP completion:

- Cloud SQL automation
- Redis Memorystore automation
- Traefik sync automation
- Cloud DNS automation
- autoscaling or MIG orchestration
- exact cloud cost attribution
- polished dashboards before real data exists

These may come later after the backbone is proven.

---

## 11. File-by-file implementation order

Use this order unless real implementation friction forces a small adjustment:

1. `/Users/francois.de/Documents/ifitwala_press/ifitwala_press/ifitwala_press/doctype/press_tenant/`
2. `/Users/francois.de/Documents/ifitwala_press/ifitwala_press/ifitwala_press/doctype/tenant_environment/`
3. `/Users/francois.de/Documents/ifitwala_press/ifitwala_press/ifitwala_press/doctype/tenant_transition_log/`
4. `/Users/francois.de/Documents/ifitwala_press/ifitwala_press/ifitwala_press/services/environment_lifecycle_service.py`
5. `/Users/francois.de/Documents/ifitwala_press/ifitwala_press/ifitwala_press/services/transition_log_service.py`
6. server action wiring for the backbone lifecycle actions
7. list/detail usability improvements for tenant and environment
8. only after that, `Tenant Subscription`
9. then `Tenant Usage Snapshot`
10. then `Tenant Cost Snapshot`
11. then health-check structure

---

## 12. MVP exit criteria

The MVP is "done enough" when all of the following are true:

- the MariaDB 11.8 baseline is explicit and internally consistent in the repo
- the baseline has been proven in a compatibility spike
- `Press Tenant`, `Tenant Policy`, `Tenant Environment`, and `Tenant Transition Log` all exist
- lifecycle transitions are server-authoritative
- transition logs are written consistently
- one tenant can be taken from lead to live through a manual but governed founder-mode workflow
- operators can review the history and current posture without digging through raw implementation details

If those conditions are not true, the platform is not yet ready for deeper infra automation.
