#!/usr/bin/env bash
set -euo pipefail

runtime_dir="${1:?runtime directory required}"

set -a
source "${runtime_dir}/.env"
set +a

docker compose -f "${runtime_dir}/compose.yaml" --project-directory "${runtime_dir}" \
    exec -T backend bench --site "${SITE_NAME}" backup --with-files --compress

latest_backup="$(ls -1t "${runtime_dir}/sites/${SITE_NAME}/private/backups"/*.tgz | head -n 1)"
backup_name="$(basename "${latest_backup}")"
backup_target="s3://${S3_BACKUPS_BUCKET}/${S3_BACKUPS_PREFIX}${backup_name}"

AWS_ACCESS_KEY_ID="${S3_ACCESS_KEY}" \
AWS_SECRET_ACCESS_KEY="${S3_SECRET_KEY}" \
aws --endpoint-url "${S3_ENDPOINT}" s3 cp "${latest_backup}" "${backup_target}"

printf '%s\n' "${backup_target}"
