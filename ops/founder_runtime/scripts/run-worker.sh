#!/usr/bin/env bash
set -euo pipefail

cd "${BENCH_DIR:-/home/frappe/frappe-bench}"
exec bench worker --queue short,default,long
