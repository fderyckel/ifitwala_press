# Ifitwala_Press

Ifitwala_Press is an internal-only **Frappe control plane** for operating hosted **Ifitwala_Ed** tenant environments on **Google Cloud**.

It is inspired by the architectural logic of Frappe Press, but it is intentionally narrower:
it exists only to manage **Ifitwala_Ed**-based environments for our own customers, including approved platform apps and tenant-specific customization apps.

## What it is

Ifitwala_Press is the internal operating system we use to:

- manage customer tenants
- provision and track tenant environments
- support sandbox, standard, and VIP hosting models
- monitor customer usage, costs, subscriptions, and operational health
- govern lifecycle transitions from trial to production
- prepare for routing and infra orchestration later, including Traefik-based hostname routing

## Deployment surfaces

The platform is expected to operate with three distinct surfaces:

- `ifitwala.com` as the public brand/docs front end
- `press.ifitwala.com` as the internal control plane
- `*.ifitwala.com` as tenant environment hostnames

The public site and the control plane must not be the same Frappe site.
They may temporarily share founder-stage infrastructure only if their isolation boundary remains explicit and operational risk is understood.

## What it is not

Ifitwala_Press is not:

- a customer-facing portal
- a generic cloud hosting platform
- a generic PaaS
- a clone of Frappe Press in full scope
- a place for unrelated Ifitwala_Ed school workflows

## Core architectural direction

### 1. Frappe app first
Ifitwala_Press is a real Frappe app with DocTypes, validations, permissions, server actions, and auditability.

### 2. Site-per-school multi-tenancy
The tenancy model is:

- 1 customer institution = 1 tenant
- 1 environment = 1 Frappe site
- 1 site = 1 database

### 3. Shared runtime, separated state
The intended hosting model is:

- shared immutable app/runtime image
- separated database layer
- separated cache / queue / realtime services
- separated object storage
- hostname-based routing

The runtime image is expected to carry a managed app bundle, not only `ifitwala_ed`.
That bundle may include:
- `ifitwala_ed`
- `ifitwala_drive`
- approved `ifitwala_*` platform apps
- approved school-specific customization apps

Those apps must be governed, versioned, and baked into images.
They must not be installed ad hoc into running production containers.

### 3.1 Current storage baseline
For the current rollout, tenant file storage is standardized on **Google Cloud Storage (GCS)**.

- live site files and attachments use the logical **Frequent Access** class
- retained site/database backups use the logical **Infrequent Access** class
- the storage contract is site-scoped and shared across approved apps in the site, including `ifitwala_ed` and `ifitwala_drive`
- daily backup exports must leave the runtime boundary and land in GCS
- no environment is ready until one off-runtime backup export and one restore rehearsal have been proven

### 4. Hybrid hosting strategy
Not all customers should get the same infrastructure.

The intended model is:

- **Sandbox / Trial**
  Cheap, disposable, shared infrastructure, normally with demo data
  Broad trials should favor shared demo density through a shared runtime pool, not a full heavy per-environment stack by default

- **Standard Production**
  Shared runtime remains the default for many smaller schools when app-bundle compatibility and observed capacity allow it
  One database per site remains mandatory

- **Premium / VIP Production**
  Stronger isolation, usually dedicated database instance per tenant
  Dedicated runtime is justified for VIP, high-concurrency, or incompatible app-bundle tenants

### 5. Sandbox is not production
A sandbox should be:

- easy to create
- cheap to operate
- easy to reset
- easy to expire
- safe to discard

Production should be:

- auditable
- monitored
- backed up
- contract-ready
- safer by default

### 6. Internal operator-first design
This system is for us, not for customers.

That means it must optimize for:

- operator clarity
- safe admin actions
- fast diagnosis
- cost visibility
- usage visibility
- subscription oversight
- lifecycle governance

## Current launch gate

The current founder runtime is acceptable for a small pilot cohort only.

This is a founder-managed demo phase for manually approved prospect environments.

Before a larger number of manually approved demo environments, the platform must hold these lines:

- Ubuntu 24.04 LTS for the founder host baseline
- MariaDB 11.4 as the documented database baseline
- GCS as the only current object storage provider
- Google Cloud DNS as the default DNS authority
- off-runtime backup export plus at least one successful restore rehearsal
- no default demo architecture that gives every manually approved sandbox a full heavy dedicated stack
- shared runtime pools must become the default placement target for demo and smaller-school environments

## Current product intent

Ifitwala_Press must eventually help us answer questions like:

- Which tenants are in sandbox, trial, production, or suspended states?
- Which tenants are expensive relative to their subscription?
- Which tenants are growing fast or saturating capacity?
- Which tenants are VIP and require stronger isolation?
- Which tenants are due for renewal, upgrade, or review?
- Which environments are unhealthy, degraded, or failing?
- Which provisioning or migration actions failed and why?

## Core domain objects

The current intended first-class objects are:

### Core
- `Press Tenant`
- `Tenant Environment`
- `Tenant Policy`
- `Tenant Transition Log`

### Likely early follow-up
- `Runtime Pool`
- `App Bundle`
- `App Release`
- `Tenant Environment App Assignment`
- `Tenant Environment Domain`
- `Tenant Health Check`
- `Tenant Subscription`
- `Tenant Usage Snapshot`
- `Tenant Cost Snapshot`
- `Tenant Incident` / `Tenant Alert Log`

## Lifecycle direction

The environment lifecycle is expected to include states such as:

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

State is not decorative.
It must drive real control-plane behavior.

## What Ifitwala_Press must track

At minimum, the platform will need to track per tenant:

- identity
- commercial state
- hosting tier
- site/environment records
- lifecycle state
- domain and routing intent
- database mode and placement
- usage
- costs
- subscription status
- operational health
- transition history

## Traefik

Traefik is expected later as the hostname-based routing layer.

Ifitwala_Press should own:

- routing intent
- domain metadata
- readiness state

The infra layer can later translate that into actual Traefik or ingress configuration.

## Current build priorities

The first priority is **not** full automation.

The first priority is to lock:

1. the control-plane domain model
2. lifecycle states and transitions
3. the hosting tier model
4. the tenant/environment distinction
5. the usage/cost/subscription model

Only after that should deeper provisioning and routing automation be added.

## Guiding principle

Ifitwala_Press must be built as a serious internal control plane for operating all hosted Ifitwala_Ed tenants.

Not a toy dashboard.
Not an ad hoc admin app.
Not a vague Press imitation.
