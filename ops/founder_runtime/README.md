# Founder Runtime

This directory holds the founder-mode runtime scaffolding for phase 1 / MVP.

The intended operating model is:

- `ifitwala_press` remains the control plane
- one same-VM Docker Compose stack is rendered per tenant environment
- the runtime image already contains `frappe`, `ifitwala_ed`, and `ifitwala_drive`
- MariaDB remains an explicit external dependency
- Redis stays local to the compose stack for founder mode
- GCS storage is injected through runtime configuration, not DocTypes
- Cloud DNS record changes are handled through `gcloud dns ...`
- a shared founder edge proxy can route hostnames to each environment's loopback nginx port
- the shared founder edge proxy can enforce per-environment ingress posture as `Public`, `Allowlisted`, or `Disabled`
- the founder host can converge a repo-managed `ufw` + `ufw-docker` firewall baseline
- the founder host installs a daily backup timer that exports every active environment to the backup tier

## Files

- `adapter.py`
  Founder-mode adapter executable expected by `ifitwala_press`
- `adapter.env.example`
  Required environment contract for the adapter host
- `image/`
  Immutable runtime image build context for `frappe` + `ifitwala_ed` + `ifitwala_drive`
- `host/`
  Founder GCE VM bootstrap, host firewall sync, and daily backup timer installation assets
- `diagnostics/`
  Google-Cloud-focused incident and health checks for the founder runtime
- `templates/compose.yaml`
  Same-VM Docker Compose layout for one tenant runtime
- `templates/nginx-default.conf`
  Per-environment nginx config bound to a loopback host port
- `scripts/init-site.sh`
  Container-side site bootstrap
- `scripts/run-backend.sh`
  Founder-mode backend process
- `scripts/run-worker.sh`
  Founder-mode worker process
- `scripts/run-scheduler.sh`
  Founder-mode scheduler process
- `scripts/backup-site.sh`
  Host-side daily backup export helper
- `scripts/restore-site.sh`
  Host-side restore helper that rehydrates one site from the exported backup manifest

## Important boundary

This scaffolding assumes:

- the founder runtime host currently uses Ubuntu 24.04 LTS
- Docker Compose runs on the founder runtime host
- `gcloud` is available on that host for Cloud DNS changes
- `gcloud storage` is available on that host for backup export
- the shared founder edge proxy in `edge_proxy/` or a later Traefik layer will route hostnames to the per-environment loopback nginx ports

This current per-environment founder stack is acceptable for small pilot cohorts only.
It is not the default architecture for a larger founder-managed demo cohort.

The adapter can now render and manage both DNS records and shared founder proxy routes.
The host bootstrap assets can now prepare the VM for Docker, Cloud DNS, and daily backup execution.
This still does not replace the later Traefik target.
