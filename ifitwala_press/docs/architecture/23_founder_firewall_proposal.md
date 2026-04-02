# 23_founder_firewall_proposal.md

## Purpose

This note records how the recent Frappe Press firewall work should be translated into **Ifitwala_Press**.

It exists because copying Press literally would be the wrong move.
Press manages fleets of servers.
Ifitwala_Press currently manages tenant environments on one founder-mode runtime host with a shared edge proxy.

The right question is not "How do we clone `Server Firewall`?"
The right question is:

- what host-hardening pattern should we borrow now
- what tenant-access behavior should stay environment-scoped
- where should each responsibility live in our control plane

---

## 1. Verified upstream signal

The key upstream PR is:

- [`frappe/press#5500`](https://github.com/frappe/press/pull/5500), merged on **2026-03-07**

That change did three important things:

- removed separate firewall setup / teardown playbooks
- moved Press to one sync-driven `ufw` flow
- installed pinned `ufw-docker` so Docker-published traffic would still respect firewall intent

Important follow-up PRs in March 2026 clarified what actually mattered in practice:

- [`frappe/press#5507`](https://github.com/frappe/press/pull/5507)
  Auto-create the firewall record from server creation
- [`frappe/press#5521`](https://github.com/frappe/press/pull/5521)
  Stop syncing protocol until the rule model supports it correctly
- [`frappe/press#5533`](https://github.com/frappe/press/pull/5533)
  Change the rule shape from destination IP to inbound port
- [`frappe/press#5586`](https://github.com/frappe/press/pull/5586)
  Include proxy IPs in the protected allowlist

Bottom line from upstream:

- sync beats setup / teardown
- host firewalls need explicit protected allowlists
- inbound firewall rules are more useful as `source CIDR + port + protocol + action`
- dashboard UX comes after the rule model and sync path are correct

---

## 2. Why Press cannot be copied 1:1 here

Press models firewalling per server.
That makes sense for Frappe Cloud because they already manage explicit server records and remote execution.

Ifitwala_Press currently does not.
Our founder-stage runtime shape is different:

- one founder VM
- one shared edge proxy using host networking
- one per-environment nginx bound only to `127.0.0.1:${HTTP_PORT}`
- many tenant domains potentially sharing public ports `80` and `443`

That means two different control problems exist:

### A. Host firewall problem

This is about:

- who can reach SSH
- whether `80/443` are open
- whether monitoring or proxy infrastructure is accidentally blocked
- whether Docker-published ports bypass host policy

This is a **host-scoped** problem.

### B. Tenant ingress restriction problem

This is about:

- whether one school site should be public
- whether a demo site should be reachable only from allowlisted IPs
- whether a sandbox should be temporarily blocked from public access

This is an **environment-scoped** problem.

On our current founder topology, `ufw` cannot distinguish tenant A from tenant B on shared `80/443`.
That distinction belongs in the shared edge proxy configuration, not the host firewall.

---

## 3. Proposed implementation for Ifitwala_Press

### 3.1 Phase 1: founder host firewall baseline

Implement a founder-host firewall baseline now.
Do **not** wait for a generic server-fleet model.

Use the same mechanism Press moved to:

- `ufw`
- pinned `ufw-docker`
- one idempotent sync script, not setup / teardown commands

#### Scope

This phase protects the founder VM itself.
It does not yet introduce tenant-specific IP allowlists.

#### Required inbound posture

- allow `80/tcp`
- allow `443/tcp`
- allow `22/tcp` only from approved operator CIDRs
- allow monitoring / admin source CIDRs that we explicitly trust
- never expose per-environment loopback nginx ports publicly

#### Required implementation changes

- update [bootstrap-founder-vm.sh](/Users/francois.de/Documents/ifitwala_press/ops/founder_runtime/host/bootstrap-founder-vm.sh) to install `ufw`
- add a new host script such as `ops/founder_runtime/host/sync-host-firewall.sh`
- fetch pinned `ufw-docker` in that script and install its service
- source firewall inputs from `adapter.env` or a sibling host config file
- run the sync script during founder host bootstrap
- allow the founder runtime adapter to re-run firewall sync explicitly when needed

#### Recommended config keys

- `IFITWALA_FOUNDER_RUNTIME_FIREWALL_ENABLED`
- `IFITWALA_FOUNDER_RUNTIME_ALLOWED_SSH_CIDRS`
- `IFITWALA_FOUNDER_RUNTIME_ALLOWED_MONITOR_CIDRS`
- `IFITWALA_FOUNDER_RUNTIME_ALLOWED_ADMIN_CIDRS`

If proxy or load-balancer source IPs become relevant later, add a dedicated config key for them.
Do not bury those exceptions in handwritten shell edits on the VM.

### 3.2 Phase 1.5: environment ingress policy at the edge proxy

Tenant-specific restriction should be implemented at the founder edge proxy, not `ufw`.

That means:

- extend [route.conf.template](/Users/francois.de/Documents/ifitwala_press/ops/founder_runtime/edge_proxy/route.conf.template) to support optional allow / deny directives
- render route snippets from environment policy and environment access settings
- keep this as a server-authoritative sync action from `ifitwala_press`

Recommended control-plane shape:

- add `ingress_access_mode` on `Tenant Environment`
  - `Public`
  - `Allowlisted`
  - `Disabled`
- add default ingress behavior on `Tenant Policy`
- add a small child table for allowlisted CIDRs only when `ingress_access_mode = Allowlisted`

This keeps the system aligned with current repo reality:

- policy owns defaults
- environment owns actual access state
- the shared edge proxy applies routing and access intent

### 3.3 Later phase: first-class runtime host records

Only after we manage more than one runtime host or introduce VIP dedicated runtime placement should we add first-class host records and host-firewall documents.

At that stage, a host-level DocType becomes justified.
Before that, a generic `Server Firewall` clone would add abstraction without operational leverage.

---

## 4. Proposed service boundary

### `ifitwala_press`

Should own:

- firewall intent for the founder host
- environment ingress intent
- validation of CIDRs, ports, and allowed modes
- explicit sync actions
- operator-visible result state
- audit trail of who changed access rules

### Founder host scripts / adapter

Should own:

- `ufw` package installation
- `ufw-docker` installation and service wiring
- actual host rule convergence
- route file rendering on disk
- nginx reload after route changes

This matches the existing repo split:

- control plane owns intent
- adapter / host assets own concrete Docker and host execution

---

## 5. Specific proposal

If the goal is to implement the Press firewall idea for founder mode without overshooting scope, the build order should be:

1. Add founder-host `ufw` + `ufw-docker` sync as a host bootstrap and adapter capability.
2. Keep the public tenant web path on `80/443` open at host level.
3. Add environment-level ingress restriction at the shared edge proxy, not in `ufw`.
4. Only after multiple runtime hosts exist, introduce a real host/firewall DocType pair.

This is the safest translation of the Press work for our current architecture.

It gives us:

- real host hardening now
- no false per-tenant firewall promises on shared ports
- no premature server-fleet modeling
- a clean path to later Traefik middleware or dedicated-host firewall policies

---

## 6. What not to do

Do not:

- copy Press's `Server Firewall` DocType directly into Ifitwala_Press right now
- model tenant-specific website access as raw host firewall rules on shared `80/443`
- add setup and teardown firewall buttons instead of one sync path
- expose per-environment published nginx ports beyond loopback
- hardcode one-off manual `ufw` exceptions on the founder VM outside repo-managed assets

Those choices would add noise and weaken auditability.

---

## 7. Recommended next code changes

If this proposal is approved, the first implementation pass should touch:

- [bootstrap-founder-vm.sh](/Users/francois.de/Documents/ifitwala_press/ops/founder_runtime/host/bootstrap-founder-vm.sh)
- [adapter.env.example](/Users/francois.de/Documents/ifitwala_press/ops/founder_runtime/adapter.env.example)
- [adapter.py](/Users/francois.de/Documents/ifitwala_press/ops/founder_runtime/adapter.py)
- [13_founder_runtime_adapter_contract.md](/Users/francois.de/Documents/ifitwala_press/ifitwala_press/docs/architecture/13_founder_runtime_adapter_contract.md)
- [17_founder_runtime_image_and_host_bootstrap.md](/Users/francois.de/Documents/ifitwala_press/ifitwala_press/docs/architecture/17_founder_runtime_image_and_host_bootstrap.md)
- [route.conf.template](/Users/francois.de/Documents/ifitwala_press/ops/founder_runtime/edge_proxy/route.conf.template)

The first schema pass should stay small:

- one environment ingress mode field
- one policy default field
- one allowlist child table only if we need restricted sandboxes immediately
