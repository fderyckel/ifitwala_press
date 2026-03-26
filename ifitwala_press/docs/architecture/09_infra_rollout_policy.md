# 09_infra_rollout_policy.md

## Purpose

This document defines the staged infrastructure rollout posture for **Ifitwala_Press**.

The goal is to keep the control-plane model stable while allowing the actual deployment shape to mature in step with revenue, operational load, and customer risk.

This is not a replacement for the core architecture documents.
It is a rollout companion that makes founder-stage reality explicit.

---

## 1. Rollout principle

The control plane must model:
- tenant and environment separation
- one site = one database
- lifecycle state
- hosting tier
- routing intent
- policy
- health, cost, and subscription visibility

The deployment implementation may mature in stages.

Early-stage cost efficiency is acceptable.
Model drift is not.

---

## 2. Founder Mode

### Purpose
Support early customers and trials at low fixed cost while proving the operating model manually.

### Acceptable runtime shape
- one low-cost shared runtime is acceptable
- self-managed deployment is acceptable
- consolidated services are acceptable if the control-plane intent stays explicit

### Mandatory site separation
Founder mode does not permit collapsing all surfaces into one site.

The minimum required separation is:
- one public-facing site for `ifitwala.com`
- one internal control-plane site for `press.ifitwala.com` or `ops.ifitwala.com`

These may temporarily share founder-stage infrastructure if necessary.
They must not be the same Frappe site.

### Runtime contract for founder mode
Founder mode still needs a concrete runtime contract.

At minimum, founder-mode docs and procedures should make explicit:
- which Docker runtime shape is authoritative
- which directories or volumes are persisted
- how app bundles are built or pulled
- how site creation and site app installation are performed
- how common bench config is stored and updated

Shared runtime in founder mode means shared only across environments with a compatible approved app bundle.
If a school needs a materially different customization stack, it may need:
- a separate shared compatibility pool
- a reserved runtime
- or a dedicated runtime

Do not treat running production containers as mutable.
Adding or changing apps should happen by approving a bundle or release and rolling out a new image.

### Acceptable DB placement
- shared DB fleet is acceptable
- self-managed DB placement is acceptable
- one database per site remains mandatory

### Managed DB posture in founder mode
Managed DB adoption is not a founder-mode requirement.

Phase 1 should assume:
- self-managed MariaDB 11.8
- manual or semi-manual DB provisioning
- explicit backup and restore runbooks

Do not make Cloud SQL or similar provider automation a phase-1 dependency.

### Backup expectation
- backups must exist for production
- sandbox backups may be lighter-weight
- restore discipline may be manual but must be real

### Founder-mode backup note
For founder-stage dockerized runtimes on one VM:

- do not rely on backups remaining only inside the container filesystem
- each environment must have its latest successful site backup copied or written to storage outside the container
- the phase-1 / MVP baseline is S3-compatible object storage rather than container-local or host-only retention
- live site files should use the frequent-access class, while retained daily backups should use the less-frequent class
- for demos and sandbox environments, keeping the latest successful backup may be enough initially
- for production environments, retention must follow the assigned policy and must not depend on container survival
- manual restore from that exported backup must be possible even if the original container is gone

### Health monitoring expectation
- simple health checks are acceptable
- manual review and heuristic summaries are acceptable
- failures must still be visible in the control plane

### Automation expectation
- manual and semi-automated actions are acceptable
- provisioning checklists or operator-run procedures are acceptable
- provider API automation is explicitly optional

---

## 3. Standard Production Target

### Purpose
Support normal live customer operations with stronger operational consistency and lower manual burden.

### Acceptable runtime shape
- shared runtime remains acceptable
- deployment should become more repeatable
- routing and backup handling should become more standardized
- compatible app bundles should be grouped into deliberate runtime pools rather than mixed casually

### Acceptable DB placement
- shared DB fleet remains the default
- placement may be self-managed or managed
- dedicated DB should be used only when justified

### Backup expectation
- production backup policy must be explicit
- restore readiness should be reviewed on a schedule
- the standard expectation is off-container, S3-compatible backup storage
- retention should be policy-driven rather than operator memory
- backup freshness should become visible in the control plane

### Health monitoring expectation
- scheduled summaries should replace purely manual checks
- production health signals should be refreshed consistently

### Automation expectation
- semi-automated execution should become the norm
- selected routing, backup, and provisioning steps may be automated once proven manually

---

## 4. Premium / VIP Target

### Purpose
Support tenants that justify stronger isolation, clearer blast-radius control, and tighter operational guarantees.

### Acceptable runtime shape
- shared, reserved, or dedicated runtime may be used based on risk and contract
- the chosen mode must be explicit in the control plane
- tenant-specific custom app combinations may justify reserved or dedicated runtime even when DB isolation is already stronger

### Acceptable DB placement
- dedicated DB instance is the normal expectation
- placement may be self-managed or managed depending on stage and commitments

### Backup expectation
- stronger retention and restore discipline is expected
- backup freshness and restore confidence should be visible
- off-host backup storage is the expected baseline
- restore testing should be tracked and reviewed explicitly

### Health monitoring expectation
- monitoring should be more frequent and more reliable
- degraded state should be surfaced quickly

### Automation expectation
- automation is justified where it reduces operator error and improves recoverability
- provider-specific implementation should still sit behind control-plane intent

---

## 5. Decision rule

When choosing infrastructure work, ask:

1. Does this improve operator clarity or safety now?
2. Does this preserve a migration path to stronger isolation later?
3. Does this avoid locking the model to a premature provider assumption?
4. Is this justified by current customers, revenue, or risk?

If the answer is no, defer it.
