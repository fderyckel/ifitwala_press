#!/usr/bin/env bash
set -euo pipefail

BENCH_DIR="${BENCH_DIR:-/home/frappe/frappe-bench}"
cd "$BENCH_DIR"

if ! bench --site "$SITE_NAME" list-apps >/dev/null 2>&1; then
    new_site_cmd=(
        bench new-site "$SITE_NAME"
        --db-host "$DB_HOST"
        --db-port "$DB_PORT"
        --db-name "$DB_NAME"
        --mariadb-root-username "$DB_ROOT_USER"
        --mariadb-root-password "$DB_ROOT_PASSWORD"
        --admin-password "$ADMIN_PASSWORD"
    )

    if [[ -n "${DB_USER:-}" ]]; then
        new_site_cmd+=(--db-user "$DB_USER")
    fi

    if [[ -n "${DB_PASSWORD:-}" ]]; then
        new_site_cmd+=(--db-password "$DB_PASSWORD")
    fi

    "${new_site_cmd[@]}"
    bench --site "$SITE_NAME" install-app ifitwala_ed
    bench --site "$SITE_NAME" install-app ifitwala_drive
fi

if [[ -n "${SITE_DOMAIN:-}" ]]; then
    bench --site "$SITE_NAME" set-config host_name "https://${SITE_DOMAIN}"
fi

if [[ -n "${FILE_STORAGE_PROVIDER:-}" ]]; then
    bench --site "$SITE_NAME" set-config file_storage_provider "${FILE_STORAGE_PROVIDER}"
fi

if [[ -n "${FILE_STORAGE_CLASS:-}" ]]; then
    bench --site "$SITE_NAME" set-config file_storage_class "${FILE_STORAGE_CLASS}"
fi

if [[ -n "${BACKUP_STORAGE_PROVIDER:-}" ]]; then
    bench --site "$SITE_NAME" set-config backup_storage_provider "${BACKUP_STORAGE_PROVIDER}"
fi

if [[ -n "${BACKUP_STORAGE_CLASS:-}" ]]; then
    bench --site "$SITE_NAME" set-config backup_storage_class "${BACKUP_STORAGE_CLASS}"
fi

if [[ -n "${GCS_PROJECT:-}" ]]; then
    bench --site "$SITE_NAME" set-config gcs_project "${GCS_PROJECT}"
fi

if [[ -n "${GCS_FILES_BUCKET:-}" ]]; then
    bench --site "$SITE_NAME" set-config gcs_files_bucket "${GCS_FILES_BUCKET}"
fi

if [[ -n "${GCS_FILES_PREFIX:-}" ]]; then
    bench --site "$SITE_NAME" set-config gcs_files_prefix "${GCS_FILES_PREFIX}"
fi

if [[ -n "${GCS_BACKUPS_BUCKET:-}" ]]; then
    bench --site "$SITE_NAME" set-config gcs_backups_bucket "${GCS_BACKUPS_BUCKET}"
fi

if [[ -n "${GCS_BACKUPS_PREFIX:-}" ]]; then
    bench --site "$SITE_NAME" set-config gcs_backups_prefix "${GCS_BACKUPS_PREFIX}"
fi
