# 04_actions_and_services.md

## Purpose

This document defines the first server-authoritative actions and service boundaries for **Ifitwala_Press**.

Ifitwala_Press is a control plane.
That means important operational behavior must not depend on:

- casual manual field edits
- hidden client-side logic
- ad hoc scripts run outside the system
- operators directly mutating records without governed actions

This document locks:

- which actions should exist first
- which DocTypes those actions act upon
- what each action is responsible for
- what validations are required
- what side effects are expected
- what must be logged
- how services should be separated from UI and from raw documents

This is a design-lock document for the control-plane action layer.

---

## 1. Core principles

### 1.1 Actions must be server-authoritative
Critical lifecycle and operational actions must run on the server.

The UI may trigger them.
The UI must not implement them.

### 1.2 Actions must be explicit
If an operator:
- creates a sandbox
- qualifies a tenant for production
- provisions production
- suspends an environment
- archives an environment

that must happen through a named action, not through status editing.

### 1.3 Validation before mutation
Every action must validate:
- whether the action is allowed in the current state
- whether required fields are present
- whether policy constraints are satisfied
- whether the target environment/tenant is coherent

### 1.4 Side effects must be deliberate
An action is not only a status change.
It may also:
- create related records
- update timestamps
- update linked tenant summaries
- create transition logs
- schedule jobs
- refresh derived metadata

These side effects must be explicit.

### 1.5 Logging is mandatory
Every meaningful action must leave a durable trail.

### 1.6 Services own orchestration
DocTypes should enforce local validation and invariants.
Named service functions should orchestrate multi-step operational behavior.

Do not bury orchestration logic inside random form events.

### 1.7 Execution maturity is expected to evolve
The same control-plane action may exist in three implementation classes:
- manual
- semi-automated
- automated

The action contract should survive across all three.
Phase 1 may legitimately use manual or semi-automated execution while preserving validation, auditability, and explicit state handling.

---

# 2. Service boundary philosophy

There are three layers to keep clean.

## 2.1 UI / Form layer
Responsible for:
- displaying state
- showing allowed actions
- collecting operator input
- calling server-side actions
- showing results/errors

Not responsible for:
- deciding lifecycle legality
- writing multi-record orchestration
- enforcing critical invariants

## 2.2 Document layer
Responsible for:
- field validation
- local invariants
- protecting schema integrity
- preventing invalid stored states

Examples:
- invalid site name format
- contract end before start
- VIP + shared-tier contradiction
- missing DB instance when database mode is dedicated

Not responsible for:
- provisioning orchestration
- multi-step environment creation
- lifecycle workflows spanning multiple records

## 2.3 Service / action layer
Responsible for:
- orchestrating lifecycle actions
- checking transition legality
- applying policy logic
- mutating multiple records coherently
- writing transition logs
- initiating background jobs when needed

This is where most control-plane behavior belongs.

### 2.4 Service contracts should stay provider-agnostic
Service inputs should describe:
- placement intent
- database mode
- routing intent
- copy or conversion strategy

They should not assume a specific cloud provider API, managed database product, or proxy implementation in phase 1.

---

# 3. First-class actions

The following actions should exist as named server-side operations.

These are the first serious control-plane actions.

---

# 3.1 Create Sandbox

## Target
Usually triggered from:
- `Press Tenant`
- optionally from a pre-created `Tenant Environment` in `Lead`

## Purpose
Create a sandbox environment for a tenant.

## Preconditions
- tenant exists
- tenant is not archived
- tenant is not already in a conflicting sandbox flow unless policy allows multiple sandboxes
- sandbox policy is available
- required tenant identity fields are present
- tenant is commercially eligible for sandbox creation

## Inputs
- tenant
- selected policy or default policy
- optional sandbox name
- optional expiry override
- optional demo/template profile
- optional region override

## Expected side effects
- create or initialize `Tenant Environment`
- set environment type = Sandbox
- set lifecycle state = Sandbox Provisioning
- apply hosting tier = Sandbox
- apply policy defaults
- assign site_name or reserve naming
- set expiry date according to policy
- create `Tenant Transition Log`
- optionally queue provisioning job

## Execution note
In phase 1 this action may initiate a manual operator workflow instead of fully automated provisioning.
The recorded job or reference may point to a checklist, ticket, or manually-run procedure.

## Output
- environment record created/updated
- action result with environment reference
- transition log reference if useful

## Failure behavior
- do not leave misleading active state
- if creation fails after environment exists, mark clearly and log failure
- if environment cannot be created at all, fail loudly

---

# 3.2 Reset Sandbox

## Target
`Tenant Environment`

## Purpose
Reset a sandbox environment to a clean demo/trial state.

## Preconditions
- environment exists
- environment type = Sandbox
- current state usually = Sandbox Active or Sandbox Expired
- policy allows reset
- environment is not archived

## Inputs
- environment
- optional reset reason
- optional demo/template profile override

## Expected side effects
- record reset intent
- optionally queue rebuild/reset job
- preserve audit trail
- optionally refresh expiry date per policy
- create log entry
- optionally create transition if reset uses an intermediate provisioning path

## State behavior
Two viable approaches:
1. reset within same state, while logging operational event
2. move temporarily into Sandbox Provisioning if reset is effectively a rebuild

This should be chosen explicitly in implementation.
Do not improvise later.

## Failure behavior
- failure must be visible
- do not silently pretend reset succeeded

---

# 3.3 Expire Sandbox

## Target
`Tenant Environment`

## Purpose
Move a sandbox from active to expired state.

## Preconditions
- environment type = Sandbox
- current state = Sandbox Active
- expiry or operator intent justifies the action

## Inputs
- environment
- expiry reason

## Expected side effects
- set state = Sandbox Expired
- update timestamps
- create transition log
- optionally disable access or mark routing/access restrictions in future automation

## Failure behavior
- clear error if already expired/archived
- no silent no-op

---

# 3.4 Reactivate Sandbox

## Target
`Tenant Environment`

## Purpose
Re-enable a sandbox that had expired.

## Preconditions
- environment type = Sandbox
- current state = Sandbox Expired
- reactivation allowed by policy or operator authority

## Inputs
- environment
- optional new expiry date
- optional reason

## Expected side effects
- set state = Sandbox Active
- update expiry if needed
- create transition log

---

# 3.5 Qualify for Production

## Target
Usually `Tenant Environment` and/or linked `Press Tenant`

## Purpose
Move a tenant/environment into production qualification state.

## Preconditions
- tenant exists
- target environment exists or is about to be defined
- current state is usually Sandbox Active, Sandbox Expired, or Lead
- commercial intent is sufficiently clear
- proposed hosting tier and DB mode can be determined

## Inputs
- tenant/environment
- target hosting tier
- target database mode
- conversion strategy
- optional region
- optional policy override

## Expected side effects
- ensure or create production-target environment if that is the chosen model
- set state = Production Qualification
- persist selected hosting intent
- persist conversion strategy
- create transition log

## Notes
This is a checkpoint action.
It should not provision production directly.

---

# 3.6 Provision Production

## Target
`Tenant Environment`

## Purpose
Start real production provisioning for a qualified environment.

## Preconditions
- environment type = Production
- current state = Production Qualification
- policy assigned
- database mode assigned
- region/placement sufficiently defined
- required site/domain intent present or intentionally deferred
- conversion strategy selected

## Inputs
- environment
- production site name or site naming confirmation
- deployment placement inputs
- optional domain inputs
- optional copy strategy inputs

## Expected side effects
- set state = Production Provisioning
- record provisioning job id if queued
- persist finalized provisioning inputs
- create transition log
- optionally dispatch background provisioning workflow

## Execution note
In phase 1, provisioning may begin as a manual or semi-automated workflow.
The action still owns validation, intent capture, state transition, and failure visibility.

## Failure behavior
- if provisioning workflow cannot start, fail loudly
- if provisioning starts but later fails, move to Provisioning Failed and log details

---

# 3.7 Mark Live

## Target
`Tenant Environment`

## Purpose
Mark a production environment as live only after provisioning and go-live checks succeed.

## Preconditions
- environment type = Production
- current state = Production Provisioning
- required checks passed
- DB placement exists
- policy exists
- production environment is considered ready

## Inputs
- environment
- go-live note
- optional checklist evidence

## Expected side effects
- set state = Live
- update go-live timestamps
- create transition log
- update tenant active environment pointer if appropriate

## Execution note
This may represent completion of a manual go-live checklist in phase 1.
The control plane should record that explicitly rather than pretending the process was fully automated.

## Notes
This action must not be casually available.
It is the boundary into real production.

---

# 3.8 Suspend Environment

## Target
`Tenant Environment`

## Purpose
Suspend a live or active environment for operational/commercial reasons.

## Preconditions
- current state allows suspension
- environment is not archived
- suspension reason provided

## Inputs
- environment
- suspension reason
- optional effective date
- optional internal notes

## Expected side effects
- set state = Suspended
- create transition log
- record reason prominently
- optionally affect billing or access flags later

## Notes
Suspension should be explicit and explainable.

---

# 3.9 Restore Environment

## Target
`Tenant Environment`

## Purpose
Restore a suspended environment to live state.

## Preconditions
- current state = Suspended
- restoration is authorized
- blocking issues resolved

## Inputs
- environment
- restore reason

## Expected side effects
- set state = Live
- create transition log
- clear/resolve suspension context where appropriate

---

# 3.10 Archive Environment

## Target
`Tenant Environment`

## Purpose
Move an environment to archived state.

## Preconditions
- environment is not already archived
- archive intent is justified
- retention implications reviewed where needed

## Inputs
- environment
- archive reason
- optional retention note

## Expected side effects
- set state = Archived
- create transition log
- mark environment as operationally closed
- optionally update tenant summary fields

## Notes
Archiving should be treated as near-terminal in v1.

---

# 3.11 Run Health Check

## Target
`Tenant Environment`

## Purpose
Execute or record a health check refresh for the environment.

## Preconditions
- environment exists
- environment not archived, unless explicit archived diagnostics are allowed

## Inputs
- environment
- check scope
  - full
  - HTTP only
  - DB only
  - Redis only
  - backup only

## Expected side effects
- update health fields
- append `Tenant Health Check` record or child row
- update last health check timestamp
- possibly update capacity/health summary
- optionally create alert if degraded

## Notes
Health checks are not lifecycle transitions by themselves.

---

# 3.12 Refresh Usage Snapshot

## Target
`Tenant Environment` and/or `Press Tenant`

## Purpose
Refresh usage metrics for operator visibility.

## Preconditions
- environment exists
- enough data sources exist to calculate a snapshot

## Inputs
- environment
- snapshot date/time or default now

## Expected side effects
- create `Tenant Usage Snapshot`
- update summary fields on environment/tenant if desired
- leave clear timestamp of refresh

---

# 3.13 Refresh Cost Snapshot

## Target
`Tenant Environment` and/or `Press Tenant`

## Purpose
Refresh cost estimates for the tenant/environment.

## Preconditions
- environment exists
- cost calculation inputs are available

## Inputs
- environment
- snapshot date/time or default now

## Expected side effects
- create `Tenant Cost Snapshot`
- update `estimated_monthly_cost` on environment if using cached summary fields
- timestamp the refresh

---

# 3.14 Sync Routing Intent

## Target
`Tenant Environment`

## Purpose
Validate and synchronize the routing metadata the control plane owns.

## Preconditions
- environment exists
- domain/routing metadata exists or is expected

## Inputs
- environment
- optional domain override / refresh scope

## Expected side effects
- validate primary domain and domain child rows
- refresh routing readiness fields
- update DNS/TLS readiness state if supported by implementation
- log action or create event if needed

## Notes
This action owns the control-plane side of routing intent.
It does not need to fully own proxy implementation in v1.

---

# 3.15 Rotate DB Credentials

## Target
`Tenant Environment`

## Purpose
Safely record or trigger DB credential rotation workflow.

## Preconditions
- environment has DB configuration
- operator authorization present

## Inputs
- environment
- reason
- optional execution mode

## Expected side effects
- record credential rotation event
- update secure references later as implementation grows
- log action clearly

## Notes
Even if full automation comes later, the action concept should exist early.

---

# 4. State transition ownership

Lifecycle transitions must be triggered through these actions, not by raw field mutation.

Examples:

- `Create Sandbox` owns transition into Sandbox Provisioning
- `Expire Sandbox` owns transition into Sandbox Expired
- `Qualify for Production` owns transition into Production Qualification
- `Provision Production` owns transition into Production Provisioning
- `Mark Live` owns transition into Live
- `Suspend Environment` owns transition into Suspended
- `Restore Environment` owns transition back to Live
- `Archive Environment` owns transition into Archived

The status field should not be treated as the workflow itself.
The action is the workflow.

---

# 5. Action validation rules

Every action should validate at least 5 things.

## 5.1 Record existence
Target tenant/environment/policy must exist.

## 5.2 Current state legality
The action must be allowed from the current lifecycle state.

## 5.3 Structural completeness
Required fields must be present for that action.

Examples:
- production cannot provision without DB mode and policy
- public routing sync cannot run meaningfully without domain metadata
- dedicated DB mode should require DB instance identity

## 5.4 Policy compatibility
Action must not violate the assigned policy.

Examples:
- sandbox reset not allowed by policy
- in-place upgrade blocked by policy
- expiry overrides outside allowed range

## 5.5 Internal coherence
Related fields must agree.

Examples:
- VIP tier + shared DB contradiction
- Production + missing policy contradiction
- Archived + active operational action contradiction

---

# 6. Action result contract

Each server action should return a clear, structured result.

At minimum, the action result should communicate:

- success/failure
- affected record(s)
- resulting state if relevant
- operator-facing message
- any queued job id if relevant
- any warning flags

Do not return vague “ok” responses for important actions.

---

# 7. Transition logging rules

Every action that changes lifecycle state must create a `Tenant Transition Log`.

At minimum, the log should store:
- tenant
- environment
- from_state
- to_state
- trigger_type
- triggered_by
- success
- timestamp
- message
- related job id if any

For non-transition operational actions, the implementation may later use:
- event logs
- health check records
- cost/usage snapshot records
- incident/alert records

But lifecycle transitions are always logged.

---

# 8. Failure handling rules

## 8.1 Validate first, mutate second
If preconditions fail:
- raise a server error
- do not partially mutate state
- do not create misleading logs

## 8.2 Partial failure during orchestration
If an action has already started changing state or scheduling work and then fails:
- reflect the failure explicitly
- log the failure
- avoid leaving ambiguous state

Examples:
- provisioning started but failed → move to Provisioning Failed
- reset requested but rebuild failed → log failure and do not pretend sandbox is healthy

## 8.3 No silent no-ops
If an operator clicks:
- suspend
- archive
- expire
- provision

and the action is not valid, the system must say so clearly.

---

# 9. Recommended service modules

The implementation should group services by control-plane concern, not by random convenience.

A reasonable early structure could be:

- `tenant_service.py`
- `environment_lifecycle_service.py`
- `environment_health_service.py`
- `environment_usage_service.py`
- `environment_cost_service.py`
- `routing_service.py`
- `transition_log_service.py`

The exact filenames can vary, but the boundary principle matters:
- lifecycle orchestration separate from usage/cost collection
- routing separate from lifecycle
- logging reusable, not duplicated everywhere

---

# 10. Recommended document responsibility split

## `Press Tenant`
Should own:
- customer identity validations
- contract date coherence
- tier and sensitivity consistency

Should not own:
- environment provisioning orchestration

## `Tenant Policy`
Should own:
- policy self-consistency
- quota and rule validation

Should not own:
- direct environment mutation workflows

## `Tenant Environment`
Should own:
- site/config field integrity
- environment self-consistency
- local field validation

Should not own:
- full lifecycle orchestration across multiple records

## `Tenant Transition Log`
Should own:
- append-only integrity
- minimal required audit fields

Should not own:
- business logic

---

# 11. UI behavior expectations

The UI should show actions based on state and permissions.

Examples:

## Sandbox Active
Show:
- Reset Sandbox
- Expire Sandbox
- Qualify for Production
- Run Health Check
- Refresh Usage Snapshot
- Refresh Cost Snapshot

Do not show:
- Mark Live

## Production Qualification
Show:
- Provision Production
- Archive

Do not show:
- Reset Sandbox

## Live
Show:
- Suspend Environment
- Run Health Check
- Refresh Usage Snapshot
- Refresh Cost Snapshot
- Sync Routing Intent

Do not show:
- Expire Sandbox

The UI should guide operators toward valid next steps.
The server still remains the source of truth.

---

# 12. What to avoid

Avoid these failure patterns:

### 12.1 Manual status editing as workflow
This destroys lifecycle trust.

### 12.2 Fat client logic
Do not implement core action rules in JS only.

### 12.3 Hidden side effects
Operators should not be surprised by major workflow changes.

### 12.4 Mixing monitoring and lifecycle carelessly
Running a health check is not the same as changing lifecycle state.

### 12.5 Weak action names
Use explicit names like:
- Create Sandbox
- Provision Production
- Archive Environment

not vague names like:
- Update Status
- Process Environment
- Sync All

---

# 13. Implementation priority

Recommended order:

## First
- Create Sandbox
- Qualify for Production
- Provision Production
- Mark Live
- Suspend Environment
- Restore Environment
- Archive Environment

## Then
- Expire Sandbox
- Reactivate Sandbox
- Run Health Check
- Refresh Usage Snapshot
- Refresh Cost Snapshot

## Then
- Sync Routing Intent
- Rotate DB Credentials
- richer operational actions

This gives immediate control-plane usefulness without pretending all automation exists on day one.

---

# 14. Final design position

In Ifitwala_Press, critical operations must happen through explicit server-authoritative actions.

Actions are the backbone of:
- lifecycle governance
- operator trust
- auditability
- safety
- future automation

The platform should behave like a real control plane:
state changes happen because named actions succeeded, not because someone edited a field.
