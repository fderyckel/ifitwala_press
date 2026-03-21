# 11_phase1_deployment_contract.md

## Purpose

This document locks the concrete phase-1 deployment contract for **Ifitwala_Press**.

It exists to prevent deployment drift while the control-plane backbone is still being built.

This is a founder-mode contract.
It does not replace the long-term target architecture.

---

## 1. Phase-1 decision summary

Phase 1 should keep a simple deployment shape without blurring the platform model.

The current contract is:

- `ifitwala.com` is the public brand/docs site
- `press.ifitwala.com` or `ops.ifitwala.com` is the internal control-plane site
- `*.ifitwala.com` is the tenant hostname space
- the public site and the control plane must not be the same Frappe site
- self-managed MariaDB 11.8 is the current database baseline
- one database per site remains mandatory
- routing automation is optional in phase 1
- provisioning may be manual or semi-automated in phase 1

---

## 2. Mandatory separation rules

### 2.1 Public site vs control plane

The public site and the control plane must be distinct at the site and hostname level.

Use:

- `ifitwala.com` for the public-facing site
- `press.ifitwala.com` or `ops.ifitwala.com` for the internal operator system

Do not:

- run both surfaces as one Frappe site
- mix operator workflows into the public brand/docs site
- treat public pages as the control-plane UI

### 2.2 Tenant runtime surface

Tenant environments should live under the managed tenant hostname space, normally:

- `schoolslug.ifitwala.com`
- sandbox/demo variants under the same controlled namespace if needed

The control plane owns routing intent for those environments.
The infra layer later applies that intent.

---

## 3. Founder-mode infrastructure contract

### 3.1 Acceptable shape

Phase 1 may run with a simple founder-mode footprint such as:

- one public web host for `ifitwala.com`
- one control-plane host for `press.ifitwala.com`
- one shared tenant runtime host or pool

This host-level split is recommended.
It is not a phase-1 requirement if cost pressure is real.

### 3.2 Minimum acceptable consolidation

If infrastructure must be temporarily consolidated for founder mode:

- the public site and the control plane must still be separate Frappe sites
- tenant runtime may temporarily share a low-cost host with the control plane only if the risk is explicit and temporary
- this consolidation must not change the modeled separation of tenant runtime, routing intent, and DB placement

The site boundary is mandatory.
The machine boundary is recommended.

---

## 4. Database contract

### 4.1 Current baseline

The current phase-1 database baseline is:

- self-managed MariaDB 11.8

### 4.2 Mandatory rules

- one site = one database
- production backups must exist
- restore discipline may be manual in phase 1 but must be real
- DB placement and DB mode must still be recorded on `Tenant Environment`

### 4.3 Explicit non-goal for phase 1

Phase 1 does not require:

- Cloud SQL adoption
- managed DB automation
- provider-driven DB provisioning

---

## 5. Runtime contract

The founder runtime must still be governed.

At minimum, phase-1 procedures should make explicit:

- the authoritative Docker runtime shape
- the approved app bundle used by the shared runtime
- how site creation is performed
- how app installation is performed
- which volumes or directories are persisted
- how common bench configuration is stored and updated

Shared runtime means shared only across environments with a compatible approved app bundle.

---

## 6. Routing contract

Phase 1 may use manual routing steps.

The control plane must still record:

- primary domain
- routing mode
- DNS readiness
- TLS readiness
- host header value where relevant

Traefik remains a later routing implementation target.
Phase 1 does not need full Traefik automation.

---

## 7. Operator workflow contract

The deployment contract must support this manual or semi-automated flow:

1. create or qualify a tenant in the control plane
2. create a sandbox or production environment record through server-side action
3. assign site name, policy, hosting tier, DB mode, and routing intent
4. perform manual or semi-automated provisioning against the founder runtime
5. update lifecycle state through governed actions only
6. record the outcome in transition logs

No critical lifecycle step should depend on freeform field editing.

---

## 8. Non-goals for phase 1

Do not treat these as MVP blockers:

- MIG rollout
- full Traefik automation
- Redis Memorystore split
- Google load balancer adoption
- managed DB automation
- full GCP API orchestration

The control-plane backbone and one proven manual lifecycle flow matter more than any of those.
