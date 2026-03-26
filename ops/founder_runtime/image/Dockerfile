ARG FRAPPE_BASE_IMAGE=ghcr.io/frappe/frappe-worker:latest
FROM ${FRAPPE_BASE_IMAGE}

USER root
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install --yes --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

USER frappe
WORKDIR /home/frappe/frappe-bench

ARG IFITWALA_ED_REPO
ARG IFITWALA_ED_REF=main
ARG IFITWALA_DRIVE_REPO
ARG IFITWALA_DRIVE_REF=main

RUN test -n "${IFITWALA_ED_REPO}" \
    && test -n "${IFITWALA_DRIVE_REPO}"

RUN bench get-app --branch "${IFITWALA_ED_REF}" "${IFITWALA_ED_REPO}" \
    && bench get-app --branch "${IFITWALA_DRIVE_REF}" "${IFITWALA_DRIVE_REPO}" \
    && bench setup requirements \
    && bench build --production
