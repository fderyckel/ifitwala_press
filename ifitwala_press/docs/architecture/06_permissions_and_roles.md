# 06_permissions_and_roles.md

## Purpose

This document defines the first permission and role model for **Ifitwala_Press**.

Ifitwala_Press is an **internal-only control plane**.
It is not customer-facing.
Its users are our own operators.

That changes the permission philosophy completely.

We do not need fake complexity for imaginary public admins.
We do need strong control over:

- who can provision
- who can change lifecycle state
- who can see cost and subscription data
- who can alter hosting policy
- who can suspend or archive environments
- who can perform sensitive operational actions

The purpose of this document is to define a pragmatic, operator-safe permission model that supports internal teamwork without turning the platform into chaos.

This is a design-lock document for roles, permissions, and action authority.

---

## 1. Design principles

### 1.1 Internal-only, but not permission-free
Because this system is internal, permissions should be pragmatic.

That does **not** mean everyone should have full access.

Internal control planes are dangerous when:
- anyone can provision
- anyone can suspend live tenants
- anyone can edit routing or DB settings
- anyone can alter subscription or cost records without accountability

### 1.2 Separate visibility from action authority
Seeing something is not the same as changing it.

Example:
- support staff may need to see health and cost context
- but they should not be able to archive environments or change DB mode

### 1.3 Prefer simple roles with strong actions
Use a small number of meaningful roles.
Do not create a maze of edge-case roles early.

### 1.4 Sensitive actions must be explicit
The most sensitive actions should be restricted clearly, even inside the team.

Examples:
- provision production
- mark live
- suspend environment
- archive environment
- rotate DB credentials
- edit hosting tier / database mode
- edit policy records

### 1.5 Auditability matters more than UI hiding
Permissions should limit what users can do.
But even authorized actions must still be logged.

---

# 2. Role philosophy

The first role model should support how we actually operate the business.

A practical early split is:

- Press Admin
- Press Ops
- Press Support
- Press Sales
- Press Finance

This is enough to begin safely.

Do not overbuild permissions before the actual workflows settle.

---

# 3. Proposed roles

## 3.1 `Ifitwala Press Admin`

### Purpose
Full control over the internal control plane.

### Who should have it
Only a very small number of trusted operators/founders.

### Capabilities
Can:
- create and edit all core records
- create and edit policies
- perform all lifecycle actions
- provision production
- mark live
- suspend and restore environments
- archive environments
- edit hosting tier and DB mode
- edit routing intent
- trigger usage/cost/health refreshes
- view all cost/subscription/commercial data
- review and correct platform metadata

### Restrictions
Very few by role.
Still subject to:
- validations
- transition rules
- server-authoritative actions
- audit logging

### Notes
This role should be rare.

---

## 3.2 `Ifitwala Press Ops`

### Purpose
Operational management of tenant environments.

### Who should have it
People responsible for deployment, lifecycle operations, monitoring, and environment hygiene.

### Capabilities
Can:
- read all tenants and environments
- create sandboxs
- qualify for production
- provision production
- run health checks
- refresh usage and cost snapshots
- suspend and restore environments
- review routing/domain state
- view policies
- create transition-causing actions within allowed scope

### Typical allowed actions
- Create Sandbox
- Reset Sandbox
- Expire Sandbox
- Reactivate Sandbox
- Qualify for Production
- Provision Production
- Mark Live
- Suspend Environment
- Restore Environment
- Run Health Check
- Refresh Usage Snapshot
- Refresh Cost Snapshot
- Sync Routing Intent

### Restrictions
Should not:
- freely edit policy definitions
- freely alter commercial contract fields unless explicitly permitted
- delete audit logs
- bypass validation/state machine

### Notes
This is likely the main working role in the platform.

---

## 3.3 `Ifitwala Press Support`

### Purpose
Operational visibility and first-line diagnosis.

### Who should have it
Support or customer success operators who need deep visibility but not full infrastructure authority.

### Capabilities
Can:
- read tenants and environments
- read health, usage, cost, and subscription context
- run non-destructive checks
- open tenant/environment detail records
- review transition logs
- review incidents/alerts
- add internal notes where allowed

### Typical allowed actions
- Run Health Check
- Refresh Usage Snapshot
- Refresh Cost Snapshot
- View routing state
- View subscription state

### Restrictions
Should not:
- provision production
- mark live
- suspend or archive environments
- change DB mode
- change hosting tier
- edit policy records
- rotate DB credentials

### Notes
This role should be strong on visibility, lighter on mutation.

---

## 3.4 `Ifitwala Press Sales`

### Purpose
Commercial visibility over prospects, tenants, trials, and subscription posture.

### Who should have it
Sales or business development operators.

### Capabilities
Can:
- read tenant records
- read commercial fields
- read subscription fields
- see active environment links
- see high-level environment state
- initiate sandbox requests if allowed by workflow
- view upcoming renewals and trial expiries

### Typical allowed actions
- Create or update prospect/tenant commercial data
- Request/Create Sandbox depending on internal process
- Mark tenant commercially qualified if that becomes a formal action later

### Restrictions
Should not:
- provision production directly
- change technical hosting placement
- suspend/restore/archive environments
- edit policy records
- edit DB or routing details
- access sensitive operational credentials

### Notes
Sales needs enough visibility to act intelligently, but not deep infra authority.

---

## 3.5 `Ifitwala Press Finance`

### Purpose
Cost, subscription, and commercial review.

### Who should have it
Anyone responsible for pricing, cost review, or renewal management.

### Capabilities
Can:
- read tenant commercial state
- read subscription records
- read usage and cost snapshots
- review pricing mismatch signals
- review renewal and trial status
- view high-level environment state

### Typical allowed actions
- update subscription data where appropriate
- review plan/tier fit
- add finance notes
- export or review cost summaries

### Restrictions
Should not:
- provision environments
- suspend or restore environments unless your internal process explicitly allows it
- change technical routing/DB placement
- edit policy definitions unless finance policy ownership becomes real later

### Notes
This role may overlap with Admin in the beginning if the team is small.

---

# 4. Role-to-surface intent

This section defines what each role should mainly use.

## Press Admin
Main surfaces:
- all surfaces
- policy management
- deep environment records
- transition logs
- incident/health/cost/usage views

## Press Ops
Main surfaces:
- environment list
- environment detail
- home dashboard
- health/alerts
- transition logs
- routing/domain data

## Press Support
Main surfaces:
- tenant list/detail
- environment list/detail
- health/alerts
- transition logs
- subscription/usage/cost summary views

## Press Sales
Main surfaces:
- tenant list/detail
- trial/sandbox views
- subscription overview
- renewal views
- limited environment state summaries

## Press Finance
Main surfaces:
- cost views
- usage views
- subscription views
- renewal views
- tenant detail with commercial emphasis

---

# 5. Permission model by DocType

This is the first practical permission direction.

---

## 5.1 `Press Tenant`

### Admin
- Read
- Write
- Create
- limited delete only if absolutely necessary
- full action access

### Ops
- Read
- Write selected operational fields if needed
- Create if needed
- no unrestricted delete

### Support
- Read
- maybe limited write for internal notes only
- no destructive actions

### Sales
- Read
- Write commercial/prospect fields
- Create tenant prospects
- no destructive actions

### Finance
- Read
- limited write to commercial/subscription-related fields if needed

### Recommendation
Keep most field-level sensitive control via:
- role-aware server logic
- action methods
- field permission levels if truly needed

Do not overcomplicate per-field permissions too early.

---

## 5.2 `Tenant Policy`

### Admin
- full access

### Ops
- read only by default

### Support
- read only

### Sales
- read maybe limited/high-level only if useful
- otherwise no need

### Finance
- read only if pricing/plan logic depends on policy visibility

### Recommendation
Policy editing should be tightly restricted.
This DocType shapes platform behavior.

---

## 5.3 `Tenant Environment`

### Admin
- full access
- all actions

### Ops
- read/write operational fields
- run most lifecycle actions
- no unrestricted raw field editing outside intended workflow if possible

### Support
- read
- run non-destructive checks only
- no major lifecycle actions

### Sales
- read selected summary fields only if feasible
- otherwise limited normal read via form/list filtering or reports

### Finance
- read summary and cost-related context
- not operational mutation

### Recommendation
Use explicit server actions to control dangerous changes.
Do not rely on broad write permission alone.

---

## 5.4 `Tenant Transition Log`

### Admin
- read
- no normal editing after insert

### Ops
- read
- no normal editing after insert

### Support
- read

### Sales
- usually no need for full log access
- maybe summary visibility only through linked records

### Finance
- usually no need except high-level context

### Recommendation
This should behave as append-only.
Editing/deleting should be extremely restricted or forbidden.

---

## 5.5 Snapshot / support DocTypes

### `Tenant Subscription`
- Admin: full
- Ops: read
- Support: read
- Sales: read/write depending on workflow
- Finance: strong read, likely limited write

### `Tenant Usage Snapshot`
- Admin: read
- Ops: read/trigger refresh
- Support: read
- Sales: read summary only if useful
- Finance: read

### `Tenant Cost Snapshot`
- Admin: read
- Ops: read/trigger refresh
- Support: read
- Sales: maybe read summary only
- Finance: strong read

### `Tenant Health Check`
- Admin: read
- Ops: read/create via checks
- Support: read/create via checks if allowed
- Sales: no need
- Finance: no need

### `Tenant Incident` / `Tenant Alert Log`
- Admin: read/write status
- Ops: read/write status
- Support: read/write acknowledgment maybe
- Sales: no need or summary only
- Finance: summary only if tied to subscription risk

---

# 6. Sensitive actions matrix

This is the most important part.

Permissions should be centered around actions, not just record CRUD.

| Action | Admin | Ops | Support | Sales | Finance |
|---|---|---|---|---|---|
| Create Sandbox | Yes | Yes | No | Maybe by workflow | No |
| Reset Sandbox | Yes | Yes | No | No | No |
| Expire Sandbox | Yes | Yes | No | No | No |
| Reactivate Sandbox | Yes | Yes | No | No | No |
| Qualify for Production | Yes | Yes | No | Maybe request only | No |
| Provision Production | Yes | Yes | No | No | No |
| Mark Live | Yes | Yes | No | No | No |
| Suspend Environment | Yes | Yes | No | No | No |
| Restore Environment | Yes | Yes | No | No | No |
| Archive Environment | Yes | Yes | No | No | No |
| Run Health Check | Yes | Yes | Yes | No | No |
| Refresh Usage Snapshot | Yes | Yes | Yes | No | Yes if needed |
| Refresh Cost Snapshot | Yes | Yes | Yes | No | Yes |
| Sync Routing Intent | Yes | Yes | No | No | No |
| Rotate DB Credentials | Yes | Maybe | No | No | No |
| Edit Tenant Policy | Yes | No | No | No | No |

## Notes
- “Maybe” means internal process choice, not default grant.
- `Rotate DB Credentials` should likely remain Admin-only early unless Ops is highly trusted.
- `Archive Environment` should remain tightly controlled because it is near-terminal.

---

# 7. Field-level sensitivity categories

Rather than micro-managing every field immediately, think in sensitivity classes.

## 7.1 Public-internal operational fields
Examples:
- tenant name
- environment type
- site status
- primary domain
- region
- health score
- capacity state

These can usually be widely visible to internal roles.

## 7.2 Commercial-sensitive fields
Examples:
- pricing
- contract dates
- renewal notes
- internal commercial commentary
- estimated margin logic

These may be readable by Admin, Sales, Finance, and maybe Ops.

## 7.3 Infrastructure-sensitive fields
Examples:
- DB host
- DB user
- credential references
- routing internals
- internal namespace/cluster detail
- security notes

These should be more tightly controlled.

## 7.4 High-trust operator fields
Examples:
- database mode
- hosting tier override
- production provisioning inputs
- suspension reason
- archive decisions
- policy assignment overrides

These should be mutated only through trusted actions.

---

# 8. Audit expectations by role

Permissions do not remove the need for logging.

The following actions should always be attributable to a user:

- create sandbox
- reset sandbox
- expire/reactivate sandbox
- qualify for production
- provision production
- mark live
- suspend/restore/archive environment
- change DB mode
- change hosting tier
- edit policy
- rotate DB credentials
- update subscription commercially

This matters especially because the system is internal.
Internal control without audit becomes informal and fragile fast.

---

# 9. Small-team reality

In the beginning, your real team may be small.

That is fine.

A small team may temporarily have:
- one Admin
- one or two people effectively acting as Ops + Sales + Finance

But the permission model should still be designed now so the system does not assume:
- everyone is root
- every operator should see everything
- every operator should mutate everything

The team can start with broader grants operationally, while the model remains disciplined.

---

# 10. Recommended first implementation

Keep v1 simple.

## Create these roles first
- Ifitwala Press Admin
- Ifitwala Press Ops
- Ifitwala Press Support
- Ifitwala Press Sales
- Ifitwala Press Finance

## Enforce strongly first
- Policy editing restrictions
- Lifecycle action restrictions
- Archive/suspend restrictions
- production provisioning restrictions
- transition log append-only behavior

## Defer finer polish if needed
- elaborate field-level permissioning
- special-case read filters
- row-level nuanced commercial separation

That can come later.

---

# 11. What to avoid

Avoid these mistakes:

### 11.1 Everyone is admin
Fast early, painful later.

### 11.2 CRUD-only permission thinking
This platform lives through actions, not just CRUD.

### 11.3 Overcomplicated role explosion
Do not invent 15 roles before real need exists.

### 11.4 Unlogged high-risk actions
A control plane without attributable action history is not serious.

### 11.5 Pure UI hiding as security
The server must still enforce authority.

---

# 12. Final design position

Ifitwala_Press permissions should be:

- internal
- pragmatic
- action-centered
- operator-safe
- auditable
- simple enough to run
- strong enough to prevent careless damage

The first role model is:

- Admin
- Ops
- Support
- Sales
- Finance

The most important restriction boundary is not record visibility.
It is **who can perform critical control-plane actions**.
