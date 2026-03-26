#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
    printf '%s\n' "Run this script as root." >&2
    exit 1
fi

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ops_root="$(cd "${script_dir}/.." && pwd)"

install_root="${INSTALL_ROOT:-/usr/local/lib/ifitwala-founder-runtime}"
adapter_env_path="${ADAPTER_ENV_PATH:-/etc/ifitwala-founder-runtime/adapter.env}"
backup_on_calendar="${BACKUP_ON_CALENDAR:-*-*-* 02:15:00}"

install -d -m 0755 "${install_root}"
install -m 0755 "${ops_root}/scripts/backup-site.sh" "${install_root}/backup-site.sh"
install -m 0755 "${ops_root}/scripts/backup-all-sites.sh" "${install_root}/backup-all-sites.sh"

sed \
    -e "s|__INSTALL_ROOT__|${install_root}|g" \
    -e "s|__ADAPTER_ENV_PATH__|${adapter_env_path}|g" \
    "${script_dir}/systemd/ifitwala-founder-backup.service.template" \
    >/etc/systemd/system/ifitwala-founder-backup.service

sed \
    -e "s|__ON_CALENDAR__|${backup_on_calendar}|g" \
    "${script_dir}/systemd/ifitwala-founder-backup.timer.template" \
    >/etc/systemd/system/ifitwala-founder-backup.timer

systemctl daemon-reload
systemctl enable --now ifitwala-founder-backup.timer
