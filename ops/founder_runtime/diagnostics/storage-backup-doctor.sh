#!/usr/bin/env bash
set -euo pipefail

site_ref="${1:?site name or runtime directory required}"
adapter_env_path="${2:-${ADAPTER_ENV_PATH:-/etc/ifitwala-founder-runtime/adapter.env}}"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${script_dir}/lib.sh"

has_gcloud=0
has_systemctl=0

if require_command gcloud; then
    has_gcloud=1
fi
require_command jq || true
require_command grep || true
if require_command systemctl; then
    has_systemctl=1
fi

load_env_file "${adapter_env_path}" || finish_diagnostics

runtime_dir="$(resolve_runtime_dir "${IFITWALA_FOUNDER_RUNTIME_ROOT}" "${site_ref}" || true)"
if [[ -z "${runtime_dir}" ]]; then
    diag_fail "Runtime directory not found for: ${site_ref}"
    finish_diagnostics
fi

check_file "${runtime_dir}/.env"
check_file "${runtime_dir}/runtime-config/runtime-plan.json"

set -a
# shellcheck disable=SC1090
source "${runtime_dir}/.env"
set +a

site_bucket_uri="gs://${GCS_FILES_BUCKET}"
backup_bucket_uri="gs://${GCS_BACKUPS_BUCKET}"
files_prefix_uri="${site_bucket_uri}/${GCS_FILES_PREFIX}"
backups_prefix_uri="${backup_bucket_uri}/${GCS_BACKUPS_PREFIX}"

if ((has_gcloud)); then
    if gcloud storage ls "${site_bucket_uri}" >/dev/null 2>&1; then
        diag_pass "Cloud Storage files bucket reachable: ${site_bucket_uri}"
    else
        diag_fail "Cloud Storage files bucket not reachable: ${site_bucket_uri}"
    fi

    if gcloud storage ls "${backup_bucket_uri}" >/dev/null 2>&1; then
        diag_pass "Cloud Storage backups bucket reachable: ${backup_bucket_uri}"
    else
        diag_fail "Cloud Storage backups bucket not reachable: ${backup_bucket_uri}"
    fi

    if gcloud storage ls --recursive "${files_prefix_uri}" >/dev/null 2>&1; then
        diag_pass "Files prefix reachable: ${files_prefix_uri}"
    else
        diag_warn "Files prefix has no visible objects yet: ${files_prefix_uri}"
    fi

    latest_remote_backup="$(
        gcloud storage ls --recursive "${backups_prefix_uri}" 2>/dev/null | tail -n 1 || true
    )"
    if [[ -n "${latest_remote_backup}" ]]; then
        diag_pass "Latest remote backup object: ${latest_remote_backup}"
    else
        diag_warn "No remote backup object found under: ${backups_prefix_uri}"
    fi
fi

latest_manifest="$(
    ls -1t "${IFITWALA_FOUNDER_RUNTIME_ROOT}/backup-logs/"*.tsv 2>/dev/null | head -n 1 || true
)"
if [[ -n "${latest_manifest}" ]]; then
    if grep -Fq "${SITE_NAME}" "${latest_manifest}"; then
        diag_pass "Latest backup manifest contains site entry: ${latest_manifest}"
    else
        diag_warn "Latest backup manifest does not mention ${SITE_NAME}: ${latest_manifest}"
    fi
else
    diag_warn "No local backup manifest found under ${IFITWALA_FOUNDER_RUNTIME_ROOT}/backup-logs"
fi

latest_local_backup="$(
    ls -1t "${runtime_dir}/sites/${SITE_NAME}/private/backups/"*.tgz 2>/dev/null | head -n 1 || true
)"
if [[ -n "${latest_local_backup}" ]]; then
    diag_pass "Latest local backup archive: ${latest_local_backup}"
else
    diag_warn "No local backup archive found for ${SITE_NAME}"
fi

if ((has_systemctl)); then
    if systemctl is-active --quiet ifitwala-founder-backup.timer; then
        diag_pass "Founder backup timer is active."
    else
        diag_fail "Founder backup timer is not active."
    fi
fi

finish_diagnostics
