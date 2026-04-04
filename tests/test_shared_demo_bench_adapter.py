from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "ops" / "shared_demo_bench" / "adapter.py"


def _base_payload() -> dict[str, object]:
	return {
		"tenant": {
			"name": "TEN-2026-0001",
			"tenant_name": "Alpha School",
			"tenant_slug": "alpha-school",
		},
		"policy": {
			"name": "Sandbox Policy",
			"default_ingress_access_mode": "Public",
		},
		"environment": {
			"name": "ENV-2026-0001",
			"environment_name": "Alpha School Sandbox",
			"environment_type": "Sandbox",
			"site_name": "alpha-school-sandbox",
			"site_status": "Sandbox Provisioning",
			"runtime_pool": "POOL-1",
			"primary_cloud_provider": "Google Cloud",
			"runtime_provider": "Google Cloud",
			"object_storage_provider": "Google Cloud",
			"dns_provider": "Google Cloud DNS",
			"ifitwala_ed_branch": "main",
			"ifitwala_drive_branch": "main",
			"file_storage_provider": "GCS",
			"file_storage_class": "Frequent Access",
			"backup_storage_provider": "GCS",
			"backup_storage_class": "Infrequent Access",
		},
		"runtime_pool": {
			"name": "POOL-1",
			"pool_name": "Shared Demo Pool",
			"pool_mode": "Shared Runtime",
			"pool_status": "Active",
			"orchestrator_type": "Bench",
			"primary_cloud_provider": "Google Cloud",
			"runtime_provider": "Google Cloud",
			"region": "us-central1",
			"pool_reference": "demo-bench-01",
			"host_reference": "demo-vm-01",
			"site_capacity": 10,
			"assigned_site_count": 2,
		},
	}


def _base_env(tmp_path: Path) -> dict[str, str]:
	env = os.environ.copy()
	env.update(
		{
			"IFITWALA_SHARED_DEMO_BENCH_ROOT": str(tmp_path / "runtime"),
			"IFITWALA_SHARED_DEMO_BENCH_IMAGE": "registry.example.com/ifitwala/runtime:latest",
			"IFITWALA_SHARED_DEMO_BENCH_DB_HOST": "127.0.0.1",
			"IFITWALA_SHARED_DEMO_BENCH_DB_PORT": "3306",
			"IFITWALA_SHARED_DEMO_BENCH_DB_ROOT_USER": "root",
			"IFITWALA_SHARED_DEMO_BENCH_DB_ROOT_PASSWORD": "secret",
			"IFITWALA_SHARED_DEMO_BENCH_ADMIN_PASSWORD": "admin-secret",
			"IFITWALA_SHARED_DEMO_BENCH_GCS_FILES_BUCKET": "ifitwala-files",
			"IFITWALA_SHARED_DEMO_BENCH_GCS_BACKUPS_BUCKET": "ifitwala-backups",
			"IFITWALA_SHARED_DEMO_BENCH_DOMAIN_SUFFIX": "ifitwala.com",
			"IFITWALA_SHARED_DEMO_BENCH_EDGE_PROXY_MODE": "shared_nginx_proxy",
			"IFITWALA_SHARED_DEMO_BENCH_EXECUTE": "0",
		}
	)
	return env


def test_shared_demo_bench_adapter_dry_run_provisions_site_on_pool(tmp_path: Path) -> None:
	payload = _base_payload()
	env = _base_env(tmp_path)

	result = subprocess.run(
		[sys.executable, str(ADAPTER), "provision-shared-demo-site"],
		input=json.dumps(payload),
		text=True,
		capture_output=True,
		check=True,
		env=env,
	)

	parsed = json.loads(result.stdout)
	pool_dir = tmp_path / "runtime" / "pools" / "demo-bench-01"
	site_manifest = pool_dir / "runtime-config" / "sites" / "alpha-school-sandbox.json"

	assert parsed["site_name"] == "alpha-school-sandbox"
	assert parsed["routing_mode"] == "Pending"
	assert parsed["runtime_reference"] == "bench:demo-bench-01:site:alpha-school-sandbox"
	assert parsed["backup_export_path"] == "gs://ifitwala-backups/sites/alpha-school-sandbox/daily/"
	assert (pool_dir / "compose.yaml").is_file()
	assert (pool_dir / ".env").is_file()
	assert (pool_dir / "sites" / "common_site_config.json").is_file()
	assert (pool_dir / "nginx" / "default.conf").is_file()
	assert site_manifest.is_file()
	assert (tmp_path / "runtime" / "edge-proxy" / "conf.d" / "alpha-school-sandbox.conf").is_file()

	site_metadata = json.loads(site_manifest.read_text())
	assert site_metadata["pool_reference"] == "demo-bench-01"
	assert site_metadata["files_prefix"] == "sites/alpha-school-sandbox/files/"


def test_shared_demo_bench_adapter_dry_run_restore_returns_planned_result(tmp_path: Path) -> None:
	payload = _base_payload()
	payload["environment"]["site_status"] = "Suspended"
	payload["environment"]["runtime_reference"] = "bench:demo-bench-01:site:alpha-school-sandbox"
	payload["environment"]["backup_export_path"] = "gs://ifitwala-backups/sites/alpha-school-sandbox/daily/"
	env = _base_env(tmp_path)

	subprocess.run(
		[sys.executable, str(ADAPTER), "provision-shared-demo-site"],
		input=json.dumps(payload),
		text=True,
		capture_output=True,
		check=True,
		env=env,
	)

	result = subprocess.run(
		[sys.executable, str(ADAPTER), "restore-shared-demo-site"],
		input=json.dumps(payload),
		text=True,
		capture_output=True,
		check=True,
		env=env,
	)

	parsed = json.loads(result.stdout)

	assert parsed["last_provisioning_step"] == "Shared demo site restore planned"
	assert parsed["runtime_reference"] == "bench:demo-bench-01:site:alpha-school-sandbox"
	assert parsed["backup_export_path"] == "gs://ifitwala-backups/sites/alpha-school-sandbox/daily/"
	assert (
		parsed["restored_backup_manifest"]
		== "gs://ifitwala-backups/sites/alpha-school-sandbox/daily/manifest-latest.json"
	)
	assert parsed["db_restore_tested_on"] is None
