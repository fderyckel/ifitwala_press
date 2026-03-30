#!/usr/bin/env bash
set -euo pipefail

BENCH_DIR="${BENCH_DIR:-/home/frappe/frappe-bench}"
cd "$BENCH_DIR"

if bench --site "$SITE_NAME" list-apps >/dev/null 2>&1; then
    exit 0
fi

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

if [[ -n "${SITE_DOMAIN:-}" ]]; then
    bench --site "$SITE_NAME" set-config host_name "https://${SITE_DOMAIN}"
fi
