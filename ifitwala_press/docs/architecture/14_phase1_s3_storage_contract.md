# 14_phase1_s3_storage_contract.md

## Purpose

This document locks the phase-1 / MVP storage contract for **Ifitwala_Press**.

It exists to remove ambiguity about how tenant files and backups are stored while the founder-mode runtime is still simple.

---

## 1. Decision summary

The phase-1 baseline is:

- S3-compatible object storage for all retained tenant files
- one site-scoped storage contract per `Tenant Environment`
- **Frequent Access** storage for live files and attachments
- **Infrequent Access** storage for retained daily backups
- one backup export written outside the runtime/container boundary every day
- shared site storage visibility for the approved app bundle, including `ifitwala_ed` and `ifitwala_drive`

This is the storage baseline for MVP readiness.

---

## 2. Architectural intent

The control plane keeps storage logical and operator-visible.

It must record:

- file storage provider
- file storage class
- backup storage provider
- backup storage class
- storage quota
- latest exported backup path

It must not store:

- bucket secrets
- access keys
- provider-specific bucket internals unless an action contract truly needs them later

Exact bucket names, object prefixes, credentials, and lifecycle automation belong in runtime/adapter configuration, not in open-ended DocType fields.

---

## 3. Application coupling

Storage is site-scoped, not app-scoped.

That means:

- `ifitwala_ed` and `ifitwala_drive` run inside the same tenant site contract
- active files and attachments should resolve through the same primary S3-compatible storage backend
- if `ifitwala_drive` surfaces note-related or attachment-linked content that originates across the approved app bundle, it should read from the same site storage namespace rather than a second silo

This keeps the platform aligned with the shared-runtime, separated-state model.

---

## 4. Backup contract

Backups are not allowed to live only in the runtime filesystem.

Phase 1 requires:

- daily exported site backups
- retained backups written to the less-frequent storage class
- operator-visible backup freshness through `backup_export_path` and backup timestamps
- manual restore discipline that works even if the original runtime has been removed

Later lifecycle policies may add stronger retention, restore testing, or archival tiers.
Those do not change the phase-1 baseline.

---

## 5. Control-plane contract

`Tenant Policy` owns the default storage posture:

- default file storage provider/class
- default backup storage provider/class
- backup frequency
- backup retention days

`Tenant Environment` owns the actual applied environment posture:

- file storage provider/class
- backup storage provider/class
- storage quota
- latest backup export path

`Ifitwala_Press` must validate that a live environment is not marked ready while drifting away from this storage contract.
