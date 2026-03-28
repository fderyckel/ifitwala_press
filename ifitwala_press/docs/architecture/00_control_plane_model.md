# 00_control_plane_model.md

## Purpose

This document locks the current architectural direction for **Ifitwala_Press** as an internal control plane for operating hosted **Ifitwala_Ed** tenant environments.

The purpose of this document is to define:

- what the platform is responsible for
- the tenant and environment model
- the lifecycle model
- the hosting tier model
- the database isolation model
- the sandbox-to-production conversion model
- the routing ownership boundary
- the operational intent for monitoring, usage, costs, and subscriptions

This is a design-lock document.
It should not be changed casually.

---

## 1. Platform role

Ifitwala_Press is our internal operating system for hosted Ifitwala_Ed environments.

Its job is to let our team:

- manage all customer tenants
- govern tenant environment lifecycle
- choose and record hosting tier and isolation level
- monitor health and capacity
- track usage, cost, and subscription state
- support safe movement from trial to production
- later orchestrate routing and provisioning actions

This is an **internal operator platform**, not a customer-facing portal.

---

## 2. Core architectural idea

The platform follows a **Press-like control-plane model** adapted for our own narrow use case.

The guiding idea is:

- one shared application/runtime layer
- many isolated tenant sites
- separated tenant databases
- externalized state services
- internal control plane managing lifecycle and operations

This is different from:
- putting each customer on a fully separate stack from day one
- placing all customers in one shared database
- building a generic public cloud platform

---

## 3. Tenant model

### 3.1 Tenant
A **tenant** is the customer institution as a managed entity.

Examples:
- one school
- one international school
- one small independent university
- one prospect institution during trial stage

A tenant is the business and operational identity of the customer.

A tenant should hold:
- customer identity
- commercial state
- plan/subscription information
- sensitivity/VIP flags
- estimated size
- default hosting intent
- internal ownership

### 3.2 Environment
An **environment** is one actual deployed operational instance for a tenant.

Examples:
- sandbox
- production
- later possibly staging

An environment should hold:
- site name
- environment type
- lifecycle state
- database placement
- hosting placement
- routing/domain metadata
- health/capacity information
- storage/backup metadata

### 3.3 Mandatory distinction
Tenant and environment are not the same thing.

This distinction is mandatory.

A single tenant may have:
- one sandbox environment
- one production environment
- later one staging environment

Therefore the model must not collapse customer identity and environment state into one object.

---

## 4. Site-per-school tenancy

The baseline tenancy model is:

- 1 institution = 1 tenant
- 1 environment = 1 Frappe site
- 1 site = 1 database

This aligns with Frappe’s site-based multi-tenancy model and gives a cleaner isolation boundary than row-level multi-tenancy.

### Why this model
It gives us:

- clear tenant isolation
- cleaner backup/restore boundaries
- easier blast-radius control
- easier upgrade/promotion path
- simpler future VIP isolation
- better alignment with operational reality

This model is the default unless explicitly revised.

---

## 5. Hosting architecture model

### 5.0 Deployment surfaces
The platform has three distinct surfaces:

- the public brand/docs site
- the internal operator control plane
- the tenant runtime surface

The public site and the control plane must not be the same Frappe site.

The expected hostname shape is:

- `ifitwala.com` for the public site
- `press.ifitwala.com` for the control plane
- `*.ifitwala.com` for tenant environments

Host-level separation is recommended early.
Site-level separation is mandatory.

### 5.1 Shared runtime, separated state
The intended architecture is:

- shared immutable application/runtime image
- separated database layer
- separated cache / queue / realtime services
- separated file/object storage
- hostname-based routing

The app/runtime layer contains:
- `frappe`
- one managed app bundle

It is reused across many tenants.

That managed app bundle may include:
- `ifitwala_ed`
- `ifitwala_drive`
- other approved `ifitwala_*` apps
- approved tenant-specific customization apps

### 5.1A Managed app bundle discipline
The control plane must treat runtime app composition as governed infrastructure intent.

That means:
- app code is baked into immutable Docker images
- running production containers must not be mutated with ad hoc `bench get-app` or similar manual installs
- each environment must be assigned to an approved app bundle and release
- the site-level installed app set must remain explicit and auditable
- tenants may share a runtime pool only when their assigned app bundle is compatible with that pool

This preserves flexibility without turning production into a mutable pet-server model.

### 5.1B Target architecture vs current deployment mode
The control-plane model is locked before the infrastructure implementation is mature.

That means:
- the target architecture remains shared runtime plus separated state layers
- the early implementation may run on a simpler self-managed stack
- temporary consolidation for cost reasons is acceptable in founder stage
- the control plane must still record intended placement and separation clearly
- the public site and the control plane must remain separate sites even in founder mode

Early deployment convenience must not blur the model.
The model should stay migration-friendly even when the first runtime is simple.

### 5.2 Separated state layers
Tenant-specific state should live outside the app image:

- databases
- redis/cache/queue/socket services
- object/file storage, with GCS split into frequent-access live files and less-frequent retained backups
- environment config
- routing config

This is a control-plane architecture, not a pet-server architecture.

### 5.3 Cash-efficiency principle
Until revenue, contractual obligations, and uptime commitments justify stronger infrastructure, deployment choices should optimize for low fixed cost while preserving clean migration paths to stronger isolation later.

Cheap early implementation is acceptable.
Architecture drift is not.

Broad free-trial economics still matter.
Do not assume the current heavy per-environment founder stack is the default long-term demo posture.

---

## 6. Hosting tiers

The current intended hosting tiers are:

### 6.1 Sandbox / Trial
Purpose:
- low-cost demos
- trials
- internal previews
- low-risk evaluation

Characteristics:
- cheap
- disposable
- resettable
- quota-limited
- lower SLA
- usually demo/fake data
- short-lived unless converted

Likely infra pattern:
- shared runtime
- shared DB fleet
- one database per site
- one approved shared app bundle or compatibility pool
- limited storage and worker budget

### 6.2 Standard Production
Purpose:
- normal live customer deployment

Characteristics:
- governed production state
- backups
- monitoring
- stronger operational discipline
- shared but controlled infrastructure

Likely infra pattern:
- shared runtime
- shared DB fleet
- one database per site
- shared runtime only for tenants on compatible approved app bundles

### 6.3 Premium / VIP Production
Purpose:
- higher-value, higher-risk, or more sensitive institutions

Characteristics:
- stronger isolation
- more explicit support guarantees
- cleaner incident boundaries
- better premium commercial positioning

Likely infra pattern:
- shared or reserved runtime
- dedicated database instance per tenant
- reserved or dedicated runtime when tenant-specific app combinations no longer fit a safe shared compatibility pool
- stronger backup and monitoring policies

### Why tiering matters
Not all customers should be treated the same.

Tiering lets us balance:
- cost efficiency
- operational simplicity
- tenant isolation
- premium upsell
- noisy-neighbor management
- VIP trust requirements

---

## 7. Database isolation model

### 7.1 Default rule
The default model is:

- **one database per site**

This is true across sandbox and production environments.

### 7.2 Shared vs dedicated database placement
The main strategic choice is not whether tenants have separate databases.
They should.

The real choice is **where those databases live**.

#### Shared DB fleet
Used by default for:
- sandbox
- standard production
- normal-sized customers

Meaning:
- multiple tenant databases on a shared DB fleet
- cost-efficient
- operationally simpler
- acceptable when monitored carefully

#### Dedicated DB instance
Used for:
- VIP customers
- larger schools
- sensitive institutions
- customers that justify stronger isolation

Meaning:
- one tenant database on a dedicated database instance
- higher cost
- stronger isolation
- cleaner blast-radius boundaries

### 7.2A Provider-agnostic placement
One database per site remains locked.

Database placement may be implemented as:
- self-managed shared VM or cluster
- managed shared instance
- dedicated self-managed instance
- dedicated managed instance

The control plane should model placement intent first.
Specific providers are an implementation choice, not the architectural contract.

### 7.3 Strategic position
The intended architecture is hybrid:

- cheap sandboxes
- shared HA production by default
- dedicated DB for premium/VIP where justified

This is the current design lock.

---

## 8. Sandbox vs production policy

Sandbox and production are not equivalent.

### 8.1 Sandbox rules
A sandbox should be:
- easy to provision
- easy to reset
- easy to expire
- cheap to operate
- safe to discard

A sandbox should not automatically inherit production expectations.

### 8.2 Production rules
A production environment should be:
- explicitly qualified
- cleanly provisioned
- auditable
- monitored
- backed up
- policy-driven

### 8.3 Default conversion policy
Default rule:

- **do not convert sandbox in place unless explicitly justified**

Preferred path:

- sandbox is used for evaluation
- production is provisioned cleanly
- selected config and approved data may be copied forward

### Why this matters
This avoids:
- demo junk in production
- unsafe defaults leaking into live environments
- accidental carryover of test users, fake records, or poor structure

---

## 9. Lifecycle model

The environment lifecycle must be explicit.

The current intended states are:

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

### 9.1 Meaning of lifecycle
Lifecycle state must drive:
- provisioning behavior
- reset behavior
- expiry behavior
- qualification behavior
- production provisioning behavior
- suspension/archive behavior
- audit trail expectations

### 9.2 Failure must be explicit
Failures must not disappear into logs only.

If provisioning or a critical transition fails, the control plane should reflect that in explicit state and logging.

---

## 10. Routing ownership and Traefik boundary

We expect to use **Traefik later** for hostname-based routing.

### 10.1 What Ifitwala_Press owns
Ifitwala_Press should own:
- primary domain intent
- alternate domain metadata
- DNS readiness state
- TLS readiness state
- routing status/intent
- environment-to-domain relationship

### 10.2 What infra later owns
The infra layer can later translate that intent into:
- Traefik config
- Kubernetes Ingress
- Docker labels
- certificates
- routing resources

### 10.3 Principle
Ifitwala_Press owns **routing intent**.
Infrastructure automation owns **routing implementation**.

This separation reduces hard coupling too early.

---

## 11. Monitoring, usage, cost, and subscription model

Because this is an internal operator platform, these are first-class concerns.

### 11.1 Usage
The platform should eventually support tracking metrics such as:
- active users
- login volume
- storage usage
- file counts
- queue/worker activity
- request volume
- growth over time
- estimated peak concurrency

### 11.2 Costs
The platform should eventually support tracking:
- estimated DB cost
- storage cost
- runtime/compute cost
- backup cost
- premium isolation cost
- total estimated tenant cost

### 11.3 Subscriptions
The platform should eventually support tracking:
- trial vs paid
- subscription tier
- renewal/expiry
- add-ons
- upgrade signals
- contract status

### 11.4 Health
The platform should eventually support:
- environment health score
- capacity state
- queue backlog warnings
- slow query warnings
- backup freshness checks
- provisioning failure visibility
- alert/incidents history

These are not optional extras.
They are part of the purpose of the control plane.

---

## 12. Operator-first design

The users of Ifitwala_Press are our internal team.

That means the platform should optimize for:

- fast diagnosis
- safe operational actions
- strong visibility
- low cognitive load
- clear tenant summaries
- sharp environment summaries
- clear failure surfaces
- clear cost and subscription signals

It should not be designed like a public admin portal with fake extensibility for external users.

---

## 13. Core first-class records

The current intended first-class records are:

### Core
- `Press Tenant`
- `Tenant Environment`
- `Tenant Policy`
- `Tenant Transition Log`

### Early follow-up
- `Tenant Environment Domain`
- `Tenant Health Check`
- `Tenant Subscription`
- `Tenant Usage Snapshot`
- `Tenant Cost Snapshot`
- `Tenant Incident` or `Tenant Alert Log`

This is the current conceptual backbone.

---

## 14. Current implementation order

The recommended implementation order is:

### First
- lock domain model
- lock lifecycle states
- lock hosting tier logic
- lock tenant/environment distinction

### Then
- implement the first 4 core DocTypes
- make transitions server-authoritative
- add validations and audit logging

### Then
- add usage / cost / subscription support
- add health checks and domain records

### Only after that
- deeper provisioning automation
- deeper routing automation
- richer infra synchronization

This ordering is deliberate.
Automation before model clarity will create drift.

---

## 15. Final design position

Ifitwala_Press is our internal control plane for all hosted Ifitwala_Ed customers.

It must be built around:

- explicit tenants
- explicit environments
- explicit lifecycle
- explicit hosting tiers
- explicit database placement
- explicit routing intent
- explicit health visibility
- explicit usage/cost/subscription tracking
- explicit auditability

That is the architectural direction currently locked.
