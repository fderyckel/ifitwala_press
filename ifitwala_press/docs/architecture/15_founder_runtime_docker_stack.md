# 15_founder_runtime_docker_stack.md

## Purpose

This document locks the first real Docker stack shape for the founder runtime used by **Ifitwala_Press**.

It exists to move phase 1 beyond abstract runtime intent and into an explicit same-VM container architecture.

---

## 1. MVP runtime decision

The founder runtime for phase 1 should use:

- one same-VM Docker Compose stack per tenant environment
- one approved runtime image containing:
  - `frappe`
  - `ifitwala_ed`
  - `ifitwala_drive`
- one external MariaDB 11.8 baseline
- local Redis containers for founder mode
- one per-environment nginx bound to a loopback host port
- one site-scoped S3-compatible storage contract
- Google Cloud DNS changes through `gcloud dns ...`

This is intentionally founder-stage.
It is not the final multi-host or Traefik architecture.

---

## 2. Why this shape

This stack keeps the control-plane contract honest while avoiding premature fleet complexity.

It gives us:

- a concrete runtime shape we can render from `ifitwala_press`
- a direct path to proving `ifitwala_ed` + `ifitwala_drive` together
- explicit S3 runtime configuration outside DocTypes
- DNS automation via the Google Cloud CLI without forcing full GCP API orchestration
- a clear future migration path toward Traefik, with a shared founder nginx edge proxy now bridging hostname routing

---

## 3. Runtime layout

Each provisioned environment gets a dedicated host directory containing:

- `compose.yaml`
- `.env`
- `sites/common_site_config.json`
- `nginx/default.conf`
- `runtime-config/payload.json`
- `runtime-config/provision.sql`
- `runtime-config/runtime-plan.json`
- logs and site volume directories

The runtime image stays immutable.
Per-environment state and config stay on the host.

---

## 4. Service layout

The founder Compose stack contains:

- `backend`
- `worker`
- `scheduler`
- `nginx`
- `redis-cache`
- `redis-queue`
- `redis-socketio`

This is a founder-mode operational split, not the final production split.

It is sufficient for:

- site bootstrap
- web access behind a later shared edge proxy
- background jobs
- scheduled jobs
- future daily backup automation

---

## 5. Routing and DNS posture

Phase 1 uses Google Cloud DNS for hostname intent.

The adapter should:

- derive or accept the primary domain
- create or update the Cloud DNS `A` record through `gcloud`
- store `dns_ready` in the control plane when that record exists
- return `host_header_value`

The adapter now cooperates with a shared founder edge proxy.

That means:

- DNS can be automated now
- per-environment nginx binds to a loopback host port
- a shared founder nginx edge proxy can route those hostnames today
- Traefik remains the later routing target

---

## 6. Storage posture

The runtime consumes the S3 storage contract already locked elsewhere:

- live files use the frequent-access class
- retained daily backups use the less-frequent class
- `ifitwala_ed` and `ifitwala_drive` share the same site storage namespace
- bucket names and credentials live in runtime configuration, not DocTypes

---

## 7. Adapter flow

The founder runtime adapter should perform these steps:

1. read the control-plane JSON payload
2. derive runtime directory, compose project name, DB name, host port, and storage prefixes
3. render the runtime files
4. optionally apply the MariaDB provisioning SQL
5. optionally run `docker compose up -d`
6. optionally bootstrap the site and install `ifitwala_ed` + `ifitwala_drive`
7. optionally create or update the Cloud DNS record with `gcloud dns ...`
8. return structured metadata to `ifitwala_press`

This is the approved founder-mode execution order.
