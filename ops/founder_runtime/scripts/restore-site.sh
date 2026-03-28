#!/usr/bin/env bash
set -euo pipefail

runtime_dir="${1:?runtime directory required}"
backup_export_path="${2:-}"
restore_dir="${runtime_dir}/runtime-config/restore"

set -a
source "${runtime_dir}/.env"
set +a

if [[ -z "${backup_export_path}" ]]; then
    backup_export_path="gs://${GCS_BACKUPS_BUCKET}/${GCS_BACKUPS_PREFIX}"
fi

mkdir -p "${restore_dir}"
rm -f "${restore_dir}"/*

manifest_uri="${backup_export_path%/}/manifest-latest.json"
manifest_path="${restore_dir}/manifest-latest.json"
gcloud storage cp "${manifest_uri}" "${manifest_path}"

database_object_uri="$(jq -r '.database.object_uri // empty' "${manifest_path}")"
public_files_object_uri="$(jq -r '.public_files.object_uri // empty' "${manifest_path}")"
private_files_object_uri="$(jq -r '.private_files.object_uri // empty' "${manifest_path}")"

if [[ -z "${database_object_uri}" || -z "${public_files_object_uri}" || -z "${private_files_object_uri}" ]]; then
    printf '%s\n' "Restore manifest is missing one or more backup object URIs." >&2
    exit 1
fi

database_local_path="${restore_dir}/$(basename "${database_object_uri}")"
public_files_local_path="${restore_dir}/$(basename "${public_files_object_uri}")"
private_files_local_path="${restore_dir}/$(basename "${private_files_object_uri}")"

gcloud storage cp "${database_object_uri}" "${database_local_path}"
gcloud storage cp "${public_files_object_uri}" "${public_files_local_path}"
gcloud storage cp "${private_files_object_uri}" "${private_files_local_path}"

docker compose -f "${runtime_dir}/compose.yaml" --project-directory "${runtime_dir}" up -d
docker compose -f "${runtime_dir}/compose.yaml" --project-directory "${runtime_dir}" \
    exec -T backend /bin/bash /workspace/founder_runtime/scripts/init-site.sh

docker compose -f "${runtime_dir}/compose.yaml" --project-directory "${runtime_dir}" \
    exec -T backend \
    bench --site "${SITE_NAME}" --force restore "/workspace/runtime-config/restore/$(basename "${database_local_path}")" \
    --db-root-username "${DB_ROOT_USER}" \
    --db-root-password "${DB_ROOT_PASSWORD}" \
    --with-public-files "/workspace/runtime-config/restore/$(basename "${public_files_local_path}")" \
    --with-private-files "/workspace/runtime-config/restore/$(basename "${private_files_local_path}")"

docker compose -f "${runtime_dir}/compose.yaml" --project-directory "${runtime_dir}" \
    exec -T backend bench --site "${SITE_NAME}" migrate

if [[ -n "${SITE_DOMAIN:-}" ]]; then
    docker compose -f "${runtime_dir}/compose.yaml" --project-directory "${runtime_dir}" \
        exec -T backend bench --site "${SITE_NAME}" set-config host_name "https://${SITE_DOMAIN}"
fi

printf '%s\n' "${manifest_uri}"
