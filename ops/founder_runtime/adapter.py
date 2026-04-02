#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import secrets
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from string import Template
from typing import Any

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[1]
TEMPLATES_DIR = ROOT / "templates"
SCRIPTS_DIR = ROOT / "scripts"
ENVIRONMENT_ROOT_NAME = "environments"
EDGE_PROXY_ROOT_NAME = "edge-proxy"
DEFAULT_DB_PORT = 3306
DEFAULT_HTTP_PORT_BASE = 18080
DEFAULT_DNS_TTL = 300
DEFAULT_EDGE_PROXY_MODE = "manual_host_proxy"
SITE_SLUG_PATTERN = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class RuntimeSettings:
	runtime_root: Path
	runtime_image: str
	db_host: str
	db_port: int
	db_root_user: str
	db_root_password: str
	admin_password: str
	gcs_files_bucket: str
	gcs_backups_bucket: str
	domain_suffix: str | None
	dns_zone: str | None
	dns_target_ip: str | None
	dns_ttl: int
	gcloud_project: str | None
	edge_proxy_mode: str
	edge_proxy_root: Path
	http_port_base: int
	firewall_enabled: bool
	allowed_ssh_cidrs: tuple[str, ...]
	public_tcp_ports: tuple[int, ...]
	firewall_script: Path
	execute: bool


@dataclass(frozen=True)
class RuntimePlan:
	site_name: str
	project_slug: str
	runtime_dir: Path
	compose_project_name: str
	http_port: int
	primary_domain: str | None
	host_header_value: str | None
	db_name: str
	db_user: str
	db_password: str
	files_prefix: str
	backups_prefix: str
	backup_export_prefix: str
	ingress_access_mode: str
	ingress_allowlist: tuple[str, ...]


def main(argv: list[str] | None = None) -> int:
	args = list(argv or sys.argv[1:])
	if len(args) != 1 or args[0] not in {
		"provision-demo-runtime",
		"sync-host-firewall",
		"sync-edge-route",
		"teardown-demo-runtime",
		"restore-demo-runtime",
	}:
		print(
			"Usage: adapter.py [provision-demo-runtime|sync-host-firewall|sync-edge-route|teardown-demo-runtime|restore-demo-runtime]",
			file=sys.stderr,
		)
		return 2

	payload = _load_payload()
	settings = _load_settings()

	if args[0] == "provision-demo-runtime":
		result = provision_demo_runtime(payload, settings)
	elif args[0] == "sync-host-firewall":
		result = sync_host_firewall(payload, settings)
	elif args[0] == "sync-edge-route":
		result = sync_edge_route(payload, settings)
	elif args[0] == "restore-demo-runtime":
		result = restore_demo_runtime(payload, settings)
	else:
		result = teardown_demo_runtime(payload, settings)

	print(json.dumps(result))
	return 0


def provision_demo_runtime(payload: dict[str, Any], settings: RuntimeSettings) -> dict[str, Any]:
	plan = _build_plan(payload, settings)
	_render_runtime_assets(plan, payload, settings)

	last_step = "Runtime assets rendered"
	message = "Runtime assets rendered. Execution not requested."
	dns_ready = 0
	edge_proxy_ready = 0

	if settings.edge_proxy_mode == "shared_nginx_proxy" and plan.primary_domain:
		_prepare_edge_proxy(plan, settings)
		edge_proxy_ready = 1

	if settings.execute:
		_require_command("docker")
		_require_command("mysql")
		_apply_database_plan(plan, settings)
		last_step = "Database provisioned"
		_start_compose_stack(plan)
		last_step = "Docker compose stack started"
		_bootstrap_site(plan)
		last_step = "Site bootstrap completed"
		if settings.edge_proxy_mode == "shared_nginx_proxy" and plan.primary_domain:
			_start_edge_proxy(settings)
			_reload_edge_proxy(settings)
			last_step = "Shared edge proxy route ensured"
		dns_ready = _ensure_dns_record(plan, settings)
		last_step = "Cloud DNS ensured" if dns_ready else last_step
		message = (
			"Founder runtime provisioned with Docker Compose, shared edge proxy, and bootstrap completed."
		)

	return {
		"site_name": plan.site_name,
		"primary_domain": plan.primary_domain,
		"routing_mode": _routing_mode(plan, settings, dns_ready=dns_ready, edge_proxy_ready=edge_proxy_ready),
		"dns_ready": dns_ready,
		"tls_ready": 0,
		"host_header_value": plan.host_header_value,
		"db_name": plan.db_name,
		"db_user": plan.db_user,
		"provisioning_job_id": plan.compose_project_name,
		"last_provisioning_step": last_step,
		"provisioning_message": message,
		"runtime_reference": f"compose:{plan.compose_project_name}",
		"file_storage_provider": payload.get("environment", {}).get("file_storage_provider") or "GCS",
		"file_storage_class": payload.get("environment", {}).get("file_storage_class") or "Frequent Access",
		"backup_storage_provider": payload.get("environment", {}).get("backup_storage_provider") or "GCS",
		"backup_storage_class": payload.get("environment", {}).get("backup_storage_class")
		or "Infrequent Access",
		"backup_export_path": plan.backup_export_prefix,
		"status_reason": "Founder runtime scaffolded for Docker Compose and gcloud-backed DNS handling.",
	}


def teardown_demo_runtime(payload: dict[str, Any], settings: RuntimeSettings) -> dict[str, Any]:
	site_name = _require_site_name(payload)
	project_slug = _slugify(site_name)
	runtime_dir = settings.runtime_root / ENVIRONMENT_ROOT_NAME / project_slug
	last_step = "Runtime assets retained"
	message = "No runtime directory found."

	if runtime_dir.exists():
		message = "Runtime directory retained for audit and backup inspection."
		if settings.execute and (runtime_dir / "compose.yaml").exists():
			_require_command("docker")
			_run(
				["docker", "compose", "down", "--remove-orphans"],
				cwd=runtime_dir,
			)
			last_step = "Docker compose stack removed"
			message = "Founder runtime stopped and removed."

			if settings.edge_proxy_mode == "shared_nginx_proxy":
				_remove_edge_proxy_route(project_slug, settings)
				_reload_edge_proxy(settings)

			primary_domain = payload.get("environment", {}).get("primary_domain")
			if primary_domain:
				_remove_dns_record(primary_domain, settings)
		else:
			last_step = "Runtime teardown planned"

	return {
		"last_provisioning_step": last_step,
		"provisioning_message": message,
		"runtime_reference": f"compose:ifw-{project_slug}",
		"backup_export_path": payload.get("environment", {}).get("backup_export_path"),
	}


def sync_host_firewall(payload: dict[str, Any], settings: RuntimeSettings) -> dict[str, Any]:
	_validate_firewall_settings(settings)
	message = "Founder host firewall sync planned. Execution not requested."
	last_step = "Host firewall sync planned"

	if settings.execute:
		_run_firewall_sync(settings)
		state = "enabled" if settings.firewall_enabled else "disabled"
		last_step = "Founder host firewall synced"
		message = f"Founder host firewall {state} with repo-managed ufw policy."

	return {
		"firewall_enabled": int(settings.firewall_enabled),
		"allowed_ssh_cidrs": list(settings.allowed_ssh_cidrs),
		"public_tcp_ports": list(settings.public_tcp_ports),
		"firewall_sync_script": str(settings.firewall_script),
		"last_provisioning_step": last_step,
		"provisioning_message": message,
		"status_reason": "Founder host firewall intent validated.",
	}


def sync_edge_route(payload: dict[str, Any], settings: RuntimeSettings) -> dict[str, Any]:
	plan = _build_plan(payload, settings)
	if settings.edge_proxy_mode != "shared_nginx_proxy":
		return {
			"routing_mode": _routing_mode(plan, settings, dns_ready=0, edge_proxy_ready=0),
			"host_header_value": plan.host_header_value,
			"last_provisioning_step": "Founder edge route sync skipped",
			"provisioning_message": "Founder edge route sync requires IFITWALA_FOUNDER_RUNTIME_EDGE_PROXY_MODE=shared_nginx_proxy.",
			"status_reason": "Shared founder edge proxy is not enabled.",
		}

	if not plan.primary_domain:
		return {
			"routing_mode": _routing_mode(plan, settings, dns_ready=0, edge_proxy_ready=0),
			"host_header_value": plan.host_header_value,
			"last_provisioning_step": "Founder edge route sync skipped",
			"provisioning_message": "Primary domain is required before founder edge routes can be synced.",
			"status_reason": "Primary domain missing for founder edge route sync.",
		}

	_prepare_edge_proxy(plan, settings)
	if settings.execute:
		_start_edge_proxy(settings)
		_reload_edge_proxy(settings)

	return {
		"routing_mode": _routing_mode(plan, settings, dns_ready=0, edge_proxy_ready=1),
		"host_header_value": plan.host_header_value,
		"last_provisioning_step": "Founder edge route synced",
		"provisioning_message": (
			"Founder edge route rendered and nginx reloaded."
			if settings.execute
			else "Founder edge route rendered. Execution not requested."
		),
		"status_reason": "Founder edge route synced from environment ingress intent.",
	}


def restore_demo_runtime(payload: dict[str, Any], settings: RuntimeSettings) -> dict[str, Any]:
	plan = _build_plan(payload, settings)
	if not plan.runtime_dir.exists():
		raise SystemExit(f"Runtime directory not found for restore: {plan.runtime_dir}")

	backup_export_path = (
		str(payload.get("environment", {}).get("backup_export_path") or "").strip()
		or plan.backup_export_prefix
	)
	last_step = "Restore planned"
	message = "Restore planned. Execution not requested."
	restored_manifest_uri = f"{backup_export_path.rstrip('/')}/manifest-latest.json"

	if settings.execute:
		_require_command("gcloud")
		_require_command("docker")
		_require_command("jq")
		_restore_site(plan, backup_export_path)
		last_step = "Site restore completed"
		message = "Founder runtime restored from exported backup."

	return {
		"last_provisioning_step": last_step,
		"provisioning_message": message,
		"runtime_reference": f"compose:{plan.compose_project_name}",
		"backup_export_path": backup_export_path,
		"restored_backup_manifest": restored_manifest_uri,
		"db_restore_tested_on": date.today().isoformat() if settings.execute else None,
	}


def _load_payload() -> dict[str, Any]:
	raw_payload = sys.stdin.read()
	if not raw_payload.strip():
		return {}

	try:
		payload = json.loads(raw_payload)
	except json.JSONDecodeError as exc:
		raise SystemExit(f"Invalid JSON payload: {exc}") from exc

	if not isinstance(payload, dict):
		raise SystemExit("Payload must be a JSON object.")

	return payload


def _load_settings() -> RuntimeSettings:
	runtime_root = Path(_env("IFITWALA_FOUNDER_RUNTIME_ROOT", required=True)).expanduser()
	return RuntimeSettings(
		runtime_root=runtime_root,
		runtime_image=_env("IFITWALA_FOUNDER_RUNTIME_IMAGE", required=True),
		db_host=_env("IFITWALA_FOUNDER_RUNTIME_DB_HOST", required=True),
		db_port=int(_env("IFITWALA_FOUNDER_RUNTIME_DB_PORT", default=str(DEFAULT_DB_PORT))),
		db_root_user=_env("IFITWALA_FOUNDER_RUNTIME_DB_ROOT_USER", required=True),
		db_root_password=_env("IFITWALA_FOUNDER_RUNTIME_DB_ROOT_PASSWORD", required=True),
		admin_password=_env("IFITWALA_FOUNDER_RUNTIME_ADMIN_PASSWORD", required=True),
		gcs_files_bucket=_env("IFITWALA_FOUNDER_RUNTIME_GCS_FILES_BUCKET", required=True),
		gcs_backups_bucket=_env("IFITWALA_FOUNDER_RUNTIME_GCS_BACKUPS_BUCKET", required=True),
		domain_suffix=_env("IFITWALA_FOUNDER_RUNTIME_DOMAIN_SUFFIX", default=None),
		dns_zone=_env("IFITWALA_FOUNDER_RUNTIME_DNS_ZONE", default=None),
		dns_target_ip=_env("IFITWALA_FOUNDER_RUNTIME_DNS_TARGET_IP", default=None),
		dns_ttl=int(_env("IFITWALA_FOUNDER_RUNTIME_DNS_TTL", default=str(DEFAULT_DNS_TTL))),
		gcloud_project=_env("IFITWALA_FOUNDER_RUNTIME_GCLOUD_PROJECT", default=None),
		edge_proxy_mode=_env("IFITWALA_FOUNDER_RUNTIME_EDGE_PROXY_MODE", default=DEFAULT_EDGE_PROXY_MODE),
		edge_proxy_root=Path(
			_env(
				"IFITWALA_FOUNDER_RUNTIME_EDGE_PROXY_ROOT",
				default=str(runtime_root / EDGE_PROXY_ROOT_NAME),
			)
		).expanduser(),
		http_port_base=int(
			_env("IFITWALA_FOUNDER_RUNTIME_HTTP_PORT_BASE", default=str(DEFAULT_HTTP_PORT_BASE))
		),
		firewall_enabled=_env("IFITWALA_FOUNDER_RUNTIME_FIREWALL_ENABLED", default="0") == "1",
		allowed_ssh_cidrs=tuple(
			_parse_csv_values(_env("IFITWALA_FOUNDER_RUNTIME_ALLOWED_SSH_CIDRS", default=""))
		),
		public_tcp_ports=tuple(
			int(value)
			for value in _parse_csv_values(
				_env("IFITWALA_FOUNDER_RUNTIME_PUBLIC_TCP_PORTS", default="80,443")
			)
		),
		firewall_script=Path(
			_env(
				"IFITWALA_FOUNDER_RUNTIME_FIREWALL_SCRIPT",
				default=str(ROOT / "host" / "sync-host-firewall.sh"),
			)
		).expanduser(),
		execute=_env("IFITWALA_FOUNDER_RUNTIME_EXECUTE", default="0") == "1",
	)


def _build_plan(payload: dict[str, Any], settings: RuntimeSettings) -> RuntimePlan:
	environment = payload.get("environment", {})
	site_name = _require_site_name(payload)
	project_slug = _slugify(site_name)
	runtime_dir = settings.runtime_root / ENVIRONMENT_ROOT_NAME / project_slug
	existing_env = _read_existing_env(runtime_dir / ".env")
	http_port = int(
		existing_env.get("HTTP_PORT") or _allocate_http_port(settings.runtime_root, settings.http_port_base)
	)
	db_name = (
		environment.get("db_name") or existing_env.get("DB_NAME") or f"site_{project_slug.replace('-', '_')}"
	)
	db_user = (
		environment.get("db_user") or existing_env.get("DB_USER") or f"user_{project_slug.replace('-', '_')}"
	)
	db_password = existing_env.get("DB_PASSWORD") or _secret_token()
	primary_domain = environment.get("primary_domain") or _default_domain(
		project_slug, settings.domain_suffix
	)
	ingress_access_mode = _resolve_ingress_access_mode(payload)
	ingress_allowlist = tuple(_resolve_ingress_allowlist(payload, ingress_access_mode))
	files_prefix = f"sites/{site_name}/files/"
	backups_prefix = f"sites/{site_name}/daily/"

	return RuntimePlan(
		site_name=site_name,
		project_slug=project_slug,
		runtime_dir=runtime_dir,
		compose_project_name=f"ifw-{project_slug}",
		http_port=http_port,
		primary_domain=primary_domain,
		host_header_value=primary_domain,
		db_name=db_name,
		db_user=db_user,
		db_password=db_password,
		files_prefix=files_prefix,
		backups_prefix=backups_prefix,
		backup_export_prefix=f"gs://{settings.gcs_backups_bucket}/{backups_prefix}",
		ingress_access_mode=ingress_access_mode,
		ingress_allowlist=ingress_allowlist,
	)


def _render_runtime_assets(plan: RuntimePlan, payload: dict[str, Any], settings: RuntimeSettings) -> None:
	(runtime_root := plan.runtime_dir).mkdir(parents=True, exist_ok=True)
	(runtime_root / "logs").mkdir(exist_ok=True)
	(runtime_root / "sites").mkdir(exist_ok=True)
	(runtime_root / "nginx").mkdir(exist_ok=True)
	(runtime_root / "runtime-config").mkdir(exist_ok=True)

	(runtime_root / "compose.yaml").write_text((TEMPLATES_DIR / "compose.yaml").read_text())
	(runtime_root / "nginx" / "default.conf").write_text(_render_nginx(plan))
	(runtime_root / ".env").write_text(_render_env(plan, payload, settings))
	(runtime_root / "sites" / "common_site_config.json").write_text(
		_render_common_site_config(plan, payload, settings)
	)
	(runtime_root / "runtime-config" / "payload.json").write_text(
		json.dumps(payload, indent=2, sort_keys=True)
	)
	(runtime_root / "runtime-config" / "provision.sql").write_text(_render_provision_sql(plan))
	(runtime_root / "runtime-config" / "runtime-plan.json").write_text(
		_render_runtime_plan(plan, payload, settings)
	)


def _prepare_edge_proxy(plan: RuntimePlan, settings: RuntimeSettings) -> None:
	settings.edge_proxy_root.mkdir(parents=True, exist_ok=True)
	(settings.edge_proxy_root / "conf.d").mkdir(exist_ok=True)
	(settings.edge_proxy_root / "compose.yaml").write_text((ROOT / "edge_proxy" / "compose.yaml").read_text())
	(settings.edge_proxy_root / "nginx.conf").write_text((ROOT / "edge_proxy" / "nginx.conf").read_text())
	(settings.edge_proxy_root / "conf.d" / f"{plan.project_slug}.conf").write_text(
		_render_edge_proxy_route(plan)
	)


def _render_edge_proxy_route(plan: RuntimePlan) -> str:
	template = Template((ROOT / "edge_proxy" / "route.conf.template").read_text())
	return template.substitute(
		SITE_DOMAIN=plan.primary_domain or "_",
		UPSTREAM_PORT=str(plan.http_port),
		SERVER_ACCESS_DIRECTIVES="",
		LOCATION_ACCESS_DIRECTIVES=_render_location_access_directives(plan),
		LOCATION_BEHAVIOR_DIRECTIVES=_render_location_behavior_directives(plan),
	)


def _render_location_access_directives(plan: RuntimePlan) -> str:
	if plan.ingress_access_mode != "Allowlisted":
		return ""

	indent = " " * 8
	lines = [f"{indent}allow {cidr};" for cidr in plan.ingress_allowlist]
	lines.append(f"{indent}deny all;")
	return "\n".join(lines) + "\n"


def _render_location_behavior_directives(plan: RuntimePlan) -> str:
	if plan.ingress_access_mode != "Disabled":
		return ""
	return "        return 403;\n"


def _render_nginx(plan: RuntimePlan) -> str:
	template = Template((TEMPLATES_DIR / "nginx-default.conf").read_text())
	return template.substitute(SITE_DOMAIN=plan.primary_domain or "_")


def _render_env(plan: RuntimePlan, payload: dict[str, Any], settings: RuntimeSettings) -> str:
	environment = payload.get("environment", {})
	return "\n".join(
		[
			f"COMPOSE_PROJECT_NAME={plan.compose_project_name}",
			f"RUNTIME_IMAGE={settings.runtime_image}",
			f"HTTP_PORT={plan.http_port}",
			f"FOUNDER_RUNTIME_SCRIPTS_DIR={SCRIPTS_DIR}",
			f"SITE_NAME={plan.site_name}",
			f"SITE_DOMAIN={plan.primary_domain or ''}",
			f"DB_HOST={settings.db_host}",
			f"DB_PORT={settings.db_port}",
			f"DB_NAME={plan.db_name}",
			f"DB_USER={plan.db_user}",
			f"DB_PASSWORD={plan.db_password}",
			f"DB_ROOT_USER={settings.db_root_user}",
			f"DB_ROOT_PASSWORD={settings.db_root_password}",
			f"ADMIN_PASSWORD={settings.admin_password}",
			"REDIS_CACHE_URL=redis://redis-cache:6379",
			"REDIS_QUEUE_URL=redis://redis-queue:6379",
			"REDIS_SOCKETIO_URL=redis://redis-socketio:6379",
			f"FILE_STORAGE_PROVIDER={environment.get('file_storage_provider') or 'GCS'}",
			f"FILE_STORAGE_CLASS={environment.get('file_storage_class') or 'Frequent Access'}",
			f"BACKUP_STORAGE_PROVIDER={environment.get('backup_storage_provider') or 'GCS'}",
			f"BACKUP_STORAGE_CLASS={environment.get('backup_storage_class') or 'Infrequent Access'}",
			f"GCS_PROJECT={settings.gcloud_project or ''}",
			f"GCS_FILES_BUCKET={settings.gcs_files_bucket}",
			f"GCS_FILES_PREFIX={plan.files_prefix}",
			f"GCS_BACKUPS_BUCKET={settings.gcs_backups_bucket}",
			f"GCS_BACKUPS_PREFIX={plan.backups_prefix}",
			"",
		]
	)


def _render_common_site_config(plan: RuntimePlan, payload: dict[str, Any], settings: RuntimeSettings) -> str:
	environment = payload.get("environment", {})
	config = {
		"db_host": settings.db_host,
		"db_port": settings.db_port,
		"redis_cache": "redis://redis-cache:6379",
		"redis_queue": "redis://redis-queue:6379",
		"redis_socketio": "redis://redis-socketio:6379",
		"webserver_port": 8000,
		"socketio_port": 9000,
		"file_storage_provider": environment.get("file_storage_provider") or "GCS",
		"file_storage_class": environment.get("file_storage_class") or "Frequent Access",
		"backup_storage_provider": environment.get("backup_storage_provider") or "GCS",
		"backup_storage_class": environment.get("backup_storage_class") or "Infrequent Access",
		"gcs_project": settings.gcloud_project,
		"gcs_files_bucket": settings.gcs_files_bucket,
		"gcs_files_prefix": plan.files_prefix,
		"gcs_backups_bucket": settings.gcs_backups_bucket,
		"gcs_backups_prefix": plan.backups_prefix,
		"approved_apps": ["frappe", "ifitwala_ed", "ifitwala_drive"],
	}
	return json.dumps(config, indent=2, sort_keys=True)


def _render_provision_sql(plan: RuntimePlan) -> str:
	return (
		f"CREATE DATABASE IF NOT EXISTS `{plan.db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;\n"
		f"CREATE USER IF NOT EXISTS '{plan.db_user}'@'%' IDENTIFIED BY '{plan.db_password}';\n"
		f"GRANT ALL PRIVILEGES ON `{plan.db_name}`.* TO '{plan.db_user}'@'%';\n"
		"FLUSH PRIVILEGES;\n"
	)


def _render_runtime_plan(plan: RuntimePlan, payload: dict[str, Any], settings: RuntimeSettings) -> str:
	runtime_plan = {
		"site_name": plan.site_name,
		"primary_domain": plan.primary_domain,
		"compose_project_name": plan.compose_project_name,
		"http_port": plan.http_port,
		"host_header_value": plan.host_header_value,
		"db_name": plan.db_name,
		"db_user": plan.db_user,
		"runtime_image": settings.runtime_image,
		"files_bucket": settings.gcs_files_bucket,
		"files_prefix": plan.files_prefix,
		"backups_bucket": settings.gcs_backups_bucket,
		"backups_prefix": plan.backups_prefix,
		"edge_proxy_mode": settings.edge_proxy_mode,
		"ingress_access_mode": plan.ingress_access_mode,
		"ingress_allowlist": list(plan.ingress_allowlist),
		"payload_environment": payload.get("environment", {}),
	}
	return json.dumps(runtime_plan, indent=2, sort_keys=True)


def _apply_database_plan(plan: RuntimePlan, settings: RuntimeSettings) -> None:
	sql_path = plan.runtime_dir / "runtime-config" / "provision.sql"
	env = os.environ.copy()
	env["MYSQL_PWD"] = settings.db_root_password
	_run(
		[
			"mysql",
			"--host",
			settings.db_host,
			"--port",
			str(settings.db_port),
			"--user",
			settings.db_root_user,
			"--execute",
			sql_path.read_text(),
		],
		env=env,
	)


def _start_compose_stack(plan: RuntimePlan) -> None:
	_run(["docker", "compose", "up", "-d"], cwd=plan.runtime_dir)


def _bootstrap_site(plan: RuntimePlan) -> None:
	_run(
		[
			"docker",
			"compose",
			"exec",
			"-T",
			"backend",
			"/bin/bash",
			"/workspace/founder_runtime/scripts/init-site.sh",
		],
		cwd=plan.runtime_dir,
	)


def _restore_site(plan: RuntimePlan, backup_export_path: str) -> None:
	_run(
		[
			"bash",
			str(SCRIPTS_DIR / "restore-site.sh"),
			str(plan.runtime_dir),
			backup_export_path,
		],
		cwd=plan.runtime_dir,
	)


def _start_edge_proxy(settings: RuntimeSettings) -> None:
	_require_command("docker")
	_run(["docker", "compose", "up", "-d"], cwd=settings.edge_proxy_root)


def _reload_edge_proxy(settings: RuntimeSettings) -> None:
	if not settings.execute or settings.edge_proxy_mode != "shared_nginx_proxy":
		return
	_run(
		[
			"docker",
			"compose",
			"exec",
			"-T",
			"edge",
			"nginx",
			"-s",
			"reload",
		],
		cwd=settings.edge_proxy_root,
	)


def _remove_edge_proxy_route(project_slug: str, settings: RuntimeSettings) -> None:
	route_path = settings.edge_proxy_root / "conf.d" / f"{project_slug}.conf"
	if route_path.exists():
		route_path.unlink()


def _ensure_dns_record(plan: RuntimePlan, settings: RuntimeSettings) -> int:
	if not plan.primary_domain or not settings.dns_zone or not settings.dns_target_ip:
		return 0

	_require_command("gcloud")
	domain = _fqdn(plan.primary_domain)
	list_command = [
		*_gcloud_base_command(settings),
		"dns",
		"record-sets",
		"list",
		"--zone",
		settings.dns_zone,
		"--name",
		domain,
		"--type",
		"A",
		"--format",
		"value(rrdatas[0])",
	]
	current = _run(list_command).strip()
	if current == settings.dns_target_ip:
		return 1

	start = [
		*_gcloud_base_command(settings),
		"dns",
		"record-sets",
		"transaction",
		"start",
		"--zone",
		settings.dns_zone,
	]
	_run(start)

	if current:
		remove = [
			*_gcloud_base_command(settings),
			"dns",
			"record-sets",
			"transaction",
			"remove",
			"--zone",
			settings.dns_zone,
			"--name",
			domain,
			"--type",
			"A",
			"--ttl",
			str(settings.dns_ttl),
			current,
		]
		_run(remove)

	add = [
		*_gcloud_base_command(settings),
		"dns",
		"record-sets",
		"transaction",
		"add",
		"--zone",
		settings.dns_zone,
		"--name",
		domain,
		"--type",
		"A",
		"--ttl",
		str(settings.dns_ttl),
		settings.dns_target_ip,
	]
	_run(add)
	execute = [
		*_gcloud_base_command(settings),
		"dns",
		"record-sets",
		"transaction",
		"execute",
		"--zone",
		settings.dns_zone,
	]
	_run(execute)
	return 1


def _remove_dns_record(primary_domain: str, settings: RuntimeSettings) -> None:
	if not settings.execute or not settings.dns_zone or not settings.dns_target_ip:
		return

	_require_command("gcloud")
	domain = _fqdn(primary_domain)
	list_command = [
		*_gcloud_base_command(settings),
		"dns",
		"record-sets",
		"list",
		"--zone",
		settings.dns_zone,
		"--name",
		domain,
		"--type",
		"A",
		"--format",
		"value(rrdatas[0])",
	]
	current = _run(list_command).strip()
	if not current:
		return

	_run(
		[
			*_gcloud_base_command(settings),
			"dns",
			"record-sets",
			"transaction",
			"start",
			"--zone",
			settings.dns_zone,
		]
	)
	_run(
		[
			*_gcloud_base_command(settings),
			"dns",
			"record-sets",
			"transaction",
			"remove",
			"--zone",
			settings.dns_zone,
			"--name",
			domain,
			"--type",
			"A",
			"--ttl",
			str(settings.dns_ttl),
			current,
		]
	)
	_run(
		[
			*_gcloud_base_command(settings),
			"dns",
			"record-sets",
			"transaction",
			"execute",
			"--zone",
			settings.dns_zone,
		]
	)


def _routing_mode(
	plan: RuntimePlan,
	settings: RuntimeSettings,
	*,
	dns_ready: int,
	edge_proxy_ready: int,
) -> str:
	if not plan.primary_domain:
		return "Internal Only"
	if (
		settings.edge_proxy_mode == "shared_nginx_proxy"
		and dns_ready
		and edge_proxy_ready
		and settings.execute
	):
		return "Public"
	if settings.edge_proxy_mode in {"manual_host_proxy", "shared_nginx_proxy"}:
		return "Pending"
	return "Public"


def _allocate_http_port(runtime_root: Path, base_port: int) -> int:
	used_ports: set[int] = set()
	for env_file in (runtime_root / ENVIRONMENT_ROOT_NAME).glob("*/.env"):
		values = _read_existing_env(env_file)
		http_port = values.get("HTTP_PORT")
		if http_port and http_port.isdigit():
			used_ports.add(int(http_port))

	port = base_port
	while port in used_ports:
		port += 1
	return port


def _resolve_ingress_access_mode(payload: dict[str, Any]) -> str:
	mode = (
		str(payload.get("environment", {}).get("ingress_access_mode") or "").strip()
		or str(payload.get("policy", {}).get("default_ingress_access_mode") or "").strip()
		or "Public"
	)
	if mode not in {"Public", "Allowlisted", "Disabled"}:
		raise SystemExit(f"Unsupported ingress access mode: {mode}")
	return mode


def _resolve_ingress_allowlist(payload: dict[str, Any], mode: str) -> list[str]:
	rows = payload.get("environment", {}).get("ingress_allowlist") or []
	cidrs = [str(row.get("cidr") or "").strip() for row in rows if str(row.get("cidr") or "").strip()]
	if mode == "Allowlisted" and not cidrs:
		raise SystemExit("Ingress allowlist is required when ingress_access_mode is Allowlisted.")
	return cidrs


def _read_existing_env(path: Path) -> dict[str, str]:
	if not path.exists():
		return {}

	values: dict[str, str] = {}
	for line in path.read_text().splitlines():
		if "=" not in line or line.strip().startswith("#"):
			continue
		key, value = line.split("=", 1)
		values[key.strip()] = value.strip()
	return values


def _validate_firewall_settings(settings: RuntimeSettings) -> None:
	if settings.firewall_enabled and not settings.allowed_ssh_cidrs:
		raise SystemExit(
			"IFITWALA_FOUNDER_RUNTIME_ALLOWED_SSH_CIDRS is required when the founder firewall is enabled."
		)
	if not settings.public_tcp_ports:
		raise SystemExit("IFITWALA_FOUNDER_RUNTIME_PUBLIC_TCP_PORTS must contain at least one TCP port.")
	for port in settings.public_tcp_ports:
		if port < 1 or port > 65535:
			raise SystemExit(f"Invalid founder firewall TCP port: {port}")
	if not settings.firewall_script.is_file():
		raise SystemExit(f"Founder firewall sync script not found: {settings.firewall_script}")


def _run_firewall_sync(settings: RuntimeSettings) -> None:
	command = ["bash", str(settings.firewall_script)]
	if os.geteuid() != 0:
		_require_command("sudo")
		command = ["sudo", "-n", *command]
	_run(command)


def _require_site_name(payload: dict[str, Any]) -> str:
	site_name = str(payload.get("environment", {}).get("site_name") or "").strip()
	if not site_name:
		raise SystemExit("Payload environment.site_name is required.")
	return site_name


def _default_domain(project_slug: str, domain_suffix: str | None) -> str | None:
	if not domain_suffix:
		return None
	return f"{project_slug}.{domain_suffix.strip('.')}"


def _slugify(value: str) -> str:
	text = value.strip().lower().replace(".", "-").replace("_", "-")
	text = SITE_SLUG_PATTERN.sub("-", text).strip("-")
	return text or "site"


def _secret_token() -> str:
	return secrets.token_urlsafe(24)


def _parse_csv_values(raw_value: str | None) -> list[str]:
	if not raw_value:
		return []
	text = raw_value.replace("\n", ",").replace(";", ",").replace(" ", ",")
	return [part.strip() for part in text.split(",") if part.strip()]


def _env(name: str, *, default: str | None = None, required: bool = False) -> str | None:
	value = os.environ.get(name, default)
	if required and (value is None or value == ""):
		raise SystemExit(f"Missing required environment variable: {name}")
	return value


def _require_command(command: str) -> None:
	if shutil.which(command):
		return
	raise SystemExit(f"Required command not found on PATH: {command}")


def _fqdn(domain: str) -> str:
	return domain if domain.endswith(".") else f"{domain}."


def _gcloud_base_command(settings: RuntimeSettings) -> list[str]:
	command = ["gcloud"]
	if settings.gcloud_project:
		command.extend(["--project", settings.gcloud_project])
	return command


def _run(command: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> str:
	result = subprocess.run(
		command,
		cwd=cwd,
		env=env,
		check=False,
		text=True,
		capture_output=True,
	)
	if result.returncode != 0:
		message = (
			result.stderr.strip() or result.stdout.strip() or f"Command failed with code {result.returncode}"
		)
		raise SystemExit(message)
	return result.stdout


if __name__ == "__main__":
	raise SystemExit(main())
