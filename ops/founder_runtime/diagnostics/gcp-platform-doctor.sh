#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${script_dir}/lib.sh"

adapter_env_path="${1:-${ADAPTER_ENV_PATH:-/etc/ifitwala-founder-runtime/adapter.env}}"

has_docker=0
has_gcloud=0
has_curl=0
has_systemctl=0

if require_command docker; then
    has_docker=1
fi
if require_command gcloud; then
    has_gcloud=1
fi
if require_command curl; then
    has_curl=1
fi
require_command jq || true
if require_command systemctl; then
    has_systemctl=1
fi

load_env_file "${adapter_env_path}" || finish_diagnostics

check_directory "${IFITWALA_FOUNDER_RUNTIME_ROOT}"
check_directory "${IFITWALA_FOUNDER_RUNTIME_ROOT}/environments"
check_directory "${IFITWALA_FOUNDER_RUNTIME_EDGE_PROXY_ROOT}"
check_directory "${IFITWALA_FOUNDER_RUNTIME_ROOT}/backup-logs"

if ((has_systemctl)); then
    if systemctl is-active --quiet docker; then
        diag_pass "Docker service is active."
    else
        diag_fail "Docker service is not active."
    fi
else
    diag_fail "Cannot inspect Docker service without systemctl."
fi

if ((has_systemctl)); then
    if systemctl is-active --quiet ifitwala-founder-backup.timer; then
        diag_pass "Founder backup timer is active."
    else
        diag_warn "Founder backup timer is not active."
    fi
fi

if ((has_gcloud)); then
    active_account="$(
        gcloud auth list --filter=status:ACTIVE --format='value(account)' 2>/dev/null | head -n 1
    )"
    if [[ -n "${active_account}" ]]; then
        diag_pass "Active gcloud account: ${active_account}"
    else
        diag_fail "No active gcloud account found."
    fi
fi

if ((has_gcloud)) && [[ -n "${IFITWALA_FOUNDER_RUNTIME_GCLOUD_PROJECT:-}" ]]; then
    if gcloud --project "${IFITWALA_FOUNDER_RUNTIME_GCLOUD_PROJECT}" projects describe \
        "${IFITWALA_FOUNDER_RUNTIME_GCLOUD_PROJECT}" >/dev/null 2>&1; then
        diag_pass "Google Cloud project reachable: ${IFITWALA_FOUNDER_RUNTIME_GCLOUD_PROJECT}"
    else
        diag_fail "Cannot access Google Cloud project: ${IFITWALA_FOUNDER_RUNTIME_GCLOUD_PROJECT}"
    fi
fi

if ((has_gcloud)) && [[ -n "${IFITWALA_FOUNDER_RUNTIME_DNS_ZONE:-}" && -n "${IFITWALA_FOUNDER_RUNTIME_GCLOUD_PROJECT:-}" ]]; then
    if gcloud --project "${IFITWALA_FOUNDER_RUNTIME_GCLOUD_PROJECT}" dns managed-zones describe \
        "${IFITWALA_FOUNDER_RUNTIME_DNS_ZONE}" >/dev/null 2>&1; then
        diag_pass "Cloud DNS zone reachable: ${IFITWALA_FOUNDER_RUNTIME_DNS_ZONE}"
    else
        diag_fail "Cannot access Cloud DNS zone: ${IFITWALA_FOUNDER_RUNTIME_DNS_ZONE}"
    fi
fi

if ((has_curl)); then
    metadata_external_ip="$(
        curl -fsS -H 'Metadata-Flavor: Google' \
            'http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip' \
            2>/dev/null || true
    )"
    if [[ -n "${metadata_external_ip}" ]]; then
        diag_pass "Compute Engine metadata server reachable."
        if [[ -n "${IFITWALA_FOUNDER_RUNTIME_DNS_TARGET_IP:-}" && "${metadata_external_ip}" == "${IFITWALA_FOUNDER_RUNTIME_DNS_TARGET_IP}" ]]; then
            diag_pass "DNS target IP matches current VM external IP."
        elif [[ -n "${IFITWALA_FOUNDER_RUNTIME_DNS_TARGET_IP:-}" ]]; then
            diag_fail "DNS target IP does not match current VM external IP (${metadata_external_ip})."
        fi
    else
        diag_warn "Compute Engine metadata server not reachable from this host."
    fi
fi

if [[ "${IFITWALA_FOUNDER_RUNTIME_IMAGE:-}" == *".pkg.dev/"* ]]; then
    diag_pass "Runtime image points to Artifact Registry."
else
    diag_warn "Runtime image does not look like an Artifact Registry reference."
fi

if ((has_docker)); then
    if docker image inspect "${IFITWALA_FOUNDER_RUNTIME_IMAGE}" >/dev/null 2>&1; then
        diag_pass "Runtime image available locally: ${IFITWALA_FOUNDER_RUNTIME_IMAGE}"
    else
        diag_warn "Runtime image not present locally: ${IFITWALA_FOUNDER_RUNTIME_IMAGE}"
    fi
fi

finish_diagnostics
