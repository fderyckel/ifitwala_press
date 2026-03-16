# 05_data_and_metrics_scope.md

## Purpose

This document defines the intended data and metrics scope for **Ifitwala_Press**.

Ifitwala_Press is not only a lifecycle and provisioning control plane.
It is also meant to help us operate the business side of hosted Ifitwala_Ed responsibly.

That means the platform must eventually help us understand, per tenant:

- usage
- cost
- subscription state
- operational health
- capacity risk
- growth signals
- tier mismatch

The purpose of this document is to prevent metric sprawl and vague observability.
It defines what categories of data matter, what they are for, and what should not be tracked blindly.

This is a design-lock document for metrics intent, not a final implementation spec.

---

## 1. Design principles

### 1.1 Track only what changes decisions
Do not collect metrics just because they are available.

A metric is worth tracking only if it helps us:
- operate environments
- diagnose issues
- price customers
- identify upgrade/downgrade need
- manage risk
- improve profitability
- support customers better

### 1.2 Separate raw telemetry from control-plane summaries
Ifitwala_Press is not a full observability backend.

Its job is to store and show:
- snapshots
- summaries
- decision-grade metrics
- operator-facing rollups

Not every raw event.

### 1.3 Keep tenant and environment context attached
A metric with no tenant or environment context is operationally weak.

Where possible, tracked data should be attributable to:
- tenant
- environment
- time period
- source or refresh time

### 1.4 Prefer trends over isolated numbers
A single number is often misleading.

Useful metrics should eventually support:
- current value
- recent change
- directional interpretation

### 1.5 Separate commercial truth from technical truth
Subscription state is not usage.
Usage is not cost.
Cost is not health.
Health is not lifecycle.

Keep those categories distinct.

---

# 2. Data categories

The intended data scope is divided into 4 first-class categories:

1. Usage
2. Cost
3. Subscription / Commercial
4. Operational Health / Capacity

These categories should be modeled separately, even if summarized together in UI.

---

# 3. Usage scope

## Purpose
Usage data helps answer:

- Which tenants are actually active?
- Which tenants are growing?
- Which tenants are under- or over-tiered?
- Which tenants are consuming disproportionate resources?
- Which sandboxes are unused and should expire?
- Which production tenants are approaching scale limits?

## 3.1 Core usage metrics

These are the first metrics worth tracking.

### User activity
- active_users_7d
- active_users_30d
- staff_users_30d
- student_users_30d
- guardian_users_30d

Why:
Helps distinguish genuine adoption from dormant environments.

### Request volume
- request_count_daily
- request_count_30d
- average_requests_per_day

Why:
Useful for broad workload estimation and anomaly spotting.

### Storage usage
- storage_used_gb
- file_count
- average_file_growth_rate

Why:
Storage cost and growth matter directly to hosting and billing decisions.

### Concurrency estimates
- avg_concurrency_estimate
- peak_concurrency_estimate

Why:
This is directly relevant to your stated architecture concern around peak school-time load.

### Queue / background activity
- queue_jobs_processed_24h
- queue_jobs_failed_24h
- queue_backlog_snapshot

Why:
High queue activity or backlog often signals growth or pain.

## 3.2 Nice-to-have usage metrics later

These may matter later, but should not block v1.

- login_count_30d
- avg_session_count
- realtime/socket activity estimate
- heavy report generation count
- API call count by category
- attendance / LMS / portal module usage breakdown

These are useful only if they help pricing, support, or capacity decisions.

## 3.3 Usage metrics we should avoid early

Avoid collecting these into Ifitwala_Press too early:

- every raw HTTP request log
- detailed user behavior analytics
- full page/event analytics
- per-document event streams
- intrusive classroom-level monitoring

Why:
This would bloat the control plane and distract from decision-grade operations.

---

# 4. Cost scope

## Purpose
Cost data helps answer:

- What does each tenant likely cost us?
- Which tenants are mismatched to their plan?
- Which sandboxes are quietly wasting money?
- Which tenants justify dedicated DB or premium pricing?
- Where are the biggest cost drivers in the fleet?

## 4.1 Core cost metrics

### Database cost estimate
- db_cost_estimate_monthly

Why:
DB placement is one of the most important structural cost levers.

### Storage cost estimate
- storage_cost_estimate_monthly

Why:
Files, backups, and object storage can grow silently.

### Compute/runtime cost estimate
- compute_cost_estimate_monthly

Why:
Even shared runtime needs a tenant-attributed estimate for business visibility.

### Backup cost estimate
- backup_cost_estimate_monthly

Why:
Important especially for premium tiers and larger tenants.

### Total estimated cost
- total_cost_estimate_monthly

Why:
This is the headline number operators need.

## 4.2 Optional cost dimensions later

These may become useful later:

- network/egress estimate
- premium isolation surcharge estimate
- cache/redis allocation estimate
- support burden estimate
- migration/project overhead estimate

Useful, but not phase 1 material.

## 4.3 Cost modeling principle
Early cost values can be approximate.

That is acceptable.

Bad:
- fake precision
- unexplained totals
- inconsistent cost attribution logic

Good:
- clear estimate categories
- explicit snapshot date
- transparent approximation logic
- trend over time

---

# 5. Subscription / commercial scope

## Purpose
Subscription data helps answer:

- Who is trial vs paid?
- Which contracts are near renewal?
- Which tenants are overdue?
- Which tenants are underpriced relative to cost/usage?
- Which tenants are candidates for upgrade?

## 5.1 Core subscription fields

### Plan identity
- subscription_tier
- plan_name
- billing_cycle
- currency
- price

### Subscription state
- subscription_status
  - Trial
  - Active
  - Pending Renewal
  - Expired
  - Suspended
  - Cancelled

### Date boundaries
- start_date
- end_date
- renewal_due_on

### Commercial ownership
- billing_owner
- sales_owner
- customer_success_owner

## 5.2 Derived commercial indicators

These are not raw fields, but should become visible signals.

- renewal_risk
- plan_cost_mismatch
- trial_conversion_probability (later, only if grounded)
- VIP_review_needed
- price_review_needed

## 5.3 What not to do early
Do not try to build:
- full invoice engine
- complete accounting system
- complex revenue recognition
- generic subscription platform

Ifitwala_Press should support operational commercial visibility, not become ERPNext Billing v2.

---

# 6. Operational health scope

## Purpose
Health data helps answer:

- Which environments are unhealthy now?
- Which tenants are at risk?
- Which production tenants need intervention?
- Which sandboxes are broken and harming sales?
- Which VIP tenants require immediate review?

## 6.1 Core health metrics

### Health score
- health_score

Why:
A summary indicator is useful if backed by explainable inputs.

### Last successful health check
- last_health_check
- last_health_check_status

Why:
Stale checks are operationally dangerous.

### Performance indicators
- avg_response_ms
- error_rate_percent

Why:
These are simple, understandable health signals.

### Capacity indicators
- queue_backlog_count
- slow_query_count
- capacity_state
  - Healthy
  - Warning
  - Saturated
  - Critical

Why:
Capacity is where cost, usage, and user pain often meet.

### Backup safety indicators
- last_backup_at
- backup_freshness_state
- last_restore_tested_on

Why:
Operational trust without backup visibility is fake.

## 6.2 Optional health metrics later
Potential later additions:
- websocket/realtime health
- storage API latency
- DNS/TLS check status detail
- environment cold start / deploy stability
- failed cron/scheduler indicator

Useful later, not mandatory in first pass.

---

# 7. Capacity and tiering signals

This area matters a lot for Ifitwala_Press because your business model depends on knowing when tenants should move tiers.

## 7.1 Signals that a tenant may need upgrade review
Examples:
- repeated capacity warning
- peak concurrency rising fast
- DB cost rising beyond standard expectations
- storage growth outpacing current plan
- VIP-like operational requirements emerging
- support burden or sensitivity level increasing

## 7.2 Signals that a sandbox should be closed
Examples:
- no active users in 30 days
- low/no request volume
- expired trial
- no recent login
- no commercial owner activity
- cost persists with no movement

## 7.3 Signals that a tenant may deserve dedicated DB
Examples:
- consistently high concurrency
- high sensitivity level
- VIP flag
- strict data residency/security requirement
- expensive noisy-neighbor profile
- major school/university size

These should eventually become review signals, not fully automatic decisions.

---

# 8. Snapshot philosophy

The recommended model is snapshot-based, not stream-based.

## Why snapshots
Snapshots are:
- simpler
- cheaper
- easier to reason about
- more aligned with operator decisions
- easier to audit historically

## Recommended snapshot cadence
This is a direction, not yet a lock.

### Usage snapshots
- daily for active production
- less frequent for sandbox if needed

### Cost snapshots
- daily or weekly depending on calculation complexity

### Health refresh
- more frequent than usage/cost
- can update summary fields regularly
- detailed checks can be stored selectively

### Subscription checks
- event-driven plus scheduled review

---

# 9. Metric ownership boundaries

This is important.

## Ifitwala_Press should own
- tenant-linked summaries
- decision-grade snapshots
- operator-facing rollups
- tiering and review signals
- platform-level status views

## Ifitwala_Press should not own
- full raw observability pipelines
- every infrastructure event
- every application event
- end-user analytics tooling
- detailed product analytics beyond control-plane need

If raw telemetry exists elsewhere, Ifitwala_Press should consume summarized outputs, not become the telemetry dump.

---

# 10. Recommended first snapshot DocTypes

These are the early first-class records to support this scope.

## `Tenant Usage Snapshot`
Purpose:
- store periodic usage summaries

Recommended key fields:
- tenant
- environment
- snapshot_on
- active_users_30d
- request_count_30d
- storage_used_gb
- file_count
- avg_concurrency_estimate
- peak_concurrency_estimate
- queue_jobs_processed_24h
- queue_jobs_failed_24h

## `Tenant Cost Snapshot`
Purpose:
- store periodic cost estimates

Recommended key fields:
- tenant
- environment
- snapshot_on
- db_cost_estimate
- storage_cost_estimate
- compute_cost_estimate
- backup_cost_estimate
- total_cost_estimate
- currency

## `Tenant Health Check`
Purpose:
- store structured health results

Recommended key fields:
- tenant
- environment
- check_type
- checked_on
- status
- response_time_ms
- message

## `Tenant Subscription`
Purpose:
- store plan and status

Recommended key fields:
- tenant
- plan_name
- subscription_tier
- status
- start_date
- end_date
- billing_cycle
- price
- currency

---

# 11. Recommended dashboard metrics

These are the first metrics worth surfacing on dashboards.

## Platform overview
- total tenants
- total live environments
- total sandbox environments
- tenants by subscription tier
- environments by lifecycle state

## Attention metrics
- provisioning failures
- unhealthy live environments
- critical capacity warnings
- stale backups
- renewals due soon
- expiring sandboxes

## Cost metrics
- top 5 highest estimated monthly cost tenants
- total estimated monthly fleet cost
- largest month-over-month cost increases

## Usage metrics
- highest growth tenants
- highest storage growth
- highest concurrency tenants
- dormant sandboxes

These are operationally meaningful.
Do not clutter dashboards with vanity metrics.

---

# 12. Metric interpretation rules

Metrics should not be shown without context.

Examples:

Bad:
- “Peak concurrency: 42”

Better:
- “Peak concurrency estimate: 42, up 40% vs prior snapshot, standard tier”

Bad:
- “Total cost: 190”

Better:
- “Estimated monthly cost: 190 EUR, driven mainly by DB and storage growth”

The control plane should help operators interpret, not merely display.

---

# 13. What we are not done with yet

This document defines scope and intent.
It does not yet define:

- exact formulas for cost allocation
- exact formulas for health score
- exact source of concurrency estimates
- exact retention policy for snapshots
- exact threshold logic for alerts/upgrades

Those should be defined later once the control-plane model and first data collection paths exist.

Do not fake certainty too early.

---

# 14. Recommended implementation order

## Phase 1
Track:
- subscription basics
- usage snapshot basics
- cost snapshot basics
- simple health summary fields on environment

## Phase 1.5
Add:
- structured health check records
- dashboard rollups
- top cost / top usage / renewal views

## Phase 2
Refine:
- trend interpretation
- tier mismatch signals
- alerting thresholds
- more accurate cost attribution
- better capacity review signals

---

# 15. Final design position

Ifitwala_Press should track only the data that helps us operate hosted tenants intelligently.

The core data categories are:

- usage
- cost
- subscription
- health/capacity

These must stay distinct, attributable, and decision-oriented.

That is the current design lock for data and metrics scope.
