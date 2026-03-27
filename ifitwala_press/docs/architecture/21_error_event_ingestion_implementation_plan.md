# 21_error_event_ingestion_implementation_plan.md

## Purpose

This document turns the proposed error-ingestion architecture into a concrete implementation plan for **Ifitwala_Press**.

It is intentionally narrow.

It does not redesign the proposal in `20_error_event_ingestion_and_triage.md`.
It translates that proposal into:

- what to build first
- where it should live in this repo
- what to defer
- what must be proven before phase-1 is considered done

---

## Bottom line

Build the first version as a **Press-owned error inbox** with:

1. two new control-plane DocTypes
2. one server-side ingestion service and API
3. one founder-runtime host shipper
4. one operator list and one environment-level error panel

Do not start with downstream app instrumentation, a generic observability stack, or fleet-wide analytics.

---

## 1. Current repo reality

As of this plan:

- the core control-plane backbone already exists in code
- `Press Tenant`, `Tenant Environment`, `Tenant Policy`, and `Tenant Transition Log` are implemented
- lifecycle orchestration already lives in the service layer under `ifitwala_press/ifitwala_press/services/`
- founder-runtime execution already has an adapter and host-oriented ops assets under `ops/founder_runtime/`
- tenant/environment panels already expose whitelisted read APIs in `ifitwala_press/api/views.py`

What does not exist yet:

- any error-ingestion DocType
- any issue-grouping service
- any authenticated ingestion endpoint
- any founder-runtime shipper
- any error inbox surface
- any scheduler hook for retention or sync work

That means this feature is still net-new and should be built as a clean vertical slice rather than folded awkwardly into lifecycle code.

---

## 2. Locked implementation posture

Phase 1 should stay aligned with the control-plane constitution:

- error occurrence and error triage remain separate
- tenant and environment context remain mandatory
- lifecycle state remains separate from health and incidents
- Press stores compact normalized records, not raw log streams
- server-side logic owns fingerprinting, severity mapping, grouping, and reopen behavior
- founder-mode runtime coverage comes first because it captures the most failures with the least downstream app change

The first release target is:

- founder-runtime container and bench log ingestion
- grouped issue tracking per environment
- operator-facing triage for open and regressed issues

The first release should not include:

- full text raw log storage in Frappe
- cross-environment global grouping
- SLA automation
- Cloud Logging or Loki integration
- required downstream changes in `ifitwala_ed` or `ifitwala_drive`

---

## 3. Delivery sequence

Implement in this order:

1. lock the Press-side data model
2. implement normalization, grouping, and authenticated ingestion
3. ship founder-runtime log ingestion
4. expose the operator inbox and environment surfaces
5. add tenant-site push sync after the founder path is working

This keeps the shortest path to actionable visibility while preserving the current control-plane architecture.

---

## 4. Phase 1A - Press data model

### Goal

Create the minimum durable records for error occurrence and operator triage.

### Build

Add these DocTypes:

1. `Tenant Error Event`
2. `Tenant Error Issue`

Recommended paths:

- `/Users/francois.de/Documents/ifitwala_press/ifitwala_press/ifitwala_press/doctype/tenant_error_event/`
- `/Users/francois.de/Documents/ifitwala_press/ifitwala_press/ifitwala_press/doctype/tenant_error_issue/`

Each DocType directory should include:

- `__init__.py`
- the DocType JSON definition
- the Python controller

### Required modeling rules

`Tenant Error Event`:

- append-only in normal operation
- stores one normalized occurrence
- links to `Press Tenant` and `Tenant Environment`
- stores fingerprint, source metadata, summary, compact stack excerpt, and raw reference
- carries occurrence time and ingest time separately

`Tenant Error Issue`:

- one grouped issue per environment and fingerprint
- stores status, severity, counts, owner, summary, last event, first seen, last seen, and regression count
- stays operator-editable only through explicit actions, not casual field edits

### Validation and indexes

Must enforce:

- valid tenant/environment linkage
- environment-specific grouping only
- required fingerprint on both records
- unique `issue_key` on `Tenant Error Issue`
- indexed `fingerprint`, `environment`, `status`, `last_seen_on`

### Done when

Phase 1A is done when:

- the DocTypes exist and install cleanly
- inserts reject malformed tenant/environment references
- issue uniqueness works at the database level
- event records cannot be casually repurposed as mutable inbox items

---

## 5. Phase 1B - Ingestion service and API

### Goal

Make Press the server-authoritative owner of normalization, grouping, and triage state.

### Build

Recommended files:

- `/Users/francois.de/Documents/ifitwala_press/ifitwala_press/ifitwala_press/services/error_ingestion_service.py`
- `/Users/francois.de/Documents/ifitwala_press/ifitwala_press/api/error_ingestion.py`

If the fingerprinting logic grows, split out:

- `/Users/francois.de/Documents/ifitwala_press/ifitwala_press/ifitwala_press/services/error_fingerprint_service.py`

### Required server actions

Implement:

1. `ingest_error_events(events: list[dict])`
2. `acknowledge_error_issue(issue, owner, note)`
3. `resolve_error_issue(issue, note)`
4. `ignore_error_issue(issue, note)`
5. `reopen_error_issue(issue, note)`

### Required behavior

The ingestion service must:

- authenticate the caller with an environment-scoped credential
- validate that the referenced environment belongs to the referenced tenant
- sanitize incoming summaries and stack excerpts
- compute the fingerprint on the Press side
- normalize noisy values out of messages and stack frames
- create one `Tenant Error Event` per accepted occurrence
- upsert one `Tenant Error Issue` per environment-specific grouping key
- reopen resolved or closed issues on regression
- increment counters and update timestamps atomically
- cap payload size and truncate oversize stack traces

### Authentication decision

This must be locked before implementation starts.

Recommended phase-1 posture:

- use one environment-scoped ingestion secret
- send it in a dedicated auth header
- validate it in the ingestion endpoint rather than depending on anonymous access

Because `hooks.py` currently has no active auth hooks, phase 1 should keep authentication local to the ingestion API unless a broader auth subsystem is introduced at the same time.

### Failure handling

If ingestion fails, do not fail silently.

At minimum:

- reject malformed batches with explicit error responses
- log authentication failures
- record repeated shipper failures locally on the host side

### Done when

Phase 1B is done when:

- a valid batch creates events and grouped issues correctly
- repeated matching events update the same issue
- resolved issues reopen on regression
- malformed or unauthenticated batches are rejected predictably

---

## 6. Phase 1C - Founder-runtime host shipper

### Goal

Cover runtime, worker, scheduler, and bench-log failures without changing every downstream app first.

### Build

Add a small founder-runtime shipper under `ops/founder_runtime/`.

Recommended paths:

- `/Users/francois.de/Documents/ifitwala_press/ops/founder_runtime/error_shipper/README.md`
- `/Users/francois.de/Documents/ifitwala_press/ops/founder_runtime/error_shipper/shipper.py`
- `/Users/francois.de/Documents/ifitwala_press/ops/founder_runtime/error_shipper/parsers.py`
- `/Users/francois.de/Documents/ifitwala_press/ops/founder_runtime/error_shipper/state.py`
- `/Users/francois.de/Documents/ifitwala_press/ops/founder_runtime/host/systemd/ifitwala-founder-error-shipper.service.template`
- `/Users/francois.de/Documents/ifitwala_press/ops/founder_runtime/host/systemd/ifitwala-founder-error-shipper.timer.template`

### Source coverage

Start with:

- container stdout/stderr
- mounted Frappe bench logs
- founder adapter failure output where available

### Host responsibilities

The shipper must:

- tail or scan known log sources
- detect exception-shaped records and failure markers
- attach environment, site, container, and process context
- batch events before posting to Press
- maintain a local cursor or offset state
- retry safely without infinite replay
- redact obvious secret patterns before transmission

### Implementation rule

Do not parse every log line into Press.

The shipper should emit only structured error candidates that match the approved control-plane scope.

### Done when

Phase 1C is done when:

- a founder host can post real error batches into Press
- repeated scans do not replay the same events indefinitely
- worker, scheduler, and backend exceptions all reach the same Press inbox

---

## 7. Phase 1D - Operator surfaces

### Goal

Turn ingestion into a usable control-plane attention surface.

### Build

Add:

1. a dedicated `Tenant Error Issue` list view
2. an environment-level error panel
3. a Press-home error attention block

Recommended touch points:

- `/Users/francois.de/Documents/ifitwala_press/ifitwala_press/api/views.py`
- `/Users/francois.de/Documents/ifitwala_press/ifitwala_press/public/js/tenant_environment.js`
- `/Users/francois.de/Documents/ifitwala_press/ifitwala_press/public/js/tenant_environment_list.js`
- workspace assets under `/Users/francois.de/Documents/ifitwala_press/ifitwala_press/ifitwala_press/workspace/ifitwala_press/`

### Minimum operator views

Environment detail should show:

- open issues
- last seen time
- occurrence count
- severity
- source system
- summary
- owner and status

The dedicated list should support filters for:

- sandbox vs production
- open, acknowledged, resolved, ignored
- source system
- critical only
- regressed
- most frequent

The Press-home block should show:

- critical unresolved issues
- new issues in the last 24 hours
- regressed issues
- recurring sandbox failures

### Done when

Phase 1D is done when an operator can go from home page to environment-level issue context without reading raw host logs first.

---

## 8. Phase 1.5 - Tenant-site Frappe push sync

### Goal

Add a second ingestion path for structured site-originated `Error Log` data after the founder path is working.

### Build posture

Press should only own the receiving contract in this repository.

The source-side sync job will likely land in tenant runtime operations or downstream app code, not primarily inside this repo.

### Press-side work

Add:

- a source-specific payload contract for site push
- mapping from Frappe `Error Log` fields into the normalized event shape
- guardrails so site push cannot spoof unrelated environments

### Defer

Do not block phase 1 on:

- perfect extraction of every scheduler failure variant
- downstream app helper APIs
- site pull access from Press into tenant databases

---

## 9. Testing plan

### Unit tests

Add isolated tests for:

- fingerprint normalization
- issue grouping key generation
- regression reopen behavior
- burst deduplication within the short collapse window
- secret redaction and stack truncation

### Integration tests

Add Frappe-level tests for:

- successful ingestion into both DocTypes
- invalid tenant/environment references
- duplicate issue-key prevention
- issue status actions

### Ops tests

Add shipper tests with fixture logs for:

- traceback extraction
- container-context parsing
- cursor persistence
- retry-safe batch replay behavior

### Repo metadata tests

Extend the existing repo metadata test file so the new architecture docs and code paths are expected explicitly.

---

## 10. Out of scope for phase 1

Do not include these in the first implementation:

- fleet-wide cross-environment fingerprint rollups
- full raw log archival in Frappe
- Cloud Logging, Loki, or OpenTelemetry integration
- automatic SLA escalation
- generalized incident management replacing `Tenant Incident`
- mandatory `ifitwala_ed` and `ifitwala_drive` capture helpers

These can follow once the basic founder-to-Press loop is proven.

---

## 11. Recommended execution order

Use this build sequence:

1. add `Tenant Error Event` and `Tenant Error Issue`
2. add ingestion service, normalization, and issue-status actions
3. lock the environment-scoped auth scheme
4. add the ingestion API
5. add founder shipper and host timer/service assets
6. add list and environment UI surfaces
7. add tenant-site push contract

This order keeps the core control-plane contracts ahead of automation, which matches the repo constitution.

---

## 12. Phase-1 acceptance criteria

Phase 1 is complete when all of the following are true:

- Press can receive authenticated founder-runtime error batches
- repeated matching failures group into one issue per environment
- resolved issues reopen on regression
- operators can acknowledge, resolve, ignore, and reopen issues from Press
- environment detail shows current open issues
- the Press home surface shows critical and regressed items
- raw evidence remains external or truncated rather than bloating control-plane tables

---

## 13. Recommended implementation decision

Approve this build target:

**Implement the first error-ingestion release as a Press-owned, environment-scoped error inbox with two DocTypes, one server-side ingestion service, one founder-runtime host shipper, and narrow operator triage surfaces.**

That is the smallest implementation that produces real operational value without violating the current Ifitwala_Press architecture.
