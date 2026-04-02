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


def test_founder_runtime_adapter_dry_run_restore_returns_planned_result(tmp_path: Path) -> None:
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
			"site_status": "Suspended",
			"runtime_reference": "compose:ifw-alpha-school-sandbox",
			"backup_export_path": "gs://ifitwala-backups/sites/alpha-school-sandbox/daily/",
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

	subprocess.run(
		[sys.executable, str(ADAPTER), "provision-demo-runtime"],
		input=json.dumps(payload),
		text=True,
		capture_output=True,
		check=True,
		env=env,
	)

	result = subprocess.run(
		[sys.executable, str(ADAPTER), "restore-demo-runtime"],
		input=json.dumps(payload),
		text=True,
		capture_output=True,
		check=True,
		env=env,
	)

	parsed = json.loads(result.stdout)

	assert parsed["last_provisioning_step"] == "Restore planned"
	assert parsed["runtime_reference"] == "compose:ifw-alpha-school-sandbox"
	assert parsed["backup_export_path"] == "gs://ifitwala-backups/sites/alpha-school-sandbox/daily/"
	assert (
		parsed["restored_backup_manifest"]
		== "gs://ifitwala-backups/sites/alpha-school-sandbox/daily/manifest-latest.json"
	)
	assert parsed["db_restore_tested_on"] is None


def test_founder_runtime_adapter_dry_run_host_firewall_sync_returns_plan(tmp_path: Path) -> None:
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
			"IFITWALA_FOUNDER_RUNTIME_EDGE_PROXY_MODE": "shared_nginx_proxy",
			"IFITWALA_FOUNDER_RUNTIME_FIREWALL_ENABLED": "1",
			"IFITWALA_FOUNDER_RUNTIME_ALLOWED_SSH_CIDRS": "203.0.113.10/32,198.51.100.0/24",
			"IFITWALA_FOUNDER_RUNTIME_PUBLIC_TCP_PORTS": "80,443",
			"IFITWALA_FOUNDER_RUNTIME_EXECUTE": "0",
		}
	)

	result = subprocess.run(
		[sys.executable, str(ADAPTER), "sync-host-firewall"],
		input="",
		text=True,
		capture_output=True,
		check=True,
		env=env,
	)

	parsed = json.loads(result.stdout)

	assert parsed["firewall_enabled"] == 1
	assert parsed["allowed_ssh_cidrs"] == ["203.0.113.10/32", "198.51.100.0/24"]
	assert parsed["public_tcp_ports"] == [80, 443]
	assert parsed["last_provisioning_step"] == "Host firewall sync planned"


def test_founder_runtime_adapter_renders_allowlisted_edge_proxy_route(tmp_path: Path) -> None:
	payload = {
		"tenant": {
			"name": "TEN-2026-0001",
			"tenant_name": "Alpha School",
			"tenant_slug": "alpha-school",
		},
		"policy": {
			"name": "Sandbox Policy",
			"default_ingress_access_mode": "Allowlisted",
		},
		"environment": {
			"name": "ENV-2026-0001",
			"environment_name": "Alpha School Sandbox",
			"environment_type": "Sandbox",
			"site_name": "alpha-school-sandbox",
			"site_status": "Sandbox Provisioning",
			"primary_domain": "alpha-school-sandbox.ifitwala.com",
			"ingress_access_mode": "Allowlisted",
			"ingress_allowlist": [
				{"cidr": "203.0.113.10/32"},
				{"cidr": "198.51.100.0/24"},
			],
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
			"IFITWALA_FOUNDER_RUNTIME_EDGE_PROXY_MODE": "shared_nginx_proxy",
			"IFITWALA_FOUNDER_RUNTIME_EXECUTE": "0",
		}
	)

	subprocess.run(
		[sys.executable, str(ADAPTER), "provision-demo-runtime"],
		input=json.dumps(payload),
		text=True,
		capture_output=True,
		check=True,
		env=env,
	)

	route = (tmp_path / "runtime" / "edge-proxy" / "conf.d" / "alpha-school-sandbox.conf").read_text()

	assert "allow 203.0.113.10/32;" in route
	assert "allow 198.51.100.0/24;" in route
	assert "deny all;" in route


def test_founder_runtime_adapter_renders_disabled_edge_proxy_route(tmp_path: Path) -> None:
	payload = {
		"tenant": {
			"name": "TEN-2026-0002",
			"tenant_name": "Beta School",
			"tenant_slug": "beta-school",
		},
		"policy": {
			"name": "Sandbox Policy",
			"default_ingress_access_mode": "Disabled",
		},
		"environment": {
			"name": "ENV-2026-0002",
			"environment_name": "Beta School Sandbox",
			"environment_type": "Sandbox",
			"site_name": "beta-school-sandbox",
			"site_status": "Sandbox Provisioning",
			"primary_domain": "beta-school-sandbox.ifitwala.com",
			"ingress_access_mode": "Disabled",
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
			"IFITWALA_FOUNDER_RUNTIME_EDGE_PROXY_MODE": "shared_nginx_proxy",
			"IFITWALA_FOUNDER_RUNTIME_EXECUTE": "0",
		}
	)

	subprocess.run(
		[sys.executable, str(ADAPTER), "provision-demo-runtime"],
		input=json.dumps(payload),
		text=True,
		capture_output=True,
		check=True,
		env=env,
	)

	route = (tmp_path / "runtime" / "edge-proxy" / "conf.d" / "beta-school-sandbox.conf").read_text()

	assert "return 403;" in route


def test_founder_runtime_adapter_sync_edge_route_updates_existing_route(tmp_path: Path) -> None:
	payload = {
		"tenant": {
			"name": "TEN-2026-0003",
			"tenant_name": "Gamma School",
			"tenant_slug": "gamma-school",
		},
		"policy": {
			"name": "Sandbox Policy",
			"default_ingress_access_mode": "Public",
		},
		"environment": {
			"name": "ENV-2026-0003",
			"environment_name": "Gamma School Sandbox",
			"environment_type": "Sandbox",
			"site_name": "gamma-school-sandbox",
			"site_status": "Sandbox Active",
			"primary_domain": "gamma-school-sandbox.ifitwala.com",
			"ingress_access_mode": "Public",
			"runtime_reference": "compose:ifw-gamma-school-sandbox",
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
			"IFITWALA_FOUNDER_RUNTIME_EDGE_PROXY_MODE": "shared_nginx_proxy",
			"IFITWALA_FOUNDER_RUNTIME_EXECUTE": "0",
		}
	)

	subprocess.run(
		[sys.executable, str(ADAPTER), "provision-demo-runtime"],
		input=json.dumps(payload),
		text=True,
		capture_output=True,
		check=True,
		env=env,
	)

	payload["environment"]["ingress_access_mode"] = "Allowlisted"
	payload["environment"]["ingress_allowlist"] = [{"cidr": "203.0.113.10/32"}]
	result = subprocess.run(
		[sys.executable, str(ADAPTER), "sync-edge-route"],
		input=json.dumps(payload),
		text=True,
		capture_output=True,
		check=True,
		env=env,
	)

	parsed = json.loads(result.stdout)
	route = (tmp_path / "runtime" / "edge-proxy" / "conf.d" / "gamma-school-sandbox.conf").read_text()

	assert parsed["last_provisioning_step"] == "Founder edge route synced"
	assert "allow 203.0.113.10/32;" in route
	assert "deny all;" in route
