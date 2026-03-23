# 13_founder_runtime_adapter_contract.md

## Purpose

This document locks the first founder-mode runtime adapter contract for **Ifitwala_Press**.

It exists to make one thing explicit:

- `Ifitwala_Press` owns the operator workflow and lifecycle
- an external founder-runtime adapter owns the actual dockerized runtime work

This prevents us from burying pet-server shell logic inside random Desk code while still allowing a pragmatic founder-stage implementation.

---

## 1. MVP intent

The MVP goal is narrow:

- from `Ifitwala_Press`, create a sandbox environment record
- optionally trigger founder-mode runtime provisioning immediately
- launch one same-VM dockerized runtime for:
  - `frappe`
  - `ifitwala_ed`
  - `ifitwala_drive`
- optionally restore seeded demo data from a prepared Frappe backup
- return structured runtime metadata to the control plane
- later tear down that runtime through a governed action

This is an internal operator feature.
It is not a generic public provisioning API.

---

## 2. Configuration contract

The adapter is configured outside the DocTypes.

Supported configuration keys:

- `ifitwala_press_founder_runtime_adapter`
- `ifitwala_press_founder_runtime_timeout`

Environment variable fallbacks:

- `IFITWALA_PRESS_FOUNDER_RUNTIME_ADAPTER`
- `IFITWALA_PRESS_FOUNDER_RUNTIME_TIMEOUT`

### Expected adapter command

The adapter command should be an absolute executable or script command.

Examples:

- `/usr/local/bin/ifitwala-founder-runtime-adapter`
- `/home/flipo-frappe/bin/ifitwala-founder-runtime-adapter`
- `bash /home/flipo-frappe/bin/ifitwala-founder-runtime-adapter.sh`

The control plane appends one action argument:

- `provision-demo-runtime`
- `teardown-demo-runtime`

The JSON payload is sent on stdin.

---

## 3. Provision action

### Action name

`provision-demo-runtime`

### Trigger source

- `Create Sandbox` with auto-provision enabled
- `Provision Founder Demo Runtime` from `Tenant Environment` in `Sandbox Provisioning`

### Input payload

The payload contains:

- tenant summary
- environment summary
- site name
- branch intent
- deployment / database intent
- seed mode
- seed reference
- expiry date if present

The adapter may ignore fields it does not need.

### Expected outcome

On success, the adapter should provision the founder runtime and return a JSON object.

Suggested fields:

- `site_name`
- `primary_domain`
- `routing_mode`
- `dns_ready`
- `tls_ready`
- `host_header_value`
- `db_name`
- `db_user`
- `provisioning_job_id`
- `last_provisioning_step`
- `provisioning_message`
- `runtime_reference`
- `backup_export_path`
- `status_reason`

On non-zero exit, the control plane marks provisioning failed.

---

## 4. Teardown action

### Action name

`teardown-demo-runtime`

### Trigger source

- `Teardown Founder Demo Runtime` from `Tenant Environment` in `Sandbox Active`

### Input payload

The payload contains:

- tenant summary
- environment summary
- runtime reference
- backup export path
- teardown reason

### Expected outcome

On success, the adapter should:

- stop and remove the founder runtime for that environment
- preserve or confirm the exported backup path if one exists
- return a JSON object with teardown notes

Suggested fields:

- `last_provisioning_step`
- `provisioning_message`
- `runtime_reference`
- `backup_export_path`

After success, the control plane expires the sandbox through a governed lifecycle action.

---

## 5. Lifecycle ownership

The adapter does not own lifecycle state.

The adapter only performs runtime work and returns structured results.

`Ifitwala_Press` remains responsible for:

- `Sandbox Provisioning`
- `Sandbox Active`
- `Provisioning Failed`
- `Sandbox Expired`
- transition logs
- operator visibility

This keeps the control plane authoritative even in founder mode.

---

## 6. Backup expectation

The adapter must not treat container-local backups as sufficient.

At minimum for founder mode:

- the latest successful site backup must be exported outside the container
- the returned `backup_export_path` must refer to persistent host or off-container storage

This aligns with the phased backup policy already locked in the rollout notes.

---

## 7. Near-term implementation guidance

The first implementation should stay simple:

- same GCE VM
- `frappe_docker` production-style compose patterns
- approved custom app image or app bundle
- synchronous founder-mode execution is acceptable initially
- SSH-free local execution on the host is acceptable initially

Do not jump straight to:

- remote multi-host orchestration
- generic cloud abstraction
- full Agent adoption
- production-grade autoscaling logic

Those are later phases once the founder runtime flow is proven.
