# Shared Demo Bench Adapter

This adapter is the shared-runtime path for founder demos and smaller schools.

It differs from `ops/founder_runtime` in one critical way:

- `ops/founder_runtime` provisions a dedicated Compose stack per environment
- `ops/shared_demo_bench` provisions many sites onto one reusable bench/runtime pool

Current contract:

- one runtime pool = one shared bench stack
- one site = one database
- shared Redis, worker, scheduler, nginx, and backend processes per pool
- per-site GCS prefixes for files and backups
- shared founder edge proxy route per site when enabled

Supported adapter actions:

- `provision-shared-demo-site`
- `sync-shared-demo-edge-route`
- `teardown-shared-demo-site`
- `restore-shared-demo-site`

Host prerequisites:

- Docker with `docker compose`
- `gcloud`
- `jq`
- `mariadb-client`
- access to the published runtime image containing `frappe`, `ifitwala_ed`, and `ifitwala_drive`

This is the intended runtime shape for:

- founder-managed demos
- manually approved sandbox schools
- smaller schools that do not yet justify dedicated runtime isolation
