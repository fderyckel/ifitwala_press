#!/usr/bin/env bash
set -euo pipefail

DIAG_FAILURES=0
DIAG_WARNINGS=0

diag_pass() {
    printf '%s\n' "[PASS] $*"
}

diag_warn() {
    printf '%s\n' "[WARN] $*"
    DIAG_WARNINGS=$((DIAG_WARNINGS + 1))
}

diag_fail() {
    printf '%s\n' "[FAIL] $*"
    DIAG_FAILURES=$((DIAG_FAILURES + 1))
}

require_command() {
    local command_name="${1:?command name required}"
    if command -v "${command_name}" >/dev/null 2>&1; then
        diag_pass "Command available: ${command_name}"
        return 0
    fi

    diag_fail "Missing command: ${command_name}"
    return 1
}

load_env_file() {
    local env_path="${1:?env path required}"
    if [[ ! -f "${env_path}" ]]; then
        diag_fail "Env file not found: ${env_path}"
        return 1
    fi

    set -a
    # shellcheck disable=SC1090
    source "${env_path}"
    set +a
    diag_pass "Loaded env file: ${env_path}"
}

resolve_runtime_dir() {
    local runtime_root="${1:?runtime root required}"
    local site_ref="${2:?site reference required}"

    if [[ -d "${site_ref}" ]]; then
        printf '%s' "${site_ref}"
        return 0
    fi

    if [[ -d "${runtime_root}/environments/${site_ref}" ]]; then
        printf '%s' "${runtime_root}/environments/${site_ref}"
        return 0
    fi

    return 1
}

check_file() {
    local file_path="${1:?file path required}"
    if [[ -f "${file_path}" ]]; then
        diag_pass "File present: ${file_path}"
    else
        diag_fail "Missing file: ${file_path}"
    fi
}

check_directory() {
    local dir_path="${1:?directory path required}"
    if [[ -d "${dir_path}" ]]; then
        diag_pass "Directory present: ${dir_path}"
    else
        diag_fail "Missing directory: ${dir_path}"
    fi
}

finish_diagnostics() {
    printf '%s\n' "[SUMMARY] ${DIAG_FAILURES} failure(s), ${DIAG_WARNINGS} warning(s)"
    if ((DIAG_FAILURES > 0)); then
        exit 1
    fi
}
