# Founder Host Bootstrap

This directory holds the founder GCE VM bootstrap assets for phase 1.

The founder host contract is:

- one Ubuntu 24.04 LTS VM
- Docker Engine with `docker compose`
- `mariadb-client` for DB provisioning
- `gcloud` for Cloud DNS updates
- `gcloud storage` for daily backup export
- systemd-managed daily backup execution

## Files

- `bootstrap-founder-vm.sh`
  Installs the host dependencies and creates the runtime directories
- `install-backup-timer.sh`
  Installs the daily backup service and timer
- `sync-host-firewall.sh`
  Converges the founder VM host firewall with `ufw` and pinned `ufw-docker`
- `systemd/`
  Templates used for the founder backup service and timer

The host-side restore helper lives under `../scripts/restore-site.sh` and is part of the pilot recovery path.

## Expected run order

1. Build and publish the immutable runtime image from `../image/`.
2. Run `sudo ./bootstrap-founder-vm.sh` on the founder VM.
3. Edit `/etc/ifitwala-founder-runtime/adapter.env`.
4. Set `IFITWALA_FOUNDER_RUNTIME_FIREWALL_ENABLED=1` and `IFITWALA_FOUNDER_RUNTIME_ALLOWED_SSH_CIDRS=...` before enabling the host firewall.
5. Authenticate `gcloud` on the founder VM and verify the DNS zone access.
6. Point `IFITWALA_FOUNDER_RUNTIME_IMAGE` at the published image tag.
7. Run one real sandbox provision from `ifitwala_press`.
8. Run the diagnostics in `../diagnostics/` whenever provisioning or runtime issues need fast triage.

The bootstrap script validates that the host is Ubuntu and warns when the detected
release does not match the current approved founder baseline of `24.04`.
