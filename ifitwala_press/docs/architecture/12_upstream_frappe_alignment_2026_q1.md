# 12_upstream_frappe_alignment_2026_q1.md

## Purpose

This note records which upstream Frappe projects should actively guide **Ifitwala_Press** and how.

It exists to prevent two common failures:

- rebuilding solved infrastructure patterns from scratch
- cargo-culting full Frappe Cloud / Press complexity into an MVP that only needs an internal founder-mode control plane

This note reflects an explicit review of the following upstream repositories on **2026-04-02**:

- `frappe/frappe_docker`
- `frappe/agent`
- `frappe/press`

The goal is not to copy those projects blindly.
The goal is to borrow the right layer from each one.

---

## 1. `frappe_docker` guidance

### What it is
`frappe_docker` is the containerization and compose reference for the Frappe stack.

Its README is explicit:

- `compose.yaml` is the base file for production setups
- `pwd.yml` is a disposable demo environment
- the quick demo setup is not the right path for custom apps

### What matters for Ifitwala_Press

For our MVP founder runtime:

- use `frappe_docker` as the reference for the same-VM dockerized runtime
- do not base our real demo runtime on `pwd.yml`
- use the production compose path and a custom app image / approved bundle instead

### Relevant recent upstream signal

Recent `frappe_docker` activity between late December 2025 and 2026-03-23 shows useful operational focus:

- release cadence is active (`v2.0.0` on 2026-01-26, `v2.1.0` on 2026-02-07, `v2.1.1` on 2026-03-05, `v2.2.0` on 2026-03-19)
- recent work improved reverse-proxy correctness for backend and Socket.IO traffic
- recent work added shared nginx security headers to production and custom images
- recent work added an nginx-proxy + ACME companion alternative

### Decision for us

`frappe_docker` should guide:

- founder runtime layout
- compose structure
- reverse proxy behavior
- security header posture
- persistent volume expectations

It should not define our control-plane model.

---

## 2. `agent` guidance

### What it is
`agent` is the remote execution / management layer used with Press.

Its own README is explicit that it works with Press and provides a CLI/service layer for remote site and bench operations.

### What matters for Ifitwala_Press

`agent` is not phase-1 MVP infrastructure.

It becomes relevant when Ifitwala_Press needs to:

- run actions on a second host
- manage remote runtimes
- coordinate restore, usage refresh, or system checks without SSH-driven ad hoc scripts

### Relevant recent upstream signal

Recent `agent` activity between late December 2025 and 2026-03-23 is especially relevant in three areas:

- physical database restoration fixes and follow-ups
- database usage / table-usage refresh APIs
- proxy and proxied-server handling improvements

This means the upstream direction is still strongly focused on:

- remote execution correctness
- restoration safety
- operational visibility

### Decision for us

Do not adopt `agent` before we have a stable founder runtime flow.

Adopt `agent` later when:

- demo provisioning on one VM is proven
- we introduce a separate runtime host
- we want governed remote execution instead of shelling directly on the control-plane host

Until then:

- do not simulate agent behavior inside Desk pages
- do not hide host operations behind summary views
- keep browser or operator-run host commands explicit when founder-mode execution is still manual

---

## 3. `press` guidance

### What it is
`press` is the full Frappe Cloud hosting product.

Its README is explicit that under the hood it uses:

- Frappe Framework
- Frappe UI
- Agent
- Docker
- Ansible

It is a serious reference architecture for operating hosted Frappe fleets, not a small founder-MVP template.

### What matters for Ifitwala_Press

Press should guide our mission at the pattern level:

- step-driven operational actions
- governed site lifecycle
- cloning and restore safety
- failover thinking
- environment visibility
- release and upgrade discipline

Press should not define our phase-1 scope at the product level.

We do not need in MVP:

- public self-serve provisioning complexity
- full marketplace behavior
- full billing orchestration
- full server-fleet automation

### Relevant recent upstream signal

Recent `press` activity between late December 2025 and 2026-04-02 shows active work in areas that matter to us later:

- failover management steps and related fixes
- release actions
- cloning from the Desk
- refresh of database usage from the site layer
- site-action cleanup / cancellation behavior
- server firewall rollout and validation hardening
- remote/server health checks that incorporate agent or egress behavior

The most relevant recent example is the March 2026 firewall rollout:

- [`press#5500`](https://github.com/frappe/press/pull/5500), merged on **2026-03-07**, replaced custom `iptables` setup / teardown playbooks with one sync-driven `ufw` + pinned `ufw-docker` flow
- [`press#5507`](https://github.com/frappe/press/pull/5507) auto-created the firewall document after server creation instead of relying on a manual setup step
- later March follow-ups such as [`press#5521`](https://github.com/frappe/press/pull/5521), [`press#5533`](https://github.com/frappe/press/pull/5533), and [`press#5586`](https://github.com/frappe/press/pull/5586) show where the first rollout was corrected:
  - rule sync needed to be idempotent and validation-heavy
  - the useful rule shape was inbound `source + port + protocol + action`, not source/destination pairs
  - protected IP allowlists had to include monitoring and proxy traffic, not only user-entered rules

This is the signal we should care about, not the billing-only or marketplace-only work.

### Decision for us

Borrow from Press now:

- explicit action names
- step-oriented operational state
- cloning / restore / failover mental model
- “operator visible progress” as a first-class requirement
- a command-center home surface with an attention queue that routes operators into the right records and actions
- sync-style firewall convergence instead of brittle setup / teardown actions
- validation-first handling for network rules and protected allowlists

Defer from Press for now:

- full orchestration breadth
- multi-product monetization concerns
- platform features for external users
- broad server-fleet execution patterns that depend on Agent
- the generic `Server` / `Server Firewall` product surface as-is, because our founder phase is still one internal runtime host plus environment records

---

## 4. Mission alignment for Ifitwala_Press

The product mission remains:

- internal-only control plane
- fast founder-mode demo provisioning
- governed lifecycle for sandbox and later production environments
- safe migration path toward stronger isolation later

That means the immediate architecture choice is:

- `ifitwala_press` remains the operator product
- `frappe_docker` guides the founder runtime implementation
- `agent` is deferred until we have remote execution needs
- `press` guides workflow and orchestration patterns, not MVP feature scope
- the control-plane home may borrow Press-style operational visibility, but it should remain a read-side summary surface over our own DocTypes
- for firewalling, we should copy Press's host-hardening mechanism (`ufw` + `ufw-docker` + sync) but not copy its server-centric data model blindly

The core translation is:

- host-level port exposure belongs to the founder runtime host contract
- tenant-specific ingress restriction belongs to the shared edge proxy and environment policy
- those are related, but they are not the same control-plane object

---

## 5. Concrete next steps

The next implementation steps should follow this order:

1. prove one founder demo runtime using `frappe_docker` production-style compose and a custom app bundle containing:
   - `frappe`
   - `ifitwala_ed`
   - `ifitwala_drive`
2. keep seeded demo data and exported backup paths explicit on `Tenant Environment`
3. wire the first founder provisioning adapter from `ifitwala_press` actions to the founder runtime
4. add a founder-host firewall sync path using `ufw` + `ufw-docker`, but keep it host-scoped and adapter-owned
5. keep tenant-specific ingress allowlisting at the founder edge proxy layer instead of pretending `ufw` can distinguish one tenant domain from another on shared ports `80/443`
6. support early sandbox teardown through governed action
7. only after this flow is real, evaluate `agent` for remote execution
8. only after remote execution exists, move broad trial density to a shared demo runtime instead of keeping one heavy stack per environment by default
9. only after that, borrow more Press-grade orchestration patterns

This keeps the MVP honest:

- no fake orchestration
- no drift into a generic cloud product
- no delay in proving the demo lifecycle that the business actually needs
