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
- the core control-plane backbone now exists in code
- `Tenant Policy`, `Press Tenant`, `Tenant Environment`, and `Tenant Transition Log` are implemented
- `Tenant Subscription`, `Tenant Usage Snapshot`, and `Tenant Cost Snapshot` also exist
- lifecycle actions are implemented in the service and API layers
- role bootstrap and baseline Desk/operator surfaces are implemented
- a founder-mode lifecycle flow has already been proven on the control plane

What remains incomplete is no longer the basic control-plane backbone.

What remains incomplete is:
- the MariaDB 11.8 compatibility proof on a supported founder runtime
- explicit founder-runtime app bundle and cache topology intent
- the phase-1 S3 storage contract for live files and daily backups
- real provisioning of `ifitwala_ed` + `ifitwala_drive` environments
- a governed founder-mode runbook that maps control-plane actions to real runtime work

This means the next work is not more basic DocType scaffolding.

The next work is to connect the control plane to a real founder runtime without drifting into premature full orchestration.

---

## 2. Locked MVP posture

The MVP should follow the already-approved founder-mode shape:

- separate public-site and control-plane Frappe sites
- one low-cost shared runtime is acceptable
- one database per site remains mandatory
- manual and semi-automated execution is acceptable
- S3-compatible object storage is the MVP baseline for live files and retained backups
- daily backup exports to the less-frequent storage class are acceptable at small scale
- routing may be manually maintained in phase 1
- full Cloud SQL, Traefik, Redis, and CI/CD automation are not phase-1 blockers

The preferred phase-1 topology is:

- `ifitwala.com` as the public site
- `press.ifitwala.com` or `ops.ifitwala.com` as the control plane
- one founder shared runtime for tenant environments

Separate hosts for public, control plane, and tenant runtime are recommended.
Separate public and control-plane sites are mandatory.

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

## 3. Immediate gate before provisioning build

Before deeper provisioning implementation, run a short compatibility spike around the chosen runtime baseline.

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
- semi-automated docker provisioning from the control plane

This spike should use the founder-mode self-managed MariaDB posture, not a managed DB assumption.

---

## 4. MVP build sequence

The implementation sequence for the MVP is:

1. lock and prove the MariaDB 11.8 baseline
2. finish the phase-1 schema backbone
3. implement the workflow backbone
4. make the operator surfaces usable
5. prove one manual end-to-end lifecycle flow
6. extend the environment model for real founder-runtime deployment intent
7. prove one real founder-mode runtime for `ifitwala_ed` + `ifitwala_drive`
8. only then add deeper provisioning automation and remote orchestration

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
2. Complete Sandbox Provisioning
3. Qualify for Production
4. Mark Provisioning Failed
5. Provision Production
6. Mark Live
7. Suspend Environment
8. Restore Environment
9. Archive Environment

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

### Current status

This control-plane proof has already been achieved.

The still-open proof is different:
- a real founder-mode runtime exists
- `ifitwala_ed` installs successfully there
- `ifitwala_drive` installs successfully there
- one real demo environment can be provisioned and then reflected back into the control plane

That runtime proof is now the live MVP gap.

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

## 11. Next file-by-file implementation order

Use this order unless real implementation friction forces a small adjustment:

1. update this execution plan and related docs so they reflect the implemented backbone
2. extend `/Users/francois.de/Documents/ifitwala_press/ifitwala_press/ifitwala_press/doctype/tenant_environment/`
   to capture the real founder runtime shape:
   - app bundle intent
   - `ifitwala_drive` install intent or branch
   - S3 storage provider/class intent for live files and retained backups
   - cache / queue topology intent
   - founder runtime profile notes
3. add or refine a service contract in
   `/Users/francois.de/Documents/ifitwala_press/ifitwala_press/ifitwala_press/services/environment_lifecycle_service.py`
   for founder-mode provisioning completion and failure capture
4. document the founder runtime runbook for a same-VM dockerized runtime using an approved app bundle
5. prove one real runtime with `ifitwala_ed` + `ifitwala_drive`
6. only after that, build a semi-automated provisioning adapter
7. only after the adapter works, evaluate Agent-style remote execution and later multi-host orchestration

---

## 12. MVP exit criteria

The MVP is "done enough" when all of the following are true:

- the MariaDB 11.8 baseline is explicit and internally consistent in the repo
- the baseline has been proven in a compatibility spike
- `Press Tenant`, `Tenant Policy`, `Tenant Environment`, and `Tenant Transition Log` all exist
- lifecycle transitions are server-authoritative
- transition logs are written consistently
- the phase-1 S3 storage contract is explicit in policy, environment, and founder-runtime payloads
- one tenant can be taken from lead to live through a manual but governed founder-mode workflow
- operators can review the history and current posture without digging through raw implementation details
- one real founder runtime for `ifitwala_ed` + `ifitwala_drive` has been proven operationally

If those conditions are not true, the platform is not yet ready for deeper infra automation.
