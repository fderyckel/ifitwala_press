# 01_doctype_proposal.md

## Purpose

This document translates the current Ifitwala_Press control-plane model into a first Frappe DocType proposal.

The goal is not to overbuild.
The goal is to define the minimum set of strong, durable records needed to operate Ifitwala_Ed tenant environments safely and clearly, including approved platform apps and tenant-specific customization apps.

This proposal focuses on:

- core control-plane records
- clear separation of concerns
- lifecycle governance
- policy-driven hosting
- cost / usage / subscription readiness
- operator-first usability

This is a design proposal for the first real Frappe data model.

---

## Design principles

### 1. Separate tenant identity from environment reality
A customer institution is not the same thing as a deployed site.

That distinction must exist in the schema.

### 2. Separate policy from instance
Quotas, backup rules, and hosting defaults should not be hardcoded into every environment row.

They should be defined in policy and applied intentionally.

### 3. Make lifecycle auditable
Critical state changes must leave a durable record.

### 4. Design for internal operations
This is an internal control plane.
The schema must optimize for clarity, actionability, and safe admin operations.

### 5. Avoid false completeness
Do not try to model the entire cloud on day one.
Model only what the control plane must truly own.

---

# Phase 1 Core DocTypes

The first implementation should build these 5 DocTypes:

1. `Press Tenant`
2. `Tenant Policy`
3. `Tenant Environment`
4. `Tenant Transition Log`
5. `Runtime Pool`

That is the minimum viable control-plane backbone.

---

# 1. `Press Tenant`

## Role

`Press Tenant` is the master customer record.

It represents the institution we manage:
- school
- international school
- small independent university
- trial/prospect institution

It is the customer/business identity layer, not the deployment layer.

## Why it exists

Without `Press Tenant`, the platform will blur:
- customer identity
- commercial state
- hosting intent
- environment state

That would be sloppy and hard to operate.

## Suggested autoname

Use a naming series or slug-based convention.

Recommended:
- naming series for the document name, for example: `TEN-.YYYY.-`
- separate unique field for `tenant_slug`

Do not use the human tenant name as the document name.

## Suggested key fields

### Identity section
- `tenant_name` — Data — reqd
- `tenant_slug` — Data — reqd — unique
- `organization_type` — Select
  - School
  - International School
  - University
  - Demo / Prospect
  - Other
- `country` — Link Country
- `timezone` — Data
- `primary_contact_name` — Data
- `primary_contact_email` — Data
- `primary_contact_phone` — Data

### Commercial section
- `tenant_status` — Select
  - Lead
  - Trial
  - Qualified
  - Customer
  - Suspended
  - Archived
- `subscription_tier` — Select
  - Sandbox
  - Standard
  - Premium
  - VIP
- `subscription_status` — Select
  - Trial
  - Active
  - Pending Renewal
  - Expired
  - Suspended
  - Cancelled
- `sales_owner` — Link User
- `customer_success_owner` — Link User
- `billing_owner` — Link User
- `contract_start_date` — Date
- `contract_end_date` — Date

### Size / profile section
- `estimated_students` — Int
- `estimated_staff` — Int
- `estimated_guardians` — Int
- `estimated_peak_concurrency` — Int

### Risk / sensitivity section
- `data_sensitivity_level` — Select
  - Low
  - Standard
  - High
  - Critical
- `vip_flag` — Check
- `requires_data_residency` — Check
- `security_notes` — Small Text

### Hosting intent section
- `default_hosting_tier` — Select
  - Shared
  - Dedicated DB
  - VIP Reserved
- `default_policy` — Link `Tenant Policy`
- `default_conversion_strategy` — Select
  - Fresh Production Site
  - Copy Config Only
  - Copy Selected Data
  - In-place Upgrade

### Internal tracking section
- `active_environment` — Link `Tenant Environment`
- `last_reviewed_on` — Date
- `internal_notes` — Small Text

## Child tables

### A. `Press Tenant Contact`
Purpose:
- allow multiple named stakeholders without flattening everything into one row

Suggested fields:
- `contact_name` — Data
- `role_label` — Data
- `email` — Data
- `phone` — Data
- `is_primary` — Check

### B. `Press Tenant Domain Intent`
Optional in phase 1, but useful if you already know a customer’s domain expectations before production.

Suggested fields:
- `domain` — Data
- `domain_type` — Select
  - Primary
  - Alias
  - Planned
- `notes` — Data

## Validations

- `tenant_slug` must be unique and normalized
- `contract_end_date` cannot be before `contract_start_date`
- if `vip_flag = 1`, then `subscription_tier` should not be Sandbox
- if `subscription_tier = VIP`, `default_hosting_tier` should not be Shared
- if `tenant_status = Customer`, there should normally be at least one environment

## Key actions

- Create Sandbox Environment
- Mark Qualified
- Open Active Environment
- Review Commercial Status

## Notes

Keep `Press Tenant` commercially and operationally meaningful.
Do not pollute it with infra detail that belongs on `Tenant Environment`.

---

# 2. `Tenant Policy`

## Role

`Tenant Policy` defines reusable hosting and lifecycle rules.

It exists so that:
- sandbox rules are centralized
- production defaults are consistent
- quota and retention rules are explicit
- hosting tier logic does not scatter across code

## Why it exists

Without `Tenant Policy`, infrastructure behavior will drift into:
- magic defaults
- per-environment manual edits
- hidden code rules
- inconsistent lifecycle handling

## Suggested autoname

Use the policy name as the document name if kept clean and unique.

Examples:
- Sandbox Default
- Standard Production
- Premium Dedicated DB
- VIP Reserved

## Suggested key fields

### Identity section
- `policy_name` — Data — reqd — unique
- `is_active` — Check
- `policy_type` — Select
  - Sandbox
  - Standard
  - Premium
  - VIP

### Hosting defaults
- `default_database_mode` — Select
  - Shared DB Fleet
  - Dedicated DB Instance
- `default_deployment_mode` — Select
  - Shared Runtime
  - Reserved Runtime
  - Dedicated Runtime
- `default_region` — Data

### Resource controls
- `worker_quota` — Int
- `web_quota` — Int
- `storage_quota_gb` — Float
- `max_background_jobs` — Int
- `max_file_size_mb` — Int

### Lifecycle rules
- `sandbox_expiry_days` — Int
- `grace_period_days` — Int
- `allow_in_place_upgrade` — Check
- `allow_copy_demo_data` — Check
- `requires_fresh_production_site` — Check

### Backup / retention
- `backup_frequency` — Select
  - None
  - Daily
  - Twice Daily
  - Hourly Snapshot
- `backup_retention_days` — Int
- `requires_restore_test` — Check
- `restore_test_frequency_days` — Int

### Monitoring / support
- `monitoring_level` — Select
  - Basic
  - Standard
  - Advanced
- `alerting_level` — Select
  - None
  - Business Hours
  - 24x7
- `sla_profile` — Select
  - None
  - Standard
  - Premium
  - VIP

## Validations

- if `policy_type = Sandbox`, backup frequency can be None or Daily, but should not imply premium guarantees
- if `default_database_mode = Dedicated DB Instance`, policy type should not be Sandbox unless explicitly justified
- if `requires_fresh_production_site = 1`, then `allow_in_place_upgrade` should usually be 0
- numeric quotas must be non-negative

## Key actions

- Apply Policy to Environment
- Review Policy Usage
- Compare Policy to Tenant Tier

## Notes

Do not overload policy with provider-specific JSON blobs in phase 1.
Keep it human-readable and operational.

---

# 3. `Tenant Environment`

## Role

`Tenant Environment` is the operational heart of the platform.

It represents one real deployable environment for a tenant.

Examples:
- sandbox
- production
- later staging

## Why it exists

This is where lifecycle, placement, health, and routing intent live.

It must stay separate from:
- customer identity (`Press Tenant`)
- default rules (`Tenant Policy`)
- lifecycle audit (`Tenant Transition Log`)

## Suggested autoname

Use naming series.

Recommended:
- `ENV-.YYYY.-`

Do not use domain or site name as the actual document name.

## Suggested key fields

### Phase 1 required vs phase 2 detail
Phase 1 should keep `Tenant Environment` focused on operational decisions and lifecycle visibility.

Required in phase 1:
- tenant/environment identity
- lifecycle state and reason
- policy and hosting tier
- placement intent
- app bundle intent
- logical DB mode and deployment mode
- primary routing intent
- expiry, health summary, cost summary, and provisioning summary

Defer to phase 2 unless clearly needed in the UI or action contracts:
- provider-specific router metadata
- exact runtime image metadata
- exact Redis endpoints
- exact bucket metadata
- exact DB host and port details
- cluster and namespace specifics that do not affect operator decisions yet

### Identity section
- `tenant` — Link `Press Tenant` — reqd
- `environment_name` — Data
- `environment_type` — Select
  - Sandbox
  - Production
  - Staging
- `site_name` — Data — reqd — unique

### Lifecycle section
- `site_status` — Select
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
- `status_reason` — Small Text
- `last_transition_on` — Datetime
- `last_transition_by` — Link User

### Policy / tier section
- `policy` — Link `Tenant Policy`
- `hosting_tier` — Select
  - Sandbox
  - Standard
  - Premium
  - VIP
- `placement_strategy` — Select
  - Founder Shared Runtime
  - Shared Production Fleet
  - Dedicated DB
  - Dedicated Runtime + DB

### Domain / routing section
- `primary_domain` — Data
- `routing_mode` — Select
  - Internal Only
  - Public
  - Pending
- `dns_ready` — Check
- `tls_ready` — Check
- `host_header_value` — Data

### Deployment placement section
- `region` — Data
- `app_bundle` — Link `App Bundle`
- `app_release` — Link `App Release`
- `site_app_assignment` — Link `Tenant Environment App Assignment`
- `deployment_mode` — Select
  - Shared Runtime
  - Reserved Runtime
  - Dedicated Runtime
- `deployment_mode_notes` — Small Text

### Database section
- `database_mode` — Select
  - Shared DB Fleet
  - Dedicated DB Instance
- `db_provider` — Select
  - Self Managed
  - Google Managed
  - Other Managed
- `db_instance_name` — Data
- `db_name` — Data
- `db_user` — Data
- `db_ha_enabled` — Check
- `db_last_backup` — Datetime
- `db_restore_tested_on` — Date

### Cache / queue / realtime section
- `socketio_enabled` — Check
- `worker_profile` — Data or Link later if needed

### Storage section
- `file_storage_provider` — Select
  - GCS
  - Local Temporary
- `file_storage_class` — Select
  - Frequent Access
  - Infrequent Access
- `backup_storage_provider` — Select
  - GCS
  - Local Temporary
- `backup_storage_class` — Select
  - Frequent Access
  - Infrequent Access
- `storage_quota_gb` — Float
- `expires_on` — Date

### Health / capacity section
- `health_score` — Percent or Float
- `last_health_check` — Datetime
- `avg_response_ms` — Int
- `error_rate_percent` — Percent
- `queue_backlog_count` — Int
- `slow_query_count` — Int
- `capacity_state` — Select
  - Healthy
  - Warning
  - Saturated
  - Critical

### Provisioning section
- `provisioning_job_id` — Data
- `last_provisioning_step` — Data
- `provisioning_message` — Small Text

### Commercial support section
- `estimated_monthly_cost` — Currency
- `billing_status_snapshot` — Select
  - Trial
  - Billable
  - Suspended
  - Archived
- `usage_snapshot_on` — Datetime

## Child tables

### A. `Tenant Environment Domain`
This may be separate later, but child table is enough initially.

Suggested fields:
- `domain` — Data
- `domain_type` — Select
  - Primary
  - Alias
  - Internal
- `dns_status` — Select
  - Pending
  - Ready
  - Failed
- `tls_status` — Select
  - Pending
  - Ready
  - Failed
- `traefik_host_rule` — Data

### B. `Tenant Environment Check`
Purpose:
- keep recent operational checks attached to the environment

Suggested fields:
- `check_type` — Select
  - HTTP
  - DB
  - Redis
  - Worker
  - SocketIO
  - Backup
  - Storage
- `status` — Select
  - Healthy
  - Warning
  - Failed
- `checked_on` — Datetime
- `response_time_ms` — Int
- `message` — Small Text

### C. `Tenant Environment Component`
Optional, but useful if you want to display service components later.

Suggested fields:
- `component_type` — Select
  - Web
  - Worker
  - Scheduler
  - SocketIO
  - DB
  - Redis
  - Storage
- `component_name` — Data
- `status` — Select
  - Healthy
  - Warning
  - Failed
- `notes` — Data

## Validations

- `site_name` must be unique and normalized
- if `environment_type = Sandbox`, `hosting_tier` should normally be Sandbox
- if `hosting_tier = VIP`, `database_mode` should not be Shared DB Fleet
- if `database_mode = Dedicated DB Instance`, `db_instance_name` should be required
- if `routing_mode = Public`, `primary_domain` should normally be required
- if `site_status = Live`, policy, DB fields, and `app_bundle` should not be blank
- if `deployment_mode = Shared Runtime`, the assigned `app_bundle` should be approved for shared-pool use
- if `expires_on` is set for non-sandbox production, require justification or policy support

## Key actions

- Create Sandbox
- Reset Sandbox
- Expire Sandbox
- Qualify for Production
- Provision Production
- Suspend Environment
- Restore Environment
- Archive Environment
- Run Health Check
- Sync Routing Intent
- Refresh Cost Snapshot
- Refresh Usage Snapshot

## Notes

`Tenant Environment` is the operational pane of glass.
Do not turn it into a dumping ground for every possible infra detail.
Only store what the control plane needs to reason and act.
Detailed provider payloads can move into follow-up records or service-layer integrations once the operator workflow proves they are necessary.

---

# 4. `Tenant Transition Log`

## Role

`Tenant Transition Log` is the append-only audit record for lifecycle and critical platform transitions.

## Why it exists

Ifitwala_Press is a control plane.
Control planes need durable transition history.

Without this record, operators will lose:
- who changed what
- why a state changed
- whether a job succeeded
- what failed during provisioning or suspension

## Suggested autoname

Use naming series.

Recommended:
- `TTL-.YYYY.-`

## Suggested key fields

- `tenant` — Link `Press Tenant`
- `environment` — Link `Tenant Environment`
- `from_state` — Data
- `to_state` — Data
- `trigger_type` — Select
  - Manual
  - Automated
  - Scheduled
  - System Recovery
- `triggered_by` — Link User
- `job_id` — Data
- `success` — Check
- `message` — Small Text
- `details_json` — Code or Long Text
- `transition_on` — Datetime

## Validations

- `from_state` and `to_state` should not be identical unless the log type explicitly allows a retry marker
- if `trigger_type = Manual`, `triggered_by` should be present
- if `success = 0`, `message` should be required

## Notes

This log should be append-only.
Do not allow casual editing after insert.

---

# Phase 1.5 / Early Follow-Up DocTypes

These are not required for the first commit, but they are close enough to the mission that they should be planned now.

---

# 5. `App Bundle`

## Role

`App Bundle` defines one approved compatible set of app code that may be deployed together in one runtime pool.

## Why it matters

Ifitwala_Press must support more than `ifitwala_ed` alone.
It must support:
- platform extensions such as `ifitwala_drive`
- future approved `ifitwala_*` apps
- school-specific customization apps

But that flexibility must stay governed.
`App Bundle` is the record that keeps app composition explicit instead of hidden in image tags or operator memory.

## Suggested fields

### Identity section
- `bundle_name` — Data — reqd — unique
- `bundle_slug` — Data — reqd — unique
- `is_active` — Check
- `bundle_type` — Select
  - Platform Default
  - Shared Compatible
  - Tenant Custom
  - VIP Custom

### Runtime section
- `frappe_branch` — Data
- `runtime_image` — Data
- `runtime_image_tag` — Data
- `default_deployment_mode` — Select
  - Shared Runtime
  - Reserved Runtime
  - Dedicated Runtime
- `shared_runtime_compatible` — Check

### Governance section
- `supports_sandbox` — Check
- `supports_standard_production` — Check
- `supports_premium` — Check
- `supports_vip` — Check
- `notes` — Small Text

## Child table

### A. `App Bundle App`
Suggested fields:
- `app_name` — Data
- `app_source_type` — Select
  - Core
  - Ifitwala Platform
  - Tenant Custom
- `source_url` — Data
- `branch_or_track` — Data
- `pin_ref` — Data
- `install_order` — Int
- `install_on_site_by_default` — Check
- `required_for_bundle` — Check

## Notes

This record owns approved app composition.
It should not be replaced by loose text notes on `Tenant Environment`.

---

# 6. `App Release`

## Role

`App Release` represents one buildable and deployable release of an `App Bundle`.

## Why it matters

The environment should point to a governed release, not only to a conceptual bundle.
This keeps image, release, and rollout intent auditable.

## Suggested fields

- `app_bundle` — Link `App Bundle` — reqd
- `release_label` — Data — reqd — unique
- `status` — Select
  - Draft
  - Build Pending
  - Ready
  - Deprecated
  - Blocked
- `runtime_image` — Data
- `runtime_image_tag` — Data
- `runtime_image_digest` — Data
- `built_on` — Datetime
- `built_by` — Link User
- `release_notes` — Small Text

## Notes

This record is where exact image metadata belongs.
That keeps `Tenant Environment` operator-focused while preserving release traceability.

---

# 7. `Tenant Environment App Assignment`

## Role

`Tenant Environment App Assignment` records how one environment consumes an approved app bundle and which apps are actually intended to be installed on that site.

## Why it matters

The runtime image and the site install set are related but not identical.
This record makes that distinction explicit and auditable.

## Suggested fields

- `environment` — Link `Tenant Environment` — reqd — unique
- `app_bundle` — Link `App Bundle` — reqd
- `app_release` — Link `App Release`
- `assignment_mode` — Select
  - Bundle Default
  - Bundle Subset
  - Bundle Plus Tenant Extensions
- `approved_by` — Link User
- `approved_on` — Datetime
- `notes` — Small Text

## Child table

### A. `Assigned Site App`
Suggested fields:
- `app_name` — Data
- `source_type` — Select
  - Core
  - Ifitwala Platform
  - Tenant Custom
- `install_on_site` — Check
- `required_for_environment` — Check
- `install_status` — Select
  - Pending
  - Installed
  - Failed
  - Skipped

## Notes

This gives the control plane a first-class record of site app intent.
Do not bury this only in image tags, shell history, or ticket comments.

---

# 8. `Tenant Subscription`

## Role

Tracks the commercial subscription layer per tenant.

## Why it matters

Ifitwala_Press is internal-only and must help us monitor:
- plan state
- renewal risk
- upgrade opportunities
- billing/suspension risk

## Suggested fields

- `tenant` — Link `Press Tenant`
- `plan_name` — Data
- `subscription_tier` — Select
  - Sandbox
  - Standard
  - Premium
  - VIP
- `status` — Select
  - Trial
  - Active
  - Pending Renewal
  - Expired
  - Suspended
  - Cancelled
- `start_date` — Date
- `end_date` — Date
- `billing_cycle` — Select
  - Monthly
  - Quarterly
  - Annual
- `price` — Currency
- `currency` — Link Currency
- `notes` — Small Text

## Notes

This can stay simple first.
Do not prematurely build a full billing engine.

---

# 9. `Tenant Usage Snapshot`

## Role

Stores time-based usage summaries for a tenant or environment.

## Why it matters

Usage is core to:
- capacity planning
- cost estimation
- upgrade conversations
- abuse/anomaly detection

## Suggested fields

- `tenant` — Link `Press Tenant`
- `environment` — Link `Tenant Environment`
- `snapshot_on` — Datetime
- `active_users_30d` — Int
- `storage_used_gb` — Float
- `file_count` — Int
- `request_count` — Int
- `avg_concurrency_estimate` — Float
- `peak_concurrency_estimate` — Float
- `queue_jobs_processed` — Int
- `notes` — Small Text

---

# 10. `Tenant Cost Snapshot`

## Role

Stores periodic cost estimates or cost allocations.

## Why it matters

Cost visibility is a first-class mission of Ifitwala_Press.

## Suggested fields

- `tenant` — Link `Press Tenant`
- `environment` — Link `Tenant Environment`
- `snapshot_on` — Datetime
- `db_cost_estimate` — Currency
- `storage_cost_estimate` — Currency
- `compute_cost_estimate` — Currency
- `backup_cost_estimate` — Currency
- `total_cost_estimate` — Currency
- `currency` — Link Currency
- `notes` — Small Text

---

# 11. `Tenant Health Check`

## Role

Stores structured health check results as first-class records if child tables become insufficient.

## Suggested fields

- `tenant` — Link `Press Tenant`
- `environment` — Link `Tenant Environment`
- `check_type` — Select
  - HTTP
  - DB
  - Redis
  - Worker
  - SocketIO
  - Backup
  - Storage
- `status` — Select
  - Healthy
  - Warning
  - Failed
- `checked_on` — Datetime
- `response_time_ms` — Int
- `message` — Small Text

---

# 12. `Tenant Incident` or `Tenant Alert Log`

## Role

Tracks incidents, warnings, failures, and alerts in a more operator-friendly way than raw checks.

## Suggested fields

- `tenant` — Link `Press Tenant`
- `environment` — Link `Tenant Environment`
- `incident_type` — Select
  - Provisioning Failure
  - Health Degradation
  - Capacity Warning
  - Backup Warning
  - Billing Warning
  - Routing Failure
  - Security Review
- `severity` — Select
  - Info
  - Warning
  - Critical
- `status` — Select
  - Open
  - Acknowledged
  - Resolved
  - Closed
- `opened_on` — Datetime
- `resolved_on` — Datetime
- `summary` — Data
- `details` — Small Text
- `owner` — Link User

---

# Recommended implementation order

## Phase 1
Build now:
1. `Press Tenant`
2. `Tenant Policy`
3. `Tenant Environment`
4. `Tenant Transition Log`

## Phase 1.5
Add soon after:
5. `App Bundle`
6. `App Release`
7. `Tenant Environment App Assignment`
8. `Tenant Subscription`
9. `Tenant Usage Snapshot`
10. `Tenant Cost Snapshot`

## Phase 2
Add when the operational flow is stable:
11. `Tenant Health Check`
12. `Tenant Incident` / `Tenant Alert Log`

---

# Recommended list views

To keep the control plane useful, list views should be intentional.

## `Press Tenant` list should emphasize
- tenant name
- tenant status
- subscription tier
- subscription status
- vip flag
- active environment
- contract end date

## `Tenant Environment` list should emphasize
- tenant
- environment type
- site status
- app bundle
- hosting tier
- database mode
- primary domain
- region
- health score
- capacity state
- estimated monthly cost

## `Tenant Transition Log` list should emphasize
- tenant
- environment
- from state
- to state
- success
- triggered by
- transition on

---

# Recommended dashboard intent

Even before deep charts, the control plane should eventually support operator dashboards for:

- tenants by lifecycle state
- environments by health/capacity state
- sandboxs expiring soon
- production environments with failed backups/checks
- top-cost tenants
- top-growth tenants
- subscriptions up for renewal
- VIP tenants requiring attention

This proposal should guide the schema toward those surfaces.

---

# Final design recommendation

The schema should stay disciplined around 4 ideas:

1. customer identity
2. environment reality
3. policy defaults
4. auditable transitions

Everything else should be added only when it strengthens internal operations.

That is the right first data model for Ifitwala_Press.
