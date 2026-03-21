# Planning Note: Cloud SQL / Managed MariaDB Posture

## Purpose

This note records how managed database planning should be treated in **Ifitwala_Press**.

It is not a phase-1 mandate.
It is not a replacement for the founder-mode rollout policy.

Its job is to clarify:
- how managed database options fit the long-term architecture
- what phase 1 should and should not depend on
- how the repository baseline affects DB planning

---

## 1. Repository baseline

The current repository database baseline is:

- MariaDB 11.8

This file must stay aligned with that project-level decision.

Any later managed DB rollout plan must therefore:
- target the approved MariaDB 11.8 line
- include a compatibility spike before production commitment
- avoid reintroducing older version guidance as if it were the active repo standard

### Current planning correction

Do not treat "Cloud SQL for MariaDB" as the active plan.

The current repository posture is:

- phase 1 stays on self-managed MariaDB 11.8
- managed DB adoption is deferred
- any future managed path must be re-evaluated against then-current provider support

---

## 2. Phase-1 rule

Managed database automation is not required for the MVP.

Phase 1 may legitimately run with:
- one shared founder-mode runtime
- manual or semi-manual database provisioning
- one database per site
- manual backup and restore verification at small scale

This matches the rollout policy and initial build-order documents.

The control plane must still model:
- database mode
- placement intent
- backup expectations
- lifecycle consequences

But phase 1 does not need to automate managed DB creation.

---

## 3. Why managed DB still matters later

A managed DB path may still matter later because it can reduce:
- operational toil
- backup burden
- restore complexity
- high-availability overhead

For standard and premium operations later on, a managed DB path may support:
- shared DB fleet for standard tenants
- stronger isolation for premium or VIP tenants
- clearer restore discipline
- more repeatable provisioning

This is a phase-2-or-later concern unless operational reality proves it earlier.

---

## 4. Constraints that still apply if managed DB is adopted later

If a managed DB path is adopted later, design around these control-plane constraints:

### A. One database per site remains mandatory

Even on a shared managed instance:
- one tenant environment
- one site
- one database

must remain the control-plane rule.

### B. Private networking only

The DB should not be exposed publicly.

Use private connectivity between runtime hosts and the DB layer.

### C. Character set and collation must be deliberate

The platform must still enforce a UTF-8 capable server configuration appropriate for Frappe and your app stack.

### D. Privilege model must be compatible with managed services

Provisioning logic should not assume unrestricted root-style behavior from the runtime host.

The control plane should eventually support a split-privilege pattern where:
- infrastructure or platform-level credentials create logical databases and users
- runtime hosts receive only tenant-scoped credentials

### E. Version choice must be validated, not assumed

Because this repository chooses MariaDB 11.8, that exact baseline must be proven by test or spike in your own stack before committing to a managed rollout.

---

## 5. Recommended founder-mode posture now

For the current MVP, keep the DB posture simple:

- one founder-mode runtime shape
- one MariaDB 11.8 baseline
- one database per site
- manual or semi-manual DB creation if needed
- explicit backup and restore runbook

This keeps the control-plane model clean without forcing early provider automation.

---

## 6. Recommended later migration posture

Only after the control-plane backbone is proven should the platform revisit managed DB automation.

That later step should follow this order:

1. prove manual lifecycle flow end to end
2. prove MariaDB 11.8 compatibility in the real app stack
3. standardize database naming, user creation, and credential handling
4. model placement intent clearly on `Tenant Environment`
5. only then automate managed DB provisioning behind service boundaries

---

## 7. Decision rule

Do not adopt managed DB work just because it sounds cleaner.

Adopt it when it materially improves one or more of:
- operator safety
- restore discipline
- production consistency
- blast-radius control
- time spent on repetitive DB operations

If it does not clearly improve those outcomes yet, defer it.
