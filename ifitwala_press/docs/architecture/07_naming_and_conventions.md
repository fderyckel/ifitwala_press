# 07_naming_and_conventions.md

## Purpose

This document defines the naming and structural conventions for **Ifitwala_Press**.

A control plane gets messy fast when names drift.

If different contributors use different meanings for:
- tenant
- environment
- site
- policy
- tier
- status
- subscription
- health
- cost
- routing

then the system becomes hard to build, hard to operate, and hard to trust.

This document locks the first naming and modeling conventions so the codebase stays coherent.

This is a design-lock document.

---

## 1. Core naming principles

### 1.1 Prefer precise domain words over generic words
Good:
- Tenant
- Environment
- Policy
- Transition
- Subscription
- Usage Snapshot
- Cost Snapshot
- Health Check

Bad:
- Record
- Config
- Status Item
- System Object
- Deployment Data
- Customer Info Blob

Names must communicate operational meaning.

### 1.2 One concept, one name
If we choose a word for a concept, reuse it consistently.

Examples:
- use `tenant`, not sometimes `customer`, sometimes `client`, sometimes `school`
- use `environment`, not sometimes `instance`, sometimes `deployment`, sometimes `site record`
- use `policy`, not `profile`, `plan`, `config set`, and `template` interchangeably

### 1.3 Separate business identity from runtime identity
Use:
- `tenant` for customer/business identity
- `environment` for operational deployment
- `site_name` for the Frappe site itself
- `primary_domain` for routing identity

Do not collapse those terms.

### 1.4 Use names that survive scaling
Avoid names that only make sense in a tiny prototype.

Bad:
- `demo_server`
- `prod_box`
- `customer_db_type`
- `ops_data`

Good names should still make sense when there are dozens or hundreds of tenants.

---

# 2. Canonical vocabulary

These are the canonical words for the project.

## 2.1 Tenant
Meaning:
The customer institution as a managed entity.

Use for:
- customer identity
- commercial state
- plan/subscription context
- ownership
- risk/sensitivity

Do not use interchangeably with:
- environment
- site
- database
- domain

## 2.2 Environment
Meaning:
One operational environment for a tenant.

Examples:
- sandbox
- production
- staging

Use for:
- lifecycle state
- deployment placement
- DB mode
- routing state
- health/capacity

## 2.3 Site
Meaning:
The actual Frappe site name.

Use field name:
- `site_name`

Do not use `site` as a synonym for tenant or environment in documentation.

## 2.4 Policy
Meaning:
A reusable set of hosting/lifecycle defaults and limits.

Use for:
- quota defaults
- backup rules
- lifecycle rules
- support/monitoring level

Do not confuse with subscription plan.

## 2.5 Subscription
Meaning:
The commercial plan relationship with the customer.

Use for:
- trial vs paid
- billing cycle
- renewal
- price
- status

Do not use subscription to mean technical policy.

## 2.6 Hosting tier
Meaning:
The service/isolation level we give the tenant or environment.

Allowed values currently:
- Sandbox
- Standard
- Premium
- VIP

This is not the same as database mode.

## 2.7 Database mode
Meaning:
How the environment’s database is placed.

Allowed values currently:
- Shared DB Fleet
- Dedicated DB Instance

This is not the same as hosting tier, though related.

## 2.8 Deployment mode
Meaning:
How the app/runtime layer is allocated.

Allowed values currently:
- Shared Runtime
- Reserved Runtime
- Dedicated Runtime

This is not the same as DB mode.

## 2.8A Current deployment mode vs target architecture
We need words for both present operational reality and intended destination.

- `database_mode` = logical database placement intent
- `deployment_mode` = current runtime isolation level
- `db_provider` = actual provider or management class if tracked
- `placement_strategy` = coarse operator-facing placement decision

Do not treat target architecture language as proof that the current deployment already has that shape.

## 2.9 Lifecycle state
Meaning:
The current operational stage of the environment.

Use only the canonical environment state list.

## 2.10 Health
Meaning:
Technical condition and service quality.

Do not use health to mean lifecycle state or subscription status.

## 2.11 Cost
Meaning:
Estimated platform cost to operate a tenant/environment.

Do not confuse with subscription price or invoice value.

## 2.12 Routing intent
Meaning:
The desired domain/routing relationship the control plane owns.

Do not hardcode this to Traefik semantics in naming yet.

## 2.13 Deployment surface
Meaning:
The functional surface a hostname or site belongs to.

Canonical surfaces:

- public site
- control plane
- tenant runtime

Do not use one site to mean all three.

## 2.14 Hostname conventions
Use these hostname conventions unless explicitly revised:

- `ifitwala.com` for the public brand/docs surface
- `press.ifitwala.com` or `ops.ifitwala.com` for the internal control plane
- `*.ifitwala.com` for tenant environments

Do not place the control plane on the same hostname or Frappe site as the public website.

---

# 3. Canonical DocType names

The first-class DocTypes should use platform-style names.

## Core
- `Press Tenant`
- `Tenant Environment`
- `Tenant Policy`
- `Tenant Transition Log`

## Early follow-up
- `Tenant Subscription`
- `Tenant Usage Snapshot`
- `Tenant Cost Snapshot`
- `Tenant Health Check`
- `Tenant Incident`
- `Tenant Environment Domain`

Avoid renaming these casually once implementation begins.

---

# 4. Canonical field naming rules

## 4.1 General style
Use:
- lowercase snake_case fieldnames
- clear nouns
- no unnecessary abbreviations

Good:
- `tenant_name`
- `site_status`
- `database_mode`
- `primary_domain`
- `estimated_monthly_cost`

Bad:
- `tnt_nm`
- `dbmode`
- `dom1`
- `est_cost`
- `envstat`

## 4.2 Link fields should be noun-based
Examples:
- `tenant`
- `policy`
- `environment`
- `subscription`
- `billing_owner`

Not:
- `tenant_ref`
- `linked_policy_id`
- `env_link`

## 4.3 Date/time fields should describe meaning
Examples:
- `contract_start_date`
- `contract_end_date`
- `last_transition_on`
- `snapshot_on`
- `db_last_backup`
- `last_health_check`

Do not use ambiguous names like:
- `date1`
- `updated_time`
- `backup_time`

## 4.4 Boolean fields should read like flags
Examples:
- `vip_flag`
- `dns_ready`
- `tls_ready`
- `db_ha_enabled`
- `requires_data_residency`

Avoid vague booleans like:
- `enabled`
- `special`
- `critical`

unless the noun is obvious from context.

## 4.5 Status/select fields must be explicit about domain
Examples:
- `tenant_status`
- `subscription_status`
- `site_status`
- `capacity_state`

Do not reuse one generic `status` field across unrelated concepts unless the DocType is extremely scoped.

---

# 5. Field naming by concept

## 5.1 Tenant identity
Use:
- `tenant_name`
- `tenant_slug`
- `organization_type`
- `country`
- `timezone`

## 5.2 Commercial
Use:
- `subscription_tier`
- `subscription_status`
- `billing_cycle`
- `contract_start_date`
- `contract_end_date`

## 5.3 Environment identity
Use:
- `environment_name`
- `environment_type`
- `site_name`
- `site_status`

## 5.4 Hosting / infra
Use:
- `hosting_tier`
- `placement_strategy`
- `database_mode`
- `deployment_mode`
- `region`
- `deployment_mode_notes`

## 5.5 Routing
Use:
- `primary_domain`
- `routing_mode`
- `host_header_value`
- `dns_ready`
- `tls_ready`

## 5.6 DB placement
Use:
- `db_provider`
- `db_instance_name`
- `db_name`
- `db_user`
- `db_ha_enabled`

Detailed connection and cluster-specific fields should remain optional until they materially improve operator workflow.

## 5.7 Health / metrics
Use:
- `health_score`
- `last_health_check`
- `avg_response_ms`
- `error_rate_percent`
- `queue_backlog_count`
- `slow_query_count`
- `capacity_state`

## 5.8 Usage / cost
Use:
- `estimated_monthly_cost`
- `storage_used_gb`
- `file_count`
- `active_users_30d`
- `peak_concurrency_estimate`
- `total_cost_estimate`

---

# 6. Canonical environment state names

These values are locked for now.

Use exactly:

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

Do not create variants like:
- Ready
- Prod
- In Trial
- Dead
- Failed Build
- Active Prod

State drift will create real operational confusion.

---

# 7. Canonical tier and mode values

## 7.1 Hosting tier
Use exactly:
- Sandbox
- Standard
- Premium
- VIP

## 7.2 Database mode
Use exactly:
- Shared DB Fleet
- Dedicated DB Instance

## 7.3 Deployment mode
Use exactly:
- Shared Runtime
- Reserved Runtime
- Dedicated Runtime

## 7.4 Routing mode
Use exactly:
- Internal Only
- Public
- Pending

## 7.5 Capacity state
Use exactly:
- Healthy
- Warning
- Saturated
- Critical

Avoid synonym drift.

---

# 8. Action naming conventions

All major server actions should use explicit, verb-first names.

Good:
- Create Sandbox
- Reset Sandbox
- Expire Sandbox
- Reactivate Sandbox
- Qualify for Production
- Provision Production
- Mark Live
- Suspend Environment
- Restore Environment
- Archive Environment
- Run Health Check
- Refresh Usage Snapshot
- Refresh Cost Snapshot
- Sync Routing Intent
- Rotate DB Credentials

Bad:
- Update Status
- Process Tenant
- Sync All
- Handle Provisioning
- Enable Live

Use names that tell operators exactly what will happen.

---

# 9. Internal service naming conventions

Service modules should be grouped by control-plane concern.

Recommended patterns:
- `tenant_service.py`
- `environment_lifecycle_service.py`
- `environment_health_service.py`
- `environment_usage_service.py`
- `environment_cost_service.py`
- `routing_service.py`
- `transition_log_service.py`

Rules:
- lifecycle orchestration belongs in lifecycle service
- metrics collection belongs in metrics-oriented services
- logging should be reusable
- avoid giant `utils.py` dumping grounds

---

# 10. Child table naming conventions

Child DocTypes should be named clearly in relation to their parent.

Good:
- `Press Tenant Contact`
- `Press Tenant Domain Intent`
- `Tenant Environment Domain`
- `Tenant Environment Check`
- `Tenant Environment Component`

Bad:
- `Tenant Item`
- `Env Child`
- `Config Row`
- `Domain Row`

Child tables should still read like meaningful records.

---

# 11. Document naming conventions

## 11.1 Human-facing labels
Use title case:
- Press Tenant
- Tenant Environment
- Tenant Policy

## 11.2 Field labels
Use clear business language:
- Tenant Name
- Environment Type
- Site Status
- Database Mode
- Estimated Monthly Cost

Avoid overtechnical labels unless needed for operators.

## 11.3 Internal fieldnames
Always use snake_case and keep them stable.

---

# 12. Naming rules for generated identifiers

## 12.1 Document names
Use naming series for primary docs.

Recommended patterns:
- `TEN-.YYYY.-`
- `ENV-.YYYY.-`
- `TPL-.YYYY.-`
- `TTL-.YYYY.-`

This keeps docnames stable and avoids business-meaning overload.

## 12.2 Slugs
Use separate slug fields where needed:
- `tenant_slug`

Slugs are not docnames.

## 12.3 Site names
Use explicit `site_name` field for real operational site identity.
Do not rely on docname to double as site identity.

---

# 13. Documentation naming conventions

Architecture docs should use:
- numbered order
- clear topic names
- stable filenames

Examples:
- `00_control_plane_model.md`
- `01_doctype_proposal.md`
- `02_state_machine.md`

Do not create random filenames like:
- `notes2.md`
- `press_thoughts_final_v3.md`
- `infra-ideas.md`

This project needs durable documentation, not scratchpad chaos.

---

# 14. What to avoid

Avoid these naming failures:

### 14.1 Using customer/school/tenant interchangeably
Pick `tenant` as the control-plane term.

### 14.2 Using environment/site interchangeably
A site is part of an environment, not the same concept.

### 14.3 Reusing `status` everywhere
Use:
- `tenant_status`
- `subscription_status`
- `site_status`
- `capacity_state`

### 14.4 Renaming core concepts for style
Do not rename `Tenant Environment` to `Deployment` just because it sounds more technical.

### 14.5 Traefik-specific leakage too early
Use routing/domain vocabulary, not proxy-internal jargon everywhere.

---

# 15. Final design position

Ifitwala_Press naming must stay:

- explicit
- stable
- domain-driven
- operator-friendly
- scalable
- consistent across docs, schema, services, and UI

One concept should have one name.
That is the naming rule that protects the whole project.
