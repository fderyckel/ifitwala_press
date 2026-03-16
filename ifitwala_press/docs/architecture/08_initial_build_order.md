# 08_initial_build_order.md

## Purpose

This document locks the initial build order for **Ifitwala_Press**.

The point is simple:

If we build in the wrong order, we will create drift, rework, and fake progress.

Ifitwala_Press is a control plane.
That means the order matters more than in a casual internal app.

This document defines:

- what must be built first
- what must be deferred
- what dependencies exist between parts
- what “done enough” means for phase 1
- what should not be built prematurely

This is the final architecture-to-build bridge before implementation begins.

---

## 1. Build philosophy

### 1.1 Model first, automation later
Do not start with provisioning automation.
Do not start with cloud integration.
Do not start with Traefik automation.
Do not start with dashboards full of guessed data.

Start by building the control-plane records and action boundaries correctly.

### 1.2 One stable layer at a time
The order should be:

1. domain model
2. lifecycle + validation
3. operator actions
4. list/detail surfaces
5. usage/cost/subscription tracking
6. health/alerts
7. deeper infra automation

### 1.3 Manual-first is acceptable
For phase 1, some actions may be manually initiated but server-authoritative.

That is acceptable.

What is not acceptable:
- manual field editing as workflow
- no audit trail
- no state discipline
- no clear separation of concepts

### 1.3A Proof before automation
No infrastructure automation should be built before at least one manual lifecycle flow has been executed end to end and proven operationally sound.

Automation should follow demonstrated operational truth, not replace it.

### 1.4 Avoid false completeness
A half-working provisioning pipeline on top of weak records is worse than a manual but governed workflow.

---

# 2. What is already locked

The following are now considered architecturally locked enough to start building:

- internal-only control-plane purpose
- site-per-school tenant model
- shared runtime + separated database/state model
- hybrid hosting strategy
- sandbox vs production distinction
- tenant vs environment distinction
- lifecycle state machine
- initial roles/permissions philosophy
- naming conventions
- operator-first surface intent
- action-first server-authoritative workflow model
- usage/cost/subscription/health scope

That is enough architecture for phase 1.

Stop expanding architecture unless implementation reveals a real gap.

---

# 3. Phase 1 implementation target

Phase 1 should aim to deliver a **working control-plane backbone**.

That means:

- core records exist
- lifecycle can be governed
- transitions are logged
- operators can create/manage sandbox and production records safely
- tenant/environment separation is real
- policy model exists
- environment list/detail is useful
- transition history is visible

Phase 1 does **not** require:
- full provisioning automation
- full Traefik integration
- full GCP cost integration
- perfect dashboards
- complete alerting engine

### 3.1 Phase 1 infrastructure posture
Phase 1 may run on a low-cost, simple deployment shape if it preserves the control-plane model.

Acceptable founder-stage realities include:
- one low-cost shared runtime
- manual DB, user, and site creation
- manual backups and restore verification at small scale
- manually maintained routing steps

The records must still capture intended future placement, lifecycle, and policy cleanly.

---

# 4. Recommended build order

## Step 1 — Repo foundation
Before any DocType work, set up the repo cleanly.

### Deliverables
- root `AGENTS.md`
- `README.md`
- `docs/architecture/` foundation files
- basic app skeleton if not already created

### Why first
So the code starts with constraints, not chaos.

### Done enough
- docs committed
- architecture folder stable
- repo intent clear

---

## Step 2 — Create roles
Create the first internal roles.

### Deliverables
- Ifitwala Press Admin
- Ifitwala Press Ops
- Ifitwala Press Support
- Ifitwala Press Sales
- Ifitwala Press Finance

### Why now
Because permissions should shape implementation early, not be patched on later.

### Done enough
- roles exist
- permission intent documented in app setup docs or fixtures later if needed

---

## Step 3 — Build `Tenant Policy`
Build this first among core DocTypes.

### Why first
Because environment creation and hosting logic need policy defaults.
If you skip this, environment records will accumulate hardcoded assumptions.

### Phase 1 scope
Implement:
- key fields
- core validations
- list view basics

### Not needed yet
- advanced policy inheritance
- provider-specific automation payloads

### Done enough
- policies can be created
- policies validate correctly
- at least 3 seed policies can exist conceptually:
  - Sandbox Default
  - Standard Production
  - Premium/VIP

---

## Step 4 — Build `Press Tenant`
Build the master tenant/customer record second.

### Why before environment
Because environments need a customer anchor.
The system should not create orphan environments.

### Phase 1 scope
Implement:
- key identity/commercial fields
- size/risk fields
- hosting intent fields
- contact child table if ready
- basic validations

### Done enough
- tenant records can be created cleanly
- slug uniqueness works
- tenant has meaningful list/detail views

---

## Step 5 — Build `Tenant Environment`
This is the main operational record.

### Why now
By this point:
- policy exists
- tenant exists
- environment can link to both cleanly

### Phase 1 scope
Implement:
- environment identity
- lifecycle state
- policy link
- hosting tier
- DB mode
- routing basics
- health summary fields
- cost summary placeholder
- child table for domains if ready

### Done enough
- environment records can be created cleanly
- list view is operationally useful
- state field exists with canonical options
- field validations prevent obvious contradictions

### Important
At this step, do **not** yet rely on raw manual status editing as the real workflow.
That comes next via actions.

---

## Step 6 — Build `Tenant Transition Log`
Build this immediately after environment.

### Why now
Because once actions start mutating lifecycle, auditability must already exist.

### Phase 1 scope
Implement:
- append-only style behavior
- core fields
- readable list view
- environment-linked display

### Done enough
- transition records can be inserted from server actions
- operators can review lifecycle history

---

## Step 7 — Implement lifecycle action services
This is the first serious service layer.

### Initial actions to build
1. Create Sandbox
2. Qualify for Production
3. Provision Production
4. Mark Live
5. Suspend Environment
6. Restore Environment
7. Archive Environment

### Why these first
These actions establish the control-plane backbone.
Without them, the records exist but the workflow is still informal.

### Phase 1 scope
Each action must:
- validate preconditions
- enforce allowed transitions
- mutate target records
- create transition logs
- fail clearly

### Done enough
- lifecycle changes happen through actions, not raw field edits
- transition logs are written consistently
- state machine enforcement is real

---

## Step 8 — Add secondary sandbox actions
After the backbone actions work, add sandbox-specific convenience.

### Actions
- Reset Sandbox
- Expire Sandbox
- Reactivate Sandbox

### Why later
They matter, but they are secondary compared to establishing the main tenant-to-production path.

### Done enough
- sandbox lifecycle feels governed
- trials are no longer informal records

---

## Step 9 — Build operator list/detail usability
Now make the UI practical.

### Priority surfaces
- Tenant list
- Tenant detail
- Environment list
- Environment detail
- transition history panel on environment

### Why now
Because once records and actions exist, operators need usable surfaces.

### Phase 1 scope
Focus on:
- key columns
- meaningful indicators
- obvious action buttons
- low-noise forms

### Done enough
- operators can actually run the phase 1 workflow without confusion

---

## Step 10 — Add `Tenant Subscription`
This is the first commercial follow-up record.

### Why before usage/cost
Subscription state is simpler and necessary for commercial clarity.

### Phase 1 scope
Implement:
- plan fields
- subscription status
- billing cycle
- date range
- linkage to tenant

### Done enough
- each tenant can have meaningful subscription data
- trial vs paid is visible inside the control plane

---

## Step 11 — Add `Tenant Usage Snapshot`
Start the metrics layer with usage.

### Why before cost
Usage is the more direct operational signal and can later inform cost.

### Phase 1 scope
Implement only core summary fields:
- snapshot_on
- active_users_30d
- storage_used_gb
- file_count
- request_count_30d
- peak_concurrency_estimate

### Done enough
- usage snapshots can be created manually or via simple server process
- environment/tenant can show latest usage summary

---

## Step 12 — Add `Tenant Cost Snapshot`
Add cost tracking after usage structure is in place.

### Why now
By this point the control plane can start making business sense.

### Phase 1 scope
Implement:
- DB cost estimate
- storage cost estimate
- compute cost estimate
- backup cost estimate
- total cost estimate

### Done enough
- operators can see rough per-tenant cost posture
- environment shows latest estimated monthly cost

---

## Step 13 — Add health check structure
Now add structured health, beyond summary fields.

### Deliverables
- `Tenant Health Check` or child-table-first approach
- Run Health Check action
- latest check surfaced on environment

### Done enough
- operators can run and review structured health checks
- environment detail reflects latest health state more credibly

---

## Step 14 — Add dashboard/home surface
Only now build the top operator dashboard.

### Why this late
Dashboards built before real data and actions usually become decorative lies.

### Phase 1 scope
Show only what the system actually knows:
- total tenants
- tenants by status
- live environments
- sandbox environments
- provisioning failures
- renewals due soon
- top estimated monthly cost tenants
- unhealthy environments
- expiring sandboxes

### Done enough
- the home screen helps operators prioritize work

---

# 5. Recommended phase grouping

## Phase 1A — Schema backbone
Build:
- Tenant Policy
- Press Tenant
- Tenant Environment
- Tenant Transition Log

Goal:
- stable data model

## Phase 1B — Workflow backbone
Build:
- lifecycle services/actions
- state validations
- transition logs
- main list/detail usability

Goal:
- controlled operator workflow

## Phase 1C — Business visibility backbone
Build:
- Tenant Subscription
- Tenant Usage Snapshot
- Tenant Cost Snapshot
- health checks

Goal:
- operational + commercial visibility

## Phase 1D — Dashboard and polish
Build:
- home dashboard
- alerts/attention summaries
- better list filters and indicators

Goal:
- practical daily operations console

---

# 6. What should be deferred

The following should not block phase 1.

## 6.1 Full GCP automation
Do not block on:
- Cloud SQL automation
- managed DB automation generally
- GCS automation
- GKE automation
- cost API integrations
- DNS automation

## 6.1A Not phase 1
The following are explicitly deferred unless a real operating need proves otherwise:

- Cloud SQL or other managed DB automation
- Redis Memorystore automation
- Traefik sync automation
- Cloud DNS automation
- instance group or autoscaling automation
- Docker API or infra-agent orchestration complexity

These can come later once the control-plane records and actions are stable.

## 6.2 Full Traefik implementation
Store routing intent now.
Do not block phase 1 on full Traefik sync.

## 6.3 Perfect cost precision
Rough internal estimates are acceptable first.
Do not block phase 1 on precise cloud billing attribution.

## 6.4 Rich charts
Useful later.
Not necessary before strong operational records exist.

## 6.5 Overly granular permissions
The role model is already defined enough to begin.
Do not delay core work chasing perfect RBAC nuance.

---

# 7. What must not be deferred

These are foundational and must happen early.

- policy model
- tenant/environment separation
- lifecycle state discipline
- transition logging
- server-authoritative actions
- append-only-ish audit records
- naming consistency
- clear operator list/detail usability

If these are deferred, the platform becomes messy fast.

---

# 8. Definition of “phase 1 done”

Phase 1 is done when all of the following are true:

### Data model
- core DocTypes exist and validate correctly

### Workflow
- key lifecycle transitions happen through server actions, not field edits

### Auditability
- transition logs are created reliably

### Usability
- operators can manage tenants and environments from list/detail surfaces

### Visibility
- at least basic subscription, usage, cost, and health visibility exists

### Discipline
- the platform can answer, for a given tenant:
  - who they are
  - what environment they have
  - what state it is in
  - what tier/policy applies
  - what it roughly costs
  - whether it looks healthy
  - what happened recently

If those are true, phase 1 is real.

---

# 9. First implementation recommendation

The first actual coding move after this document should be:

1. build `Tenant Policy`
2. then `Press Tenant`
3. then `Tenant Environment`
4. then `Tenant Transition Log`
5. then lifecycle action service for Create Sandbox

That is the sharpest, least sloppy start.

Do not start with dashboards.
Do not start with GCP integration.
Do not start with Traefik integration.

Start with the control-plane backbone.

---

# 10. Final build position

The correct initial build order for Ifitwala_Press is:

- schema backbone first
- lifecycle actions second
- operator usability third
- usage/cost/subscription visibility fourth
- automation and infra integration later

That is how we avoid fake progress and build a real internal control plane.
