#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
runtime_root="${IFITWALA_FOUNDER_RUNTIME_ROOT:-}"

if [[ -z "${runtime_root}" ]]; then
    printf '%s\n' "IFITWALA_FOUNDER_RUNTIME_ROOT is required." >&2
    exit 1
fi

environments_dir="${runtime_root}/environments"
manifest_dir="${runtime_root}/backup-logs"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
manifest_path="${manifest_dir}/${timestamp}.tsv"

mkdir -p "${manifest_dir}"

shopt -s nullglob
runtime_dirs=("${environments_dir}"/*)
failures=0

for runtime_dir in "${runtime_dirs[@]}"; do
    [[ -f "${runtime_dir}/compose.yaml" ]] || continue
    [[ -f "${runtime_dir}/.env" ]] || continue

    runtime_name="$(basename "${runtime_dir}")"

    if backup_target="$("${script_dir}/backup-site.sh" "${runtime_dir}")"; then
        printf '%s\tok\t%s\n' "${runtime_name}" "${backup_target}" | tee -a "${manifest_path}"
        continue
    fi

    printf '%s\tfailed\t-\n' "${runtime_name}" | tee -a "${manifest_path}" >&2
    failures=$((failures + 1))
done

printf '%s\n' "${manifest_path}"

if ((failures > 0)); then
    exit 1
fi
