#!/usr/bin/env bash
set -euo pipefail

pool_dir="${1:?pool directory required}"
site_name="${2:?site name required}"
backup_export_path="${3:-}"

set -a
source "${pool_dir}/.env"
set +a

site_slug="$(printf '%s' "${site_name}" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//')"
manifest_dir="${pool_dir}/runtime-config/sites"
site_manifest="${manifest_dir}/${site_slug}.json"
restore_dir="${pool_dir}/runtime-config/restore/${site_slug}"

if [[ ! -f "${site_manifest}" ]]; then
    printf '%s\n' "Site manifest not found for ${site_name}: ${site_manifest}" >&2
    exit 1
fi

if [[ -z "${backup_export_path}" ]]; then
    backup_export_path="$(jq -r '.backup_export_path // empty' "${site_manifest}")"
fi

if [[ -z "${backup_export_path}" ]]; then
    printf '%s\n' "Backup export path is required to restore ${site_name}." >&2
    exit 1
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

db_name="$(jq -r '.db_name' "${site_manifest}")"
db_user="$(jq -r '.db_user' "${site_manifest}")"
db_password="$(jq -r '.db_password' "${site_manifest}")"
site_domain="$(jq -r '.primary_domain // empty' "${site_manifest}")"
files_prefix="$(jq -r '.files_prefix // empty' "${site_manifest}")"
backups_prefix="$(jq -r '.backups_prefix // empty' "${site_manifest}")"
file_storage_provider="$(jq -r '.file_storage_provider // empty' "${site_manifest}")"
file_storage_class="$(jq -r '.file_storage_class // empty' "${site_manifest}")"
backup_storage_provider="$(jq -r '.backup_storage_provider // empty' "${site_manifest}")"
backup_storage_class="$(jq -r '.backup_storage_class // empty' "${site_manifest}")"

docker compose -f "${pool_dir}/compose.yaml" --project-directory "${pool_dir}" up -d
docker compose -f "${pool_dir}/compose.yaml" --project-directory "${pool_dir}" \
    exec -T \
    -e SITE_NAME="${site_name}" \
    -e DB_HOST="${DB_HOST}" \
    -e DB_PORT="${DB_PORT}" \
    -e DB_NAME="${db_name}" \
    -e DB_USER="${db_user}" \
    -e DB_PASSWORD="${db_password}" \
    -e DB_ROOT_USER="${DB_ROOT_USER}" \
    -e DB_ROOT_PASSWORD="${DB_ROOT_PASSWORD}" \
    -e ADMIN_PASSWORD="${ADMIN_PASSWORD}" \
    -e SITE_DOMAIN="${site_domain}" \
    -e FILE_STORAGE_PROVIDER="${file_storage_provider}" \
    -e FILE_STORAGE_CLASS="${file_storage_class}" \
    -e BACKUP_STORAGE_PROVIDER="${backup_storage_provider}" \
    -e BACKUP_STORAGE_CLASS="${backup_storage_class}" \
    -e GCS_PROJECT="${GCS_PROJECT:-}" \
    -e GCS_FILES_BUCKET="${GCS_FILES_BUCKET}" \
    -e GCS_FILES_PREFIX="${files_prefix}" \
    -e GCS_BACKUPS_BUCKET="${GCS_BACKUPS_BUCKET}" \
    -e GCS_BACKUPS_PREFIX="${backups_prefix}" \
    backend /bin/bash /workspace/shared_demo_bench/scripts/provision-site.sh

docker compose -f "${pool_dir}/compose.yaml" --project-directory "${pool_dir}" \
    exec -T backend \
    bench --site "${site_name}" --force restore "/workspace/runtime-config/restore/${site_slug}/$(basename "${database_local_path}")" \
    --db-root-username "${DB_ROOT_USER}" \
    --db-root-password "${DB_ROOT_PASSWORD}" \
    --with-public-files "/workspace/runtime-config/restore/${site_slug}/$(basename "${public_files_local_path}")" \
    --with-private-files "/workspace/runtime-config/restore/${site_slug}/$(basename "${private_files_local_path}")"

docker compose -f "${pool_dir}/compose.yaml" --project-directory "${pool_dir}" \
    exec -T backend bench --site "${site_name}" migrate

printf '%s\n' "${manifest_uri}"
