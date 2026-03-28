from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "ops" / "founder_runtime" / "adapter.py"


def test_founder_runtime_adapter_dry_run_renders_runtime_assets(tmp_path: Path) -> None:
	payload = {
		"tenant": {
			"name": "TEN-2026-0001",
			"tenant_name": "Alpha School",
			"tenant_slug": "alpha-school",
		},
		"policy": {
			"name": "Standard GCS",
			"backup_frequency": "Daily",
			"backup_retention_days": 14,
		},
			"environment": {
				"name": "ENV-2026-0001",
				"environment_name": "Alpha School Sandbox",
				"environment_type": "Sandbox",
				"site_name": "alpha-school-sandbox",
				"site_status": "Sandbox Provisioning",
				"primary_cloud_provider": "OVH",
				"runtime_provider": "OVH",
				"object_storage_provider": "Google Cloud",
				"dns_provider": "Google Cloud DNS",
				"ifitwala_ed_branch": "main",
				"ifitwala_drive_branch": "main",
				"file_storage_provider": "GCS",
				"file_storage_class": "Frequent Access",
				"backup_storage_provider": "GCS",
				"backup_storage_class": "Infrequent Access",
			},
			"providers": {
				"primary_cloud_provider": "OVH",
				"runtime_provider": "OVH",
				"object_storage_provider": "Google Cloud",
				"dns_provider": "Google Cloud DNS",
			},
			"storage": {
				"file_storage_provider": "GCS",
				"file_storage_class": "Frequent Access",
			"backup_storage_provider": "GCS",
			"backup_storage_class": "Infrequent Access",
		},
	}
	env = os.environ.copy()
	env.update(
		{
			"IFITWALA_FOUNDER_RUNTIME_ROOT": str(tmp_path / "runtime"),
			"IFITWALA_FOUNDER_RUNTIME_IMAGE": "registry.example.com/ifitwala/runtime:latest",
			"IFITWALA_FOUNDER_RUNTIME_DB_HOST": "127.0.0.1",
			"IFITWALA_FOUNDER_RUNTIME_DB_PORT": "3306",
			"IFITWALA_FOUNDER_RUNTIME_DB_ROOT_USER": "root",
			"IFITWALA_FOUNDER_RUNTIME_DB_ROOT_PASSWORD": "secret",
			"IFITWALA_FOUNDER_RUNTIME_ADMIN_PASSWORD": "admin-secret",
			"IFITWALA_FOUNDER_RUNTIME_GCS_FILES_BUCKET": "ifitwala-files",
			"IFITWALA_FOUNDER_RUNTIME_GCS_BACKUPS_BUCKET": "ifitwala-backups",
			"IFITWALA_FOUNDER_RUNTIME_DOMAIN_SUFFIX": "ifitwala.com",
			"IFITWALA_FOUNDER_RUNTIME_EDGE_PROXY_MODE": "shared_nginx_proxy",
			"IFITWALA_FOUNDER_RUNTIME_EXECUTE": "0",
		}
	)

	result = subprocess.run(
		[sys.executable, str(ADAPTER), "provision-demo-runtime"],
		input=json.dumps(payload),
		text=True,
		capture_output=True,
		check=True,
		env=env,
	)

	parsed = json.loads(result.stdout)
	runtime_dir = tmp_path / "runtime" / "environments" / "alpha-school-sandbox"

	assert parsed["site_name"] == "alpha-school-sandbox"
	assert parsed["routing_mode"] == "Pending"
	assert parsed["dns_ready"] == 0
	assert parsed["runtime_reference"] == "compose:ifw-alpha-school-sandbox"
	assert parsed["backup_export_path"] == "gs://ifitwala-backups/sites/alpha-school-sandbox/daily/"
	assert (runtime_dir / "compose.yaml").is_file()
	assert (runtime_dir / ".env").is_file()
	assert (runtime_dir / "sites" / "common_site_config.json").is_file()
	assert (runtime_dir / "runtime-config" / "provision.sql").is_file()
	assert (runtime_dir / "nginx" / "default.conf").is_file()
	assert (tmp_path / "runtime" / "edge-proxy" / "compose.yaml").is_file()
	assert (tmp_path / "runtime" / "edge-proxy" / "conf.d" / "alpha-school-sandbox.conf").is_file()

	common_site_config = json.loads((runtime_dir / "sites" / "common_site_config.json").read_text())
	assert common_site_config["approved_apps"] == ["frappe", "ifitwala_ed", "ifitwala_drive"]
	assert common_site_config["gcs_files_bucket"] == "ifitwala-files"
	assert common_site_config["gcs_backups_bucket"] == "ifitwala-backups"
