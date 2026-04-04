# AGENTS.md — Ifitwala_Press Repository Constitution

## Purpose

Ifitwala_Press is an **internal-only Frappe control plane** operated by our own team.

It exists to manage, monitor, and operate **all customer tenants of Ifitwala_Ed** on **Google Cloud**.

It is inspired by the architectural logic of Frappe Press, but it is **not** a generic clone and it is **not** a public platform for third parties to administer themselves.

Its job is to help us:

- provision and manage tenant environments for Ifitwala_Ed
- operate a **site-per-school** multi-tenant architecture
- separate **shared application runtime** from **tenant databases**
- support **sandbox**, **standard production**, and **VIP / premium** hosting models
- monitor **tenant health, capacity, usage, costs, and subscriptions**
- support safe lifecycle transitions from demo/trial to production
- give operators a clear internal console for action, diagnosis, and governance
- prepare for later integration with **Traefik** for hostname-based routing

This repository is for the **internal operating system of our hosted ERP fleet**.

---

## What Ifitwala_Press Is

Ifitwala_Press is:

- a **Frappe app first**
- an **internal control plane**
- an **operator console**
- a **tenant lifecycle and hosting governance system**
- a **platform monitoring and cost visibility layer**
- a **future routing / provisioning orchestrator**

It is not:

- a customer-facing portal
- a generic cloud hosting product
- a generic PaaS
- a general DevOps playground
- a dumping ground for unrelated ERP features

---

## Core Product Position

Ifitwala_Press is the system we use to run all hosted Ifitwala_Ed tenants.

That means it must model and govern:

- tenant identity
- tenant commercial state
- tenant environment lifecycle
- hosting tier
- isolation model
- database placement
- routing intent
- backup / retention policy
- health and capacity status
- usage
- costs
- subscription state
- audit trail of operator actions and lifecycle transitions

If a proposed feature does not strengthen that mission, challenge it.

---

## Locked Infrastructure Baseline

Until explicitly revised in this repository, the operating baseline is:

- **MariaDB 11.4** only
- **Google Cloud Storage (GCS)** as the only current object-storage provider
- **Google Cloud DNS** as the default DNS authority
- **Google Cloud** as the default production provider
- **OVH** as an optional later sandbox/runtime placement provider, not the production default
- **Ubuntu 24.04 LTS** as the founder-host baseline

Additional launch-gate rules are also locked:

- the current per-environment founder Docker stack is acceptable only for small pilot cohorts
- manually approved demo environments must not default to a full heavy per-environment runtime
- shared runtime placement is the default target for demo and many smaller-school environments
- dedicated runtime placement is reserved for VIP, high-concurrency, or incompatible app-bundle tenants
- no environment is operationally ready until off-runtime backup export and at least one restore rehearsal have been proven

## Founder-stage operating model

Ifitwala_Press is **not** a public self-serve platform.

Current operating model:
- interested schools are reviewed manually by the founder
- the founder decides which prospects receive a demo environment
- demo/sandbox environments are provisioned under founder control from Ifitwala_Press
- there is no public self-serve signup or automatic external provisioning flow

Architecture implications:
- do not design for a mass free-trial fleet
- do not introduce Kubernetes or GKE
- do not assume public onboarding pipelines
- use VM + Docker / Docker Compose + Press-governed lifecycle
- keep the system modeled on Frappe Press, Frappe Agent, and frappe_docker
- treat the current demo phase as a controlled founder-managed demo workflow

When writing notes, proposals, or code guidance, describe the system as:
- an internal control plane
- for a small number of manually approved demo tenants
- with later conversion to paying production tenants

Agents must not:

- reintroduce AWS, S3, Cloud SQL, RDS, or Amazon terminology unless the task is explicitly about comparison or migration
- drift the database baseline away from MariaDB 11.4
- describe GCS as "S3 storage" at the architecture or contract layer

---

## Non-Negotiable Architectural Principles

### 1. Frappe app first
Ifitwala_Press must be built as a proper Frappe app with:

- DocTypes
- validations
- server-authoritative actions
- permissions
- logs
- auditable workflows
- clear operator surfaces

Do not build the platform as a loose pile of shell scripts with a thin admin UI added later.

### 2. Site-per-school tenancy
The tenancy model is:

- **1 customer institution = 1 tenant**
- **1 tenant environment = 1 Frappe site**
- **1 site = 1 database**

Do not design around row-level multi-tenancy inside one big shared customer database.

### 3. Shared runtime, separated state
The intended architecture is:

- shared immutable app/runtime image containing `frappe` + `ifitwala_ed`
- separated database layer
- separated cache / queue / realtime services
- separated file/object storage
- hostname-based routing

Do not tightly couple the app layer to a specific tenant database or to local persistent storage.

### 4. Hybrid hosting model
Not all tenants get the same infrastructure profile.

The intended model is:

- **Sandbox / Trial**
  Cheap, disposable, shared infrastructure, usually demo data

- **Standard Production**
  Shared runtime is the default for many smaller schools, with **one database per site**

- **Premium / VIP Production**
  Shared or reserved runtime, but typically **dedicated database instance per tenant**
  Dedicated runtime is appropriate for VIP, high-concurrency, or incompatible app-bundle tenants

Do not push every tenant into dedicated infrastructure from day one.
Do not trap all tenants forever in one undifferentiated shared setup either.

### 5. Sandbox and production are different classes of environment
A sandbox is:

- cheap
- resettable
- disposable
- lower-SLA
- limited in quota
- designed for trials, demos, and evaluation

Production is:

- backed up
- monitored
- contract-ready
- operationally governed
- safer by default
- designed for real school operations

Do not casually blur the line between sandbox and production.

### 6. Fresh production by default
Default rule:

- **do not promote a sandbox in place unless explicitly justified**

Preferred flow:

- sandbox is used for trial/evaluation
- production is provisioned cleanly
- selected configuration and approved data may be copied forward

Never assume demo/test junk should become part of a live school environment.

### 7. Traefik-ready, not Traefik-hardcoded
We expect to use **Traefik later** for hostname-based routing.

The control plane must store:

- domain intent
- routing metadata
- readiness state
- TLS/DNS state

But it must not prematurely hardcode all architecture to one proxy implementation.

Ifitwala_Press owns **routing intent**.
The infra layer later applies that intent via Traefik / shared founder edge proxy / deployment adapters.

### 8. Safety over convenience
This platform manages real school customers and potentially sensitive/VIP institutions.

Every design choice must be evaluated against:

- tenant isolation
- blast radius
- data safety
- recoverability
- auditability
- migration safety
- operational clarity

If something is easier but weakens safety or traceability, reject it.

### 9. Operator-first design
Because Ifitwala_Press is for us, the platform must optimize for:

- fast diagnosis
- clear state visibility
- safe manual override paths
- auditable admin actions
- usage and cost visibility
- subscription oversight
- low cognitive load for operators

Do not design this like a public SaaS admin interface.
Design it like a serious internal control room.

### 10. Control-plane home discipline
The first landing surface for operators should be a real control-plane home, not only a static workspace.

That home should:
- summarize current tenant and environment posture
- show a short attention queue
- link directly to the underlying tenant or environment records
- reuse explicit summary fields already modeled in DocTypes

It must not:
- become a fake orchestration layer
- invent hidden state outside the core DocTypes
- expose data through client-only permission checks

Any read API that powers dashboard, panel, or summary surfaces must enforce server-side role checks just like write actions do.

### 11. Press and Agent borrowing discipline
When this repository borrows ideas from Frappe Press and Frappe Agent, the borrowing boundary must stay explicit.

Borrow from Press now:
- explicit action names
- operator-visible progress
- attention-oriented control-plane landing surfaces
- server-authoritative lifecycle and operational actions

Do not borrow from Agent yet:
- remote host execution inside Desk pages
- hidden host orchestration in client scripts
- implicit SSH-style side effects disguised as UI refreshes

Until remote execution becomes a real product need, Agent remains a later boundary, not a behavior to simulate inside the control plane app.

---

## Repository Operating Rule

**Do not invent. Do not assume. Do not drift.**

When working in this repository, agents must never:

- invent DocTypes, fields, routes, statuses, or workflows without grounding them in the current project model
- assume generic Press/Frappe Cloud behavior automatically applies here
- introduce infrastructure features detached from the control-plane design
- widen scope into unrelated Ifitwala_Ed product features
- bury critical operational logic in hidden scripts
- normalize away architectural contradictions instead of fixing them

Agents must always:

- work from the current repo files and current agreed architecture
- preserve the internal control-plane model
- keep lifecycle and environment concepts explicit
- prefer server-authoritative actions over freeform edits
- preserve auditability
- keep commercial, operational, and technical state clearly modeled

### Worktree and index discipline

When fixing a staged-file failure such as a commit hook or parse error, agents must verify the exact file content seen by both the worktree and the git index before declaring the issue fixed.

Minimum rule:
- after `apply_patch`, re-read the exact changed lines from the worktree
- if the file is tracked and the fix must affect a commit, verify the staged blob too, for example with `git show :path`
- if the index still has stale content, stage the file and verify again before rerunning hooks or telling the user the fix is ready
- do not rely on memory or a prior patch success message when the hook output still shows old code

---

## Intended Platform Model

Ifitwala_Press is our internal operating system for all hosted Ifitwala_Ed tenants.

At minimum, it must eventually know per tenant:

- who the customer is
- what environments exist
- what lifecycle state each environment is in
- which site/domain belongs to that environment
- what hosting tier applies
- which database mode applies
- where the environment is deployed
- what policy and quota apply
- how much it is costing
- how much it is being used
- what subscription/commercial state it is in
- whether it is healthy, degraded, saturated, or failing

If a feature bypasses this model, it is suspect.

---

## Core Domain Objects

These are the intended first-class objects.

### Core DocTypes
- `Press Tenant`
- `Tenant Environment`
- `Tenant Policy`
- `Tenant Transition Log`

### Support / likely early follow-up DocTypes
- `Tenant Environment Domain`
- `Tenant Health Check`
- `Tenant Subscription`
- `Tenant Usage Snapshot`
- `Tenant Cost Snapshot`
- `Tenant Incident` or `Tenant Alert Log`

Agents must not collapse these into one giant table “for simplicity.”

---

## Tenant and Environment Distinction

This distinction is mandatory.

### `Press Tenant`
Represents the institution/customer/prospect as a managed customer entity.

It should hold:
- identity
- commercial data
- sensitivity flags
- default hosting intent
- plan/subscription summary
- internal ownership

### `Tenant Environment`
Represents one actual operational environment.

It should hold:
- sandbox / production / staging type
- site name
- lifecycle state
- hosting placement
- database placement
- routing/domain data
- health / capacity state
- storage / backup / infra metadata

Do not merge customer identity and environment state into one sloppy object.

---

## Lifecycle Model

Lifecycle state must be explicit and governed.

The agreed environment state model includes:

- Lead
- Sandbox Provisioning
- Sandbox Active
- Sandbox Expired
- Production Qualification
- Production Provisioning
- Live
- Suspended
- Archived
- Provisioning Failed

This is not decorative UI.
This is the backbone of the platform.

State must drive:
- provisioning behavior
- reset behavior
- expiry behavior
- promotion behavior
- suspension behavior
- archive behavior
- policy enforcement
- operational visibility

### Transition discipline
Agents must not allow arbitrary state jumps without explicit design approval.

State transitions should be modeled as controlled server-side actions, with logging.

---

## Internal Hosting Strategy

The current intended hosting strategy is:

### Shared immutable application layer
- one shared application/runtime image
- app layer contains `frappe` and `ifitwala_ed`
- runtime is reused across many tenants

### Tenant-separated database layer
- one database per site
- default production = shared HA DB fleet
- premium/VIP = dedicated DB instances where appropriate

### Hosting tiers
- Sandbox
- Standard
- Premium
- VIP

### Promotion path
- most prospects begin in sandbox/trial
- qualified customers move to governed production environments
- heavier or more sensitive customers can be placed on more isolated DB infrastructure

This is the strategic model unless explicitly revised.

---

## Monitoring, Usage, Cost, and Subscription Intent

Because Ifitwala_Press is for internal operations, these concerns are first-class, not optional extras.

The system must be designed to track and surface:

### Usage
Examples:
- active users
- storage consumption
- file volume
- request volume
- worker/queue load
- concurrency patterns
- growth over time

### Costs
Examples:
- estimated infra cost by tenant
- DB cost
- storage cost
- compute allocation cost
- backup cost
- premium isolation cost

### Subscriptions / plans
Examples:
- current plan
- contract status
- trial vs paid
- renewal / expiry
- feature entitlements
- overage / upgrade signals

### Operational health
Examples:
- uptime/availability indicators
- queue backlog
- slow queries
- error rates
- backup freshness
- saturation warnings
- failed provisioning attempts

Agents must not treat these as afterthoughts.

---

## Frappe Engineering Rules

### 1. Server-authoritative lifecycle actions
Critical actions must be server-side, explicit, and auditable.

Examples:
- create sandbox
- reset sandbox
- expire sandbox
- qualify for production
- provision production
- suspend environment
- restore environment
- archive environment
- run health check
- sync routing intent
- rotate credentials
- refresh usage snapshot
- refresh cost snapshot

Do not rely on manual status editing as the primary mechanism.

### 2. DocTypes are operational contracts
Every core DocType is part of a control-plane contract.

That means:
- names matter
- fields matter
- statuses matter
- transitions matter
- validations matter
- indexes matter
- permissions matter

Avoid vague fields and catch-all blobs unless absolutely necessary.

### 3. Validation is mandatory
Any field affecting:
- site identity
- routing/domain
- hosting tier
- database placement
- environment state
- quotas
- costs
- subscription logic

must be validated on the server.

Never trust client-only enforcement for critical control-plane behavior.

### 4. Never fail silently
If provisioning, routing sync, state transition, monitoring, backup validation, or credential rotation fails:

- record it
- expose it
- log it
- move to an explicit failure or warning state when appropriate

Silent failure is unacceptable in a control plane.

### 5. Auditability is mandatory
Important actions and transitions must leave a durable trace.

If an operator or job changes:
- lifecycle state
- deployment intent
- tier
- domain/routing
- database placement
- policy
- quota
- suspension/archive state

that change must be attributable.

---

## Infrastructure Modeling Rules

### 1. Model intent first
We target Google Cloud, and likely later:
- Traefik
- founder runtime adapters
- Docker Compose-managed runtimes
- GCS

But the Frappe data model must describe **control-plane intent first**, not bury infrastructure assumptions everywhere.

Bad:
- random hardcoded Traefik specifics in unrelated business logic
- embedding one infrastructure provider’s current object shape directly into every DocType

Better:
- store clear routing, hosting, and placement intent
- translate intent to infra implementation via services/adapters later

### 2. Shared vs dedicated must be explicit
If an environment is:
- shared DB
- dedicated DB
- shared runtime
- reserved runtime
- dedicated runtime

that must be represented explicitly in the model.

Do not rely on naming conventions or hidden assumptions.

### 3. Sandboxes must be easy to kill or reset
Any architecture that makes sandbox expensive, sticky, or hard to recycle is wrong.

### 4. Production must be recoverable
Production design must support:
- backup policy
- restore path
- tenant-specific isolation
- safe transition handling
- operational clarity

---

## Permission and Role Philosophy

Because this system is internal-only, permissions should optimize for safety and clarity, not public extensibility theater.

Likely operator roles may include:
- Ifitwala Press Admin
- Ifitwala Press Ops
- Ifitwala Press Sales
- Ifitwala Press Support
- Ifitwala Press Finance / Billing

But keep the model pragmatic.
Do not overcomplicate permissions for imaginary external users.

The main goal is:
- protect sensitive actions
- separate commercial visibility from infra write access where useful
- preserve audit trails

---

## Scope Discipline

This repo is for **Ifitwala_Press** only.

Do not drift into building:
- unrelated school workflows from Ifitwala_Ed
- generic CRM unrelated to tenant operations
- generic accounting systems
- random infrastructure tools with no control-plane connection
- overbuilt automation before the data model is sound

If a feature is proposed, ask:

1. Does it improve tenant governance?
2. Does it improve environment lifecycle management?
3. Does it improve monitoring / usage / cost / subscription visibility?
4. Does it improve operator clarity and safety?
5. Does it fit the internal control-plane mission?

If not, push back.

---

## Expected Agent Behavior

### Product / architecture agents
Must protect:
- tenant/environment separation
- hosting tier model
- hybrid DB isolation strategy
- sandbox vs production distinction
- lifecycle clarity
- operator-first usability
- internal business visibility on costs/usage/subscriptions

### Engineering agents
Must protect:
- DocType integrity
- server-side validation
- audited state transitions
- clear service boundaries
- explicit infra intent modeling
- reliable failure handling

### Review agents
Must challenge:
- vague statuses
- hidden coupling
- accidental cross-tenant risk
- silent failures
- schema sloppiness
- premature infra hardcoding
- shortcuts that weaken auditability

### Documentation agents
Must keep docs aligned with:
- actual DocTypes
- actual lifecycle states
- actual hosting model
- actual operator workflows
- actual cost / usage / subscription logic

---

## Early Build Priorities

Do not start by automating everything.

The right build order is:

1. lock the control-plane data model
2. lock lifecycle states and transitions
3. lock policy model
4. lock tenant/environment distinction
5. lock usage / cost / subscription tracking model
6. implement manual but server-authoritative actions
7. only then add deeper automation

Agents must resist jumping straight into infrastructure scripting before the platform model is coherent.

---

## What Good Work Looks Like

Good work in this repo:

- sharpens the tenant model
- sharpens the environment model
- makes lifecycle more deterministic
- improves operator visibility
- makes costs and usage more legible
- improves subscription governance
- strengthens auditability
- clarifies routing/hosting/database intent
- prepares for Traefik and cloud automation without hardcoding prematurely

Bad work in this repo:

- blurs sandbox and production
- mixes customer identity and environment state
- hides critical actions behind manual edits
- adds status clutter instead of real state discipline
- ignores cost/usage/subscription visibility
- invents generic abstractions detached from the project
- overbuilds automation before the control-plane contracts are locked

---

## Final Rule

Ifitwala_Press must be built as a serious internal control plane for operating all hosted Ifitwala_Ed tenants.

Not a toy dashboard.
Not a vague Press imitation.
Not an ad hoc admin tool.

Every change must move the system toward:

- explicit tenancy
- explicit environment governance
- explicit lifecycle
- explicit hosting tier logic
- explicit monitoring
- explicit cost visibility
- explicit subscription oversight
- explicit auditability
- explicit recoverability
- explicit operator control
