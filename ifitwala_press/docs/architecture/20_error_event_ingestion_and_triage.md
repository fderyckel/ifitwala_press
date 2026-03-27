# 20_error_event_ingestion_and_triage.md

## Purpose

This document proposes the first serious upstream error-ingestion design for **Ifitwala_Press**.

The goal is to give operators one place to see and triage real application and runtime failures across sandbox and production tenant environments, especially:

- founder runtime container failures
- Frappe `Error Log` / scheduler / worker exceptions
- `ifitwala_ed` and `ifitwala_drive` application errors
- repeated errors coming back from demo sandboxes

The target outcome is **Airbrake-like operator visibility** without turning Ifitwala_Press into a generic full-stream observability platform.

This proposal stays aligned with the existing control-plane rules:

- tenant and environment context must stay explicit
- lifecycle state is separate from health and incidents
- important operational problems must be surfaced and auditable
- raw telemetry should not bloat the control plane

---

## Bottom line

Ifitwala_Press should own a **normalized error inbox**, not a giant raw log warehouse.

The recommended design is:

1. ingest structured error events from runtime logs and tenant sites
2. normalize and fingerprint them server-side
3. group them into operator-facing error issues
4. keep raw log evidence outside the main control-plane tables
5. expose unresolved and regressing issues on the Press home page and environment detail pages

---

## 1. Problem to solve

Today we can prove lifecycle and deployment intent, but we do not yet have a reliable upstream path for runtime and app failures.

That creates several operator problems:

- sandbox errors stay buried in per-site Frappe logs
- worker and scheduler failures stay buried in container logs
- repeated app exceptions are hard to group and prioritize
- there is no shared attention queue for demo failures that deserve engineering follow-up
- operators have no durable acknowledgment / resolution flow for recurring issues

For this repository, the problem is not "collect every log line."

The problem is:

- know which tenant environments are failing
- know what is failing repeatedly
- know whether the problem is app, runtime, routing, worker, or provisioning related
- give operators a small, actionable error inbox

---

## 2. Design principles

### 2.1 Control-plane summaries, not a raw log dump

Ifitwala_Press should not become the permanent storage backend for every container log line.

It should store:

- normalized error events
- grouped issue records
- counts, timestamps, severity, ownership, and status
- references to raw evidence

It should not try to store unbounded raw stdout/stderr history.

### 2.2 Every error must carry tenant and environment context

Errors must be attributable to:

- `Press Tenant`
- `Tenant Environment`
- site name
- environment type
- source system
- occurrence time

An error without environment context is weak and hard to act on.

### 2.3 Separate occurrence from triage

One repeated exception should not create hundreds of manually managed operator records.

We need two layers:

- append-only normalized occurrences
- grouped operator-facing issues

### 2.4 Server-authoritative ingestion

Issue grouping, severity mapping, deduplication, and status transitions should happen in Press server logic.

Clients and shippers may submit data.
They should not decide final incident state.

### 2.5 Raw evidence stays referenceable

Operators need enough evidence to debug:

- exception type
- message summary
- stack trace excerpt
- container / worker / scheduler identity
- related request or job metadata

But large raw payloads should live in:

- retained runtime log files
- object storage
- or later a log backend such as Cloud Logging / Loki

Press should keep compact evidence and pointers, not infinite history.

### 2.6 Never fail silently

If ingestion fails, that failure must itself be visible.

Examples:

- shipper cannot reach Press
- Press rejects malformed payloads
- tenant-site sync job fails repeatedly

These are operational issues and should become visible records.

---

## 3. Recommended data model

The first design should add **one new append-only record** and **one grouped operator record**.

### 3.1 `Tenant Error Event`

## Role

Stores one normalized error occurrence received from a tenant site or runtime shipper.

This is the durable per-occurrence record.

## Why it exists

Without this record:

- deduplication becomes opaque
- recurrence tracking becomes weak
- regression detection becomes brittle
- grouped issues lose their factual base

## Suggested key fields

- `tenant` — Link `Press Tenant` — reqd
- `environment` — Link `Tenant Environment` — reqd
- `occurred_on` — Datetime — reqd
- `source_type` — Select
  - Container Runtime
  - Frappe Error Log
  - Scheduler
  - Worker
  - HTTP Request
  - App Hook
  - Provisioning Adapter
- `source_system` — Select
  - Founder Runtime
  - Frappe
  - Ifitwala Ed
  - Ifitwala Drive
  - Edge Proxy
  - Control Plane Adapter
- `severity` — Select
  - Error
  - Critical
- `site_name_snapshot` — Data
- `container_name` — Data
- `process_name` — Data
- `request_id` — Data
- `job_id` — Data
- `exception_type` — Data
- `message_summary` — Data
- `stacktrace_excerpt` — Small Text
- `fingerprint` — Data — reqd — indexed
- `raw_reference` — Data
- `ingested_on` — Datetime
- `ingest_channel` — Select
  - Host Shipper
  - Site Push
  - Control Plane Pull
  - Manual Import

## Notes

- Keep this append-only.
- Do not let operators edit occurrence facts casually.
- `raw_reference` should point to object storage, retained log file path, or later Cloud Logging query metadata.

### 3.2 `Tenant Error Issue`

## Role

Represents the grouped, operator-facing issue that behaves like the Press-side equivalent of an Airbrake error group.

This is the main inbox object operators will triage.

## Why it exists

Operators need to see:

- what is still open
- what is new
- what is recurring
- what was resolved and then regressed

That is different from looking at raw occurrences.

## Suggested key fields

- `tenant` — Link `Press Tenant` — reqd
- `environment` — Link `Tenant Environment` — reqd
- `issue_key` — Data — reqd — unique
- `fingerprint` — Data — reqd
- `source_type` — Select
- `source_system` — Select
- `severity` — Select
  - Warning
  - Error
  - Critical
- `status` — Select
  - Open
  - Acknowledged
  - Resolved
  - Closed
  - Ignored
- `summary` — Data — reqd
- `first_seen_on` — Datetime
- `last_seen_on` — Datetime
- `last_event` — Link `Tenant Error Event`
- `occurrence_count` — Int
- `regression_count` — Int
- `owner` — Link User
- `resolution_notes` — Small Text
- `raw_reference` — Data

## Grouping rule

Group by a stable issue key derived from:

- environment
- source system
- exception type
- normalized stack fingerprint

Do not group globally across different environments.

The same bug across ten sandboxes should still be visible as ten affected environments, even if later we add a higher-level "fleet-wide fingerprint" report.

### 3.3 Relationship to `Tenant Incident`

This proposal does **not** replace the broader incident/alert model already described in the architecture docs.

Recommended distinction:

- `Tenant Error Event` = one occurrence
- `Tenant Error Issue` = grouped recurring error for operator triage
- `Tenant Incident` = broader operational event that may come from errors, health checks, provisioning failures, or billing/routing concerns

In phase 1, it is acceptable to use `Tenant Error Issue` as the practical operator inbox and add a broader `Tenant Incident` layer later.

---

## 4. Ingestion paths

We need more than one source path because not all failures originate in the same layer.

### 4.1 Founder runtime host shipper

This should be the first ingestion path.

It should run close to the founder runtime host and read from:

- container stdout/stderr
- `./logs` mounted from the Frappe bench
- provisioning adapter failure output

Current repo facts already support this path:

- the founder compose stack mounts `/home/frappe/frappe-bench/logs` into `./logs`
- diagnostics already exist for founder-mode incident work
- founder runtime behavior is already modeled as a controlled adapter surface

## Responsibilities

- parse runtime and bench log files
- extract exceptions and failure markers
- attach site and container context
- batch and POST normalized events to Ifitwala_Press
- record shipper cursor state locally so events are not resent forever

## Why start here

This is the fastest path to cover:

- backend exceptions
- worker failures
- scheduler failures
- provisioning adapter errors

without first modifying every app.

### 4.2 Tenant-site Frappe error sync

Each tenant site should push structured records for:

- `Error Log`
- scheduler job exceptions where available
- selected app-captured exceptions

This can run as a scheduled job on the tenant site or a small sync command executed from the runtime host.

## Recommendation

Prefer a **site push** model over a Press pull model.

Why:

- the tenant site already has direct DB access to its own `Error Log`
- it avoids teaching Press to reach into every tenant database remotely
- it keeps source-specific extraction logic near the source

### 4.3 Explicit app-level capture for `ifitwala_ed` and `ifitwala_drive`

Not every important error lands cleanly in Frappe `Error Log` in an operator-friendly shape.

For application-level failure points, add a small shared helper later so the apps can emit:

- module / feature area
- business action name
- sanitized context
- tenant site metadata
- caught exception details

Use this for:

- integration failures
- background workflow failures
- domain-specific exceptions that deserve better summaries than raw tracebacks

Do not make this the only path.
Uncaught runtime failures still need the shipper and Frappe sync paths.

---

## 5. Normalization and grouping rules

### 5.1 Fingerprint contract

The Press server should compute the fingerprint from normalized fields, not trust client-provided grouping.

Recommended inputs:

- `source_system`
- `source_type`
- `exception_type`
- top stack frames after trimming line-number noise
- normalized message text

### 5.2 Message normalization

Strip or normalize values that cause false issue splits:

- UUIDs
- numeric row ids
- timestamps
- generated file paths
- request-specific tokens

### 5.3 Severity mapping

Use simple rules first:

- uncaught exception with traceback = `Error`
- repeated high-frequency occurrence burst = escalate grouped issue to `Critical`
- provisioning, backup, or routing failures with explicit service impact = `Critical`

Avoid a complicated scoring engine in v1.

### 5.4 Regression behavior

If an issue was `Resolved` or `Closed` and a matching fingerprint appears again:

- reopen the issue
- increment `regression_count`
- update `last_seen_on`

Recurring regressions are one of the main reasons to build this feature.

### 5.5 Rate limiting and storm protection

The ingestion service should guard against log storms.

Minimum protections:

- batch inserts
- per-issue occurrence counters
- collapse duplicate occurrences within a very short window when they are identical
- truncate oversize stack traces

---

## 6. Operator surfaces

This proposal should plug directly into the already-defined attention-surface architecture.

### 6.1 Press home attention queue

Add an error-focused block showing:

- new issues in the last 24h
- critical unresolved issues
- top recurring sandbox issues
- regressed issues

### 6.2 `Tenant Environment` detail

Add an "Errors" panel showing:

- open grouped issues
- last seen time
- occurrence count
- source system
- exception summary
- owner / status

### 6.3 `Press Tenant` detail

Show unresolved issues across all environments for that tenant.

This matters once a tenant has both sandbox and production environments.

### 6.4 Dedicated error list

Add a dedicated list view for `Tenant Error Issue` with filters for:

- Sandbox vs Production
- Open / Acknowledged / Resolved
- Ifitwala Ed / Ifitwala Drive / Frappe / Founder Runtime
- Critical only
- Regressed
- Most frequent

This should become the main "error inbox" for engineering and support.

---

## 7. Server-authoritative actions

The first action layer should stay small.

### Required actions

- `ingest_error_events(events: list[...])`
- `acknowledge_error_issue(issue, owner, note)`
- `resolve_error_issue(issue, note)`
- `ignore_error_issue(issue, note)`
- `reopen_error_issue(issue, note)` for manual override

### Required behavior

- validate tenant/environment references
- compute fingerprint server-side
- create `Tenant Error Event`
- open or update `Tenant Error Issue`
- update counts and timestamps
- preserve auditability on status changes

This should follow the same service-layer philosophy already used for lifecycle actions and snapshots.

---

## 8. Security and data-handling rules

Because this system handles school environments, error ingestion must be conservative about sensitive data.

### Rules

- never ship passwords, tokens, cookies, or full request bodies
- truncate stack traces and request payloads to useful summaries
- sanitize known secret patterns before storage
- prefer references to raw logs over copying large unredacted payloads into Press
- authenticate shippers with environment-scoped credentials

### Authentication recommendation

Each environment should have a Press-ingestion credential stored in runtime config and rotated from the control plane later.

Do not rely on an anonymous inbound endpoint.

---

## 9. Storage and retention posture

### In Press

Keep:

- grouped issues long enough for operator history
- occurrences for a bounded operational window

Suggested starting posture:

- `Tenant Error Event`: retain 30 to 60 days
- `Tenant Error Issue`: retain full history unless archived

### Outside Press

Keep full raw evidence in:

- founder runtime log files
- object storage exports
- or later Cloud Logging / Loki

This preserves debug depth without turning Frappe tables into a log warehouse.

---

## 10. Recommended rollout

### Phase 1

Build now:

1. `Tenant Error Event`
2. `Tenant Error Issue`
3. Press ingestion API and service layer
4. founder-runtime host shipper for container and bench logs
5. basic list view and environment error panel

### Phase 1.5

Add soon after:

1. tenant-site Frappe `Error Log` push sync
2. status actions: acknowledge / resolve / ignore
3. Press home error attention queue
4. regression reopen behavior

### Phase 2

Add when the basic loop works:

1. explicit `ifitwala_ed` / `ifitwala_drive` capture helper
2. raw evidence export to object storage or Cloud Logging
3. fleet-wide fingerprint reporting across many sandboxes
4. optional issue ownership SLA views

---

## 11. Why this is the right shape for Ifitwala_Press

This proposal fits the repo constitution because it:

- keeps tenant and environment context explicit
- gives operators a concrete attention surface
- keeps error events separate from lifecycle state
- avoids turning Press into a generic observability product
- supports manual and semi-automated founder-mode operation first
- creates an auditable upstream path for recurring sandbox failures

It also keeps the first implementation narrow:

- one ingestion API
- one occurrence record
- one grouped issue record
- one founder-runtime shipper
- one operator inbox

That is enough to start catching real failures and working them down.

---

## 12. Recommended implementation decision

Approve the following build target:

**Implement a Press-owned error inbox based on `Tenant Error Event` and `Tenant Error Issue`, fed first by a founder-runtime host shipper and then by tenant-site Frappe error sync.**

This is the shortest path to real upstream error visibility without breaking the current control-plane architecture.
