#!/usr/bin/env bash
set -euo pipefail

runtime_dir="${1:?runtime directory required}"

set -a
source "${runtime_dir}/.env"
set +a

docker compose -f "${runtime_dir}/compose.yaml" --project-directory "${runtime_dir}" \
    exec -T backend bench --site "${SITE_NAME}" backup --with-files --compress

backup_dir="${runtime_dir}/sites/${SITE_NAME}/private/backups"
db_backup="$(find "${backup_dir}" -maxdepth 1 -type f \( -name "*-database.sql.gz" -o -name "*-database.sql" \) -print0 | xargs -0 -r ls -1t | head -n 1)"
if [[ -z "${db_backup}" ]]; then
    printf '%s\n' "No database backup found for ${SITE_NAME} in ${backup_dir}." >&2
    exit 1
fi

db_backup_name="$(basename "${db_backup}")"
backup_stem="${db_backup_name%-database.sql.gz}"
if [[ "${backup_stem}" == "${db_backup_name}" ]]; then
    backup_stem="${db_backup_name%-database.sql}"
fi

public_files_backup=""
for candidate in \
    "${backup_dir}/${backup_stem}-files.tgz" \
    "${backup_dir}/${backup_stem}-files.tar"
do
    if [[ -f "${candidate}" ]]; then
        public_files_backup="${candidate}"
        break
    fi
done

private_files_backup=""
for candidate in \
    "${backup_dir}/${backup_stem}-private-files.tgz" \
    "${backup_dir}/${backup_stem}-private-files.tar"
do
    if [[ -f "${candidate}" ]]; then
        private_files_backup="${candidate}"
        break
    fi
done

if [[ -z "${public_files_backup}" || -z "${private_files_backup}" ]]; then
    printf '%s\n' "Expected public and private file backups for ${SITE_NAME} under ${backup_dir}." >&2
    exit 1
fi

backup_prefix="gs://${GCS_BACKUPS_BUCKET}/${GCS_BACKUPS_PREFIX}"
exported_on="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

gcloud storage cp "${db_backup}" "${backup_prefix}"
gcloud storage cp "${public_files_backup}" "${backup_prefix}"
gcloud storage cp "${private_files_backup}" "${backup_prefix}"

db_object_uri="${backup_prefix}$(basename "${db_backup}")"
public_object_uri="${backup_prefix}$(basename "${public_files_backup}")"
private_object_uri="${backup_prefix}$(basename "${private_files_backup}")"
manifest_path="$(mktemp "/tmp/ifitwala-backup-manifest.XXXXXX.json")"
jq -n \
    --arg site_name "${SITE_NAME}" \
    --arg exported_on "${exported_on}" \
    --arg backup_export_path "${backup_prefix}" \
    --arg db_filename "$(basename "${db_backup}")" \
    --arg db_object_uri "${db_object_uri}" \
    --arg public_filename "$(basename "${public_files_backup}")" \
    --arg public_object_uri "${public_object_uri}" \
    --arg private_filename "$(basename "${private_files_backup}")" \
    --arg private_object_uri "${private_object_uri}" \
    '{
        site_name: $site_name,
        exported_on: $exported_on,
        backup_export_path: $backup_export_path,
        database: {
            filename: $db_filename,
            object_uri: $db_object_uri
        },
        public_files: {
            filename: $public_filename,
            object_uri: $public_object_uri
        },
        private_files: {
            filename: $private_filename,
            object_uri: $private_object_uri
        }
    }' > "${manifest_path}"

gcloud storage cp "${manifest_path}" "${backup_prefix}manifest-${backup_stem}.json"
gcloud storage cp "${manifest_path}" "${backup_prefix}manifest-latest.json"
rm -f "${manifest_path}"

printf '%s\n' "${backup_prefix}"
