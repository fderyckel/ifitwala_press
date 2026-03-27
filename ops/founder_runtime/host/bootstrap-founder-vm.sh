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
operator_user="${FOUNDER_OPERATOR_USER:-${SUDO_USER:-}}"
runtime_root_default="${IFITWALA_FOUNDER_RUNTIME_ROOT:-/srv/ifitwala-founder-runtime}"

check_supported_host() {
    if [[ ! -r /etc/os-release ]]; then
        printf '%s\n' "Unable to read /etc/os-release. Founder host bootstrap expects Ubuntu Minimal 25.04." >&2
        exit 1
    fi

    # shellcheck disable=SC1091
    source /etc/os-release

    if [[ "${ID:-}" != "ubuntu" ]]; then
        printf '%s\n' "Founder host bootstrap currently supports Ubuntu Minimal 25.04. Detected ${PRETTY_NAME:-unknown}." >&2
        exit 1
    fi

    if [[ "${VERSION_ID:-}" != "25.04" ]]; then
        printf '%s\n' "Warning: approved founder host baseline is Ubuntu Minimal 25.04. Detected Ubuntu ${VERSION_ID:-unknown}." >&2
    fi
}

install_base_packages() {
    apt-get update
    DEBIAN_FRONTEND=noninteractive apt-get install --yes --no-install-recommends \
        awscli \
        ca-certificates \
        curl \
        docker.io \
        gnupg \
        jq \
        mariadb-client \
        unzip

    if ! docker compose version >/dev/null 2>&1; then
        DEBIAN_FRONTEND=noninteractive apt-get install --yes --no-install-recommends docker-compose-plugin \
            || DEBIAN_FRONTEND=noninteractive apt-get install --yes --no-install-recommends docker-compose-v2
    fi

    docker compose version >/dev/null 2>&1 || {
        printf '%s\n' "docker compose is required on the founder host." >&2
        exit 1
    }
}

install_gcloud() {
    if command -v gcloud >/dev/null 2>&1; then
        return
    fi

    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg \
        | gpg --dearmor -o /etc/apt/keyrings/google-cloud.gpg
    chmod a+r /etc/apt/keyrings/google-cloud.gpg

    cat >/etc/apt/sources.list.d/google-cloud-cli.list <<'EOF'
deb [signed-by=/etc/apt/keyrings/google-cloud.gpg] https://packages.cloud.google.com/apt cloud-sdk main
EOF

    apt-get update
    DEBIAN_FRONTEND=noninteractive apt-get install --yes --no-install-recommends google-cloud-cli \
        || DEBIAN_FRONTEND=noninteractive apt-get install --yes --no-install-recommends google-cloud-sdk
}

install_adapter_env() {
    install -d -m 0750 "$(dirname "${adapter_env_path}")"
    if [[ ! -f "${adapter_env_path}" ]]; then
        install -m 0600 "${ops_root}/adapter.env.example" "${adapter_env_path}"
    fi
}

load_runtime_root() {
    local runtime_root="${runtime_root_default}"

    if [[ -f "${adapter_env_path}" ]]; then
        set -a
        # shellcheck disable=SC1090
        source "${adapter_env_path}"
        set +a
        runtime_root="${IFITWALA_FOUNDER_RUNTIME_ROOT:-${runtime_root}}"
    fi

    printf '%s' "${runtime_root}"
}

ensure_runtime_dirs() {
    local runtime_root="${1}"
    install -d -m 0755 "${runtime_root}"
    install -d -m 0755 "${runtime_root}/environments"
    install -d -m 0755 "${runtime_root}/edge-proxy"
    install -d -m 0755 "${runtime_root}/backup-logs"
}

enable_docker() {
    systemctl enable --now docker

    if [[ -n "${operator_user}" ]] && id "${operator_user}" >/dev/null 2>&1; then
        usermod -aG docker "${operator_user}"
    fi
}

install_diagnostics() {
    install -d -m 0755 "${install_root}/diagnostics"
    install -m 0755 "${ops_root}/diagnostics/gcp-platform-doctor.sh" "${install_root}/diagnostics/gcp-platform-doctor.sh"
    install -m 0755 "${ops_root}/diagnostics/founder-runtime-doctor.sh" "${install_root}/diagnostics/founder-runtime-doctor.sh"
    install -m 0755 "${ops_root}/diagnostics/storage-backup-doctor.sh" "${install_root}/diagnostics/storage-backup-doctor.sh"
    install -m 0644 "${ops_root}/diagnostics/lib.sh" "${install_root}/diagnostics/lib.sh"
}

install_backup_timer() {
    INSTALL_ROOT="${install_root}" \
    ADAPTER_ENV_PATH="${adapter_env_path}" \
        "${script_dir}/install-backup-timer.sh"
}

print_next_steps() {
    local runtime_root="${1}"

    printf '%s\n' "Founder runtime host bootstrap complete."
    printf '%s\n' "Runtime root: ${runtime_root}"
    printf '%s\n' "Adapter env: ${adapter_env_path}"
    printf '%s\n' "Next steps:"
    printf '%s\n' "1. Edit ${adapter_env_path} and pin IFITWALA_FOUNDER_RUNTIME_IMAGE to the published runtime image tag."
    printf '%s\n' "2. Authenticate gcloud on this host and confirm access to the configured Cloud DNS zone."
    printf '%s\n' "3. Restart the control-plane process with the adapter env loaded."
    printf '%s\n' "4. Run /usr/local/lib/ifitwala-founder-runtime/diagnostics/gcp-platform-doctor.sh ${adapter_env_path}."
    printf '%s\n' "5. Run one sandbox provision from Ifitwala_Press and verify DNS, shared edge proxy routing, and Cloud-Storage-backed file writes."

    if [[ -n "${operator_user}" ]] && id "${operator_user}" >/dev/null 2>&1; then
        printf '%s\n' "User ${operator_user} was added to the docker group. A new login session is required before docker commands work without sudo."
    fi
}

check_supported_host
install_base_packages
install_gcloud
install_adapter_env
runtime_root="$(load_runtime_root)"
ensure_runtime_dirs "${runtime_root}"
enable_docker
install_diagnostics
install_backup_timer
print_next_steps "${runtime_root}"
