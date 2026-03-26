# Founder Host Bootstrap

This directory holds the founder GCE VM bootstrap assets for phase 1.

The founder host contract is:

- one Debian or Ubuntu VM
- Docker Engine with `docker compose`
- `mariadb-client` for DB provisioning
- `gcloud` for Cloud DNS updates
- `aws` CLI or equivalent S3 tooling for daily backup export
- systemd-managed daily backup execution

## Files

- `bootstrap-founder-vm.sh`
  Installs the host dependencies and creates the runtime directories
- `install-backup-timer.sh`
  Installs the daily backup service and timer
- `systemd/`
  Templates used for the founder backup service and timer

## Expected run order

1. Build and publish the immutable runtime image from `../image/`.
2. Run `sudo ./bootstrap-founder-vm.sh` on the founder VM.
3. Edit `/etc/ifitwala-founder-runtime/adapter.env`.
4. Authenticate `gcloud` on the founder VM and verify the DNS zone access.
5. Point `IFITWALA_FOUNDER_RUNTIME_IMAGE` at the published image tag.
6. Run one real sandbox provision from `ifitwala_press`.
