# 17_founder_runtime_image_and_host_bootstrap.md

## Purpose

This document locks the founder-mode runtime image and host bootstrap contract for **Ifitwala_Press**.

It exists so phase 1 no longer stops at an adapter scaffold.
It defines the minimum deployable host and image shape needed to run one real founder environment.

---

## 1. Runtime image contract

Phase 1 now requires one immutable runtime image that contains:

- `frappe`
- `ifitwala_ed`
- `ifitwala_drive`
- native `libmagic` support for governed upload MIME validation

That image should:

- start from an approved `frappe_docker`-style worker image
- bake the approved app refs into the image ahead of provisioning
- bake native runtime dependencies required by the app contract, including `libmagic`
- avoid tenant-specific credentials or storage settings
- be published under one pinned image tag

`IFITWALA_FOUNDER_RUNTIME_IMAGE` must point at that published tag.

---

## 2. Founder host bootstrap contract

The founder runtime host is still one same-VM founder deployment target.

For phase 1, the host must provide:

- one Ubuntu Minimal 25.04 VM baseline
- Docker Engine with `docker compose`
- `mariadb-client`
- `gcloud`
- `aws` CLI or equivalent S3-compatible upload tooling
- one runtime root containing:
  - per-environment Docker stacks
  - the shared edge proxy files
  - backup logs

This host bootstrap is now captured in `ops/founder_runtime/host/`.

---

## 3. Daily backup execution contract

Daily backups are no longer only a manual note.

The founder host now installs:

- a host-side `backup-all-sites.sh` runner
- a systemd service for backup execution
- a systemd timer for daily backup cadence

The backup flow is:

1. iterate every rendered founder runtime environment
2. run the site backup through `docker compose exec`
3. export the resulting archive to the S3-compatible backup tier
4. record a backup manifest under the founder runtime root

This makes the phase-1 backup posture operationally real on the founder VM.

---

## 4. What this does not solve yet

This still does not provide:

- a proven restore rehearsal
- automated TLS issuance
- multi-host orchestration
- Traefik
- GKE rollout

Those remain later steps after one real founder runtime is brought up and verified end to end.
