#!/usr/bin/env bash
set -euo pipefail

UFW_DOCKER_URL="https://raw.githubusercontent.com/chaifeng/ufw-docker/2b419bbdde946a4fd1a8651940ad95b6b0b96dfa/ufw-docker"
UFW_DOCKER_CHECKSUM="16bc578c0cd78b7d44c53e5780c0d3d545860e428457a8910a3d2138fb225374"
UFW_DOCKER_BIN="/usr/local/bin/ufw-docker"

if [[ "${EUID}" -ne 0 ]]; then
    printf '%s\n' "Run this script as root." >&2
    exit 1
fi

if [[ "$#" -gt 1 ]]; then
    printf '%s\n' "Usage: sync-host-firewall.sh [adapter-env-path]" >&2
    exit 2
fi

if [[ "$#" -eq 1 ]]; then
    env_path="${1}"
    if [[ ! -f "${env_path}" ]]; then
        printf '%s\n' "Adapter env file not found: ${env_path}" >&2
        exit 1
    fi
    set -a
    # shellcheck disable=SC1090
    source "${env_path}"
    set +a
fi

enabled="${IFITWALA_FOUNDER_RUNTIME_FIREWALL_ENABLED:-0}"
ssh_cidrs_raw="${IFITWALA_FOUNDER_RUNTIME_ALLOWED_SSH_CIDRS:-}"
public_tcp_ports_raw="${IFITWALA_FOUNDER_RUNTIME_PUBLIC_TCP_PORTS:-80,443}"

trim() {
    local value="${1:-}"
    value="${value#"${value%%[![:space:]]*}"}"
    value="${value%"${value##*[![:space:]]}"}"
    printf '%s' "${value}"
}

split_csv() {
    local raw="${1:-}"
    raw="${raw//$'\n'/,}"
    raw="${raw//;/,}"
    raw="${raw// /,}"
    local item
    IFS=',' read -r -a values <<<"${raw}"
    for item in "${values[@]}"; do
        item="$(trim "${item}")"
        if [[ -n "${item}" ]]; then
            printf '%s\n' "${item}"
        fi
    done
}

ensure_ufw() {
    if command -v ufw >/dev/null 2>&1; then
        return
    fi

    apt-get update
    DEBIAN_FRONTEND=noninteractive apt-get install --yes --no-install-recommends ufw
}

ensure_ufw_docker() {
    if [[ -x "${UFW_DOCKER_BIN}" ]]; then
        return
    fi

    install -d -m 0755 "$(dirname "${UFW_DOCKER_BIN}")"
    curl -fsSL "${UFW_DOCKER_URL}" -o "${UFW_DOCKER_BIN}"
    printf '%s  %s\n' "${UFW_DOCKER_CHECKSUM}" "${UFW_DOCKER_BIN}" | sha256sum --check --status
    chmod 0755 "${UFW_DOCKER_BIN}"
}

configure_disabled_firewall() {
    ufw --force reset >/dev/null
    ufw default allow incoming >/dev/null
    ufw default allow outgoing >/dev/null
    ufw disable >/dev/null || true
    printf '%s\n' "Founder host firewall disabled."
}

configure_enabled_firewall() {
    local -a ssh_cidrs=()
    local -a public_tcp_ports=()
    local cidr
    local port

    while IFS= read -r cidr; do
        ssh_cidrs+=("${cidr}")
    done < <(split_csv "${ssh_cidrs_raw}")

    while IFS= read -r port; do
        public_tcp_ports+=("${port}")
    done < <(split_csv "${public_tcp_ports_raw}")

    if [[ "${#ssh_cidrs[@]}" -eq 0 ]]; then
        printf '%s\n' "IFITWALA_FOUNDER_RUNTIME_ALLOWED_SSH_CIDRS is required when the founder firewall is enabled." >&2
        exit 1
    fi

    if [[ "${#public_tcp_ports[@]}" -eq 0 ]]; then
        printf '%s\n' "IFITWALA_FOUNDER_RUNTIME_PUBLIC_TCP_PORTS must contain at least one TCP port when the founder firewall is enabled." >&2
        exit 1
    fi

    ufw --force reset >/dev/null
    ufw default deny incoming >/dev/null
    ufw default allow outgoing >/dev/null

    for port in "${public_tcp_ports[@]}"; do
        ufw allow "${port}/tcp" >/dev/null
    done

    for cidr in "${ssh_cidrs[@]}"; do
        ufw allow from "${cidr}" to any port 22 proto tcp >/dev/null
    done

    ufw --force enable >/dev/null
    "${UFW_DOCKER_BIN}" install >/dev/null
    "${UFW_DOCKER_BIN}" install-service --force >/dev/null

    printf '%s\n' "Founder host firewall enabled."
}

ensure_ufw
ensure_ufw_docker

if [[ "${enabled}" == "1" ]]; then
    configure_enabled_firewall
else
    configure_disabled_firewall
fi
