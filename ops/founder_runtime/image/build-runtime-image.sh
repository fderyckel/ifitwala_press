#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -n "${BUILD_ENV_FILE:-}" ]]; then
    # shellcheck disable=SC1090
    source "${BUILD_ENV_FILE}"
fi

: "${IMAGE_TAG:?IMAGE_TAG is required.}"
: "${IFITWALA_ED_REPO:?IFITWALA_ED_REPO is required.}"
: "${IFITWALA_DRIVE_REPO:?IFITWALA_DRIVE_REPO is required.}"

frappe_base_image="${FRAPPE_BASE_IMAGE:-ghcr.io/frappe/frappe-worker:latest}"
ifitwala_ed_ref="${IFITWALA_ED_REF:-main}"
ifitwala_drive_ref="${IFITWALA_DRIVE_REF:-main}"

docker build \
    --build-arg "FRAPPE_BASE_IMAGE=${frappe_base_image}" \
    --build-arg "IFITWALA_ED_REPO=${IFITWALA_ED_REPO}" \
    --build-arg "IFITWALA_ED_REF=${ifitwala_ed_ref}" \
    --build-arg "IFITWALA_DRIVE_REPO=${IFITWALA_DRIVE_REPO}" \
    --build-arg "IFITWALA_DRIVE_REF=${ifitwala_drive_ref}" \
    --tag "${IMAGE_TAG}" \
    --file "${script_dir}/Dockerfile" \
    "${script_dir}"

if [[ "${PUSH_IMAGE:-0}" == "1" ]]; then
    docker push "${IMAGE_TAG}"
fi

printf '%s\n' "${IMAGE_TAG}"
