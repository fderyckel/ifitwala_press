#!/usr/bin/env bash
set -euo pipefail

site_ref="${1:?site name or runtime directory required}"
adapter_env_path="${2:-${ADAPTER_ENV_PATH:-/etc/ifitwala-founder-runtime/adapter.env}}"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${script_dir}/lib.sh"

has_docker=0
has_jq=0
has_curl=0
has_mysql=0
has_systemctl=0

if require_command docker; then
    has_docker=1
fi
if require_command jq; then
    has_jq=1
fi
if require_command curl; then
    has_curl=1
fi
if require_command mysql; then
    has_mysql=1
fi
if require_command systemctl; then
    has_systemctl=1
fi

load_env_file "${adapter_env_path}" || finish_diagnostics

runtime_dir="$(resolve_runtime_dir "${IFITWALA_FOUNDER_RUNTIME_ROOT}" "${site_ref}" || true)"
if [[ -z "${runtime_dir}" ]]; then
    diag_fail "Runtime directory not found for: ${site_ref}"
    finish_diagnostics
fi

check_directory "${runtime_dir}"
check_file "${runtime_dir}/compose.yaml"
check_file "${runtime_dir}/.env"
check_file "${runtime_dir}/runtime-config/runtime-plan.json"
check_file "${runtime_dir}/sites/common_site_config.json"

set -a
# shellcheck disable=SC1090
source "${runtime_dir}/.env"
set +a

expected_services=(
    backend
    worker
    scheduler
    nginx
    redis-cache
    redis-queue
    redis-socketio
)

if ((has_docker)); then
    running_services="$(
        docker compose -f "${runtime_dir}/compose.yaml" --project-directory "${runtime_dir}" \
            ps --services --status running 2>/dev/null || true
    )"

    if [[ -z "${running_services}" ]]; then
        diag_fail "No running services reported by docker compose."
    else
        for service_name in "${expected_services[@]}"; do
            if grep -Fxq "${service_name}" <<<"${running_services}"; then
                diag_pass "Service running: ${service_name}"
            else
                diag_fail "Service not running: ${service_name}"
            fi
        done
    fi
fi

if ((has_docker)); then
    apps_output="$(
        docker compose -f "${runtime_dir}/compose.yaml" --project-directory "${runtime_dir}" \
            exec -T backend bench --site "${SITE_NAME}" list-apps 2>/dev/null || true
    )"
    if grep -Fxq "ifitwala_ed" <<<"${apps_output}"; then
        diag_pass "App installed: ifitwala_ed"
    else
        diag_fail "App missing from site: ifitwala_ed"
    fi

    if grep -Fxq "ifitwala_drive" <<<"${apps_output}"; then
        diag_pass "App installed: ifitwala_drive"
    else
        diag_fail "App missing from site: ifitwala_drive"
    fi
fi

if ((has_mysql)); then
    db_ping_output="$(
        MYSQL_PWD="${DB_PASSWORD}" mysql \
            --host "${DB_HOST}" \
            --port "${DB_PORT}" \
            --user "${DB_USER}" \
            --database "${DB_NAME}" \
            --batch \
            --skip-column-names \
            --execute 'select 1' 2>/dev/null || true
    )"
    if [[ "${db_ping_output}" == "1" ]]; then
        diag_pass "Database connectivity succeeded for ${DB_NAME}."
    else
        diag_fail "Database connectivity failed for ${DB_NAME}."
    fi
fi

if ((has_curl)); then
    primary_domain=""
    if ((has_jq)); then
        primary_domain="$(jq -r '.primary_domain // empty' "${runtime_dir}/runtime-config/runtime-plan.json")"
    fi
    curl_args=(
        --silent
        --show-error
        --max-time 10
        --output /dev/null
        --write-out '%{http_code}'
    )
    if [[ -n "${primary_domain}" ]]; then
        curl_args+=(-H "Host: ${primary_domain}")
    fi
    http_status="$(
        curl "${curl_args[@]}" "http://127.0.0.1:${HTTP_PORT}/" 2>/dev/null || true
    )"
    case "${http_status}" in
        200|301|302|307|308)
            diag_pass "Local HTTP response healthy on port ${HTTP_PORT} (${http_status})."
            ;;
        "")
            diag_fail "No local HTTP response from nginx on port ${HTTP_PORT}."
            ;;
        *)
            diag_fail "Unexpected local HTTP status on port ${HTTP_PORT}: ${http_status}"
            ;;
    esac
fi

if ((has_systemctl)); then
    if systemctl is-active --quiet ifitwala-founder-backup.timer; then
        diag_pass "Founder backup timer is active."
    else
        diag_warn "Founder backup timer is not active."
    fi
fi

finish_diagnostics
