# Founder Runtime Diagnostics

This directory holds the first founder-mode diagnostic commands for a Google-Cloud-first deployment.

The current diagnostic set is:

- `gcp-platform-doctor.sh`
  Founder VM and Google Cloud platform preflight
- `founder-runtime-doctor.sh`
  One environment runtime health check
- `storage-backup-doctor.sh`
  Cloud Storage and backup freshness check for one environment

## Usage

- `./gcp-platform-doctor.sh [/etc/ifitwala-founder-runtime/adapter.env]`
- `./founder-runtime-doctor.sh <site-name-or-runtime-dir> [/etc/ifitwala-founder-runtime/adapter.env]`
- `./storage-backup-doctor.sh <site-name-or-runtime-dir> [/etc/ifitwala-founder-runtime/adapter.env]`

These commands are intentionally:

- read-only
- founder-host focused
- aligned with the current runtime contract, where object-storage env names use `GCS_*`
- opinionated toward Google Cloud services such as Compute Engine, Cloud DNS, Cloud Storage, and Artifact Registry

Exit code `0` means no failures.
Exit code `1` means at least one failure was detected.
