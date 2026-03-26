# 18_founder_gcp_diagnostics.md

## Purpose

This document locks the first founder-mode diagnostic commands for a Google-Cloud-first phase 1 deployment.

It exists so operators can run a tight, repeatable incident checklist without jumping straight into raw shell spelunking.

---

## 1. Diagnostic posture

The first diagnostic set should stay:

- founder-host local
- read-only
- fast to run
- narrow enough to match the actual MVP runtime

It is not a replacement for later Cloud Monitoring dashboards or deeper telemetry.

---

## 2. Approved commands

Phase 1 now approves these commands under `ops/founder_runtime/diagnostics/`:

- `gcp-platform-doctor.sh`
- `founder-runtime-doctor.sh`
- `storage-backup-doctor.sh`

These cover:

- Google Cloud account and project reachability
- Cloud DNS and founder-VM alignment
- Docker and backup timer readiness
- one tenant runtime stack health
- Cloud Storage bucket and backup visibility

---

## 3. Founder Google Cloud assumptions

For the current founder path, the diagnostics assume:

- Compute Engine for the founder VM
- Artifact Registry or another Google-Cloud-hosted image path for the runtime image
- Cloud DNS for hostname intent
- Cloud Storage for files and backup object visibility

The current runtime env still carries object-storage values under `S3_*` names.

For phase 1 diagnostics, those names are treated as the logical object-storage contract even when the actual provider is Google Cloud Storage.

---

## 4. Operator workflow

The intended operator order is:

1. run `gcp-platform-doctor.sh`
2. if the issue is environment-specific, run `founder-runtime-doctor.sh <site>`
3. if the issue touches files, retention, or restore safety, run `storage-backup-doctor.sh <site>`

This gives operators one concrete and repeatable first response path.
