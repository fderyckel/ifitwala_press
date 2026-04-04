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
FOUNDER_RUNTIME_SCRIPTS_DIR = REPO_ROOT / "ops" / "founder_runtime" / "scripts"
FOUNDER_EDGE_PROXY_DIR = REPO_ROOT / "ops" / "founder_runtime" / "edge_proxy"
POOLS_ROOT_NAME = "pools"
EDGE_PROXY_ROOT_NAME = "edge-proxy"
DEFAULT_DB_PORT = 3306
DEFAULT_HTTP_PORT_BASE = 19080
DEFAULT_DNS_TTL = 300
DEFAULT_EDGE_PROXY_MODE = "manual_host_proxy"
SLUG_PATTERN = re.compile(r"[^a-z0-9]+")


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
	execute: bool


@dataclass(frozen=True)
class PoolPlan:
	pool_name: str
	pool_reference: str
	pool_slug: str
	pool_dir: Path
	compose_project_name: str
	http_port: int


@dataclass(frozen=True)
class SitePlan:
	site_name: str
	site_slug: str
	primary_domain: str | None
	host_header_value: str | None
	db_name: str
	db_user: str
	db_password: str
	files_prefix: str
	backups_prefix: str
	backup_export_prefix: str
	file_storage_provider: str
	file_storage_class: str
	backup_storage_provider: str
	backup_storage_class: str
	ingress_access_mode: str
	ingress_allowlist: tuple[str, ...]
	site_manifest_path: Path
	payload_snapshot_path: Path


def main(argv: list[str] | None = None) -> int:
	args = list(argv or sys.argv[1:])
	if len(args) != 1 or args[0] not in {
		"provision-shared-demo-site",
		"sync-shared-demo-edge-route",
		"teardown-shared-demo-site",
		"restore-shared-demo-site",
	}:
		print(
			"Usage: adapter.py [provision-shared-demo-site|sync-shared-demo-edge-route|teardown-shared-demo-site|restore-shared-demo-site]",
			file=sys.stderr,
		)
		return 2

	payload = _load_payload()
	settings = _load_settings()
	pool_plan = _build_pool_plan(payload, settings)
	site_plan = _build_site_plan(payload, settings, pool_plan)

	if args[0] == "provision-shared-demo-site":
		result = provision_shared_demo_site(payload, settings, pool_plan, site_plan)
	elif args[0] == "sync-shared-demo-edge-route":
		result = sync_shared_demo_edge_route(payload, settings, pool_plan, site_plan)
	elif args[0] == "restore-shared-demo-site":
		result = restore_shared_demo_site(payload, settings, pool_plan, site_plan)
	else:
		result = teardown_shared_demo_site(payload, settings, pool_plan, site_plan)

	print(json.dumps(result))
	return 0


def provision_shared_demo_site(
	payload: dict[str, Any],
	settings: RuntimeSettings,
	pool_plan: PoolPlan,
	site_plan: SitePlan,
) -> dict[str, Any]:
	_render_pool_assets(pool_plan, site_plan, payload, settings)

	last_step = "Shared runtime pool assets rendered"
	message = "Shared runtime pool assets rendered. Execution not requested."
	dns_ready = 0
	edge_proxy_ready = 0

	if settings.edge_proxy_mode == "shared_nginx_proxy" and site_plan.primary_domain:
		_prepare_edge_proxy(site_plan, pool_plan, settings)
		edge_proxy_ready = 1

	if settings.execute:
		_require_command("docker")
		_start_pool_stack(pool_plan)
		last_step = "Shared runtime pool stack started"
		_bootstrap_site(pool_plan, site_plan, settings)
		last_step = "Shared demo site bootstrapped"
		if settings.edge_proxy_mode == "shared_nginx_proxy" and site_plan.primary_domain:
			_start_edge_proxy(settings)
			_reload_edge_proxy(settings)
			last_step = "Shared edge proxy route ensured"
		dns_ready = _ensure_dns_record(site_plan.primary_domain, settings)
		last_step = "Cloud DNS ensured" if dns_ready else last_step
		message = "Shared demo site provisioned on the runtime pool."

	return _build_result(
		payload,
		settings,
		pool_plan,
		site_plan,
		dns_ready=dns_ready,
		edge_proxy_ready=edge_proxy_ready,
		last_step=last_step,
		message=message,
		status_reason="Shared demo site scaffolded on a runtime pool.",
	)


def sync_shared_demo_edge_route(
	payload: dict[str, Any],
	settings: RuntimeSettings,
	pool_plan: PoolPlan,
	site_plan: SitePlan,
) -> dict[str, Any]:
	if settings.edge_proxy_mode != "shared_nginx_proxy":
		return _build_result(
			payload,
			settings,
			pool_plan,
			site_plan,
			dns_ready=0,
			edge_proxy_ready=0,
			last_step="Shared edge route sync skipped",
			message="Shared edge route sync requires IFITWALA_SHARED_DEMO_BENCH_EDGE_PROXY_MODE=shared_nginx_proxy.",
			status_reason="Shared edge proxy is not enabled for this runtime pool.",
		)

	if not site_plan.primary_domain:
		return _build_result(
			payload,
			settings,
			pool_plan,
			site_plan,
			dns_ready=0,
			edge_proxy_ready=0,
			last_step="Shared edge route sync skipped",
			message="Primary domain is required before the shared edge route can be synced.",
			status_reason="Primary domain missing for shared edge route sync.",
		)

	_prepare_edge_proxy(site_plan, pool_plan, settings)
	if settings.execute:
		_start_edge_proxy(settings)
		_reload_edge_proxy(settings)

	return _build_result(
		payload,
		settings,
		pool_plan,
		site_plan,
		dns_ready=0,
		edge_proxy_ready=1,
		last_step="Shared edge route synced",
		message=(
			"Shared edge route rendered and nginx reloaded."
			if settings.execute
			else "Shared edge route rendered. Execution not requested."
		),
		status_reason="Shared edge route synced from runtime-pool placement.",
	)


def teardown_shared_demo_site(
	payload: dict[str, Any],
	settings: RuntimeSettings,
	pool_plan: PoolPlan,
	site_plan: SitePlan,
) -> dict[str, Any]:
	backup_export_path = (
		str(payload.get("environment", {}).get("backup_export_path") or "").strip()
		or site_plan.backup_export_prefix
	)
	last_step = "Shared demo site teardown planned"
	message = "Shared demo site teardown planned. Execution not requested."

	if settings.execute:
		_require_command("docker")
		_require_command("gcloud")
		_require_command("jq")
		backup_export_path = _backup_site(pool_plan, site_plan)
		_remove_edge_proxy_route(site_plan.site_slug, settings)
		_reload_edge_proxy(settings)
		_remove_dns_record(site_plan.primary_domain, settings)
		_drop_site(pool_plan, site_plan, settings)
		last_step = "Shared demo site removed"
		message = "Shared demo site removed after backup export."

	return _build_result(
		payload,
		settings,
		pool_plan,
		site_plan,
		dns_ready=0,
		edge_proxy_ready=0,
		last_step=last_step,
		message=message,
		status_reason="Shared demo site teardown prepared.",
		override_backup_export_path=backup_export_path,
	)


def restore_shared_demo_site(
	payload: dict[str, Any],
	settings: RuntimeSettings,
	pool_plan: PoolPlan,
	site_plan: SitePlan,
) -> dict[str, Any]:
	backup_export_path = (
		str(payload.get("environment", {}).get("backup_export_path") or "").strip()
		or site_plan.backup_export_prefix
	)
	last_step = "Shared demo site restore planned"
	message = "Shared demo site restore planned. Execution not requested."
	dns_ready = 0
	edge_proxy_ready = 0

	if settings.edge_proxy_mode == "shared_nginx_proxy" and site_plan.primary_domain:
		_prepare_edge_proxy(site_plan, pool_plan, settings)
		edge_proxy_ready = 1

	if settings.execute:
		_require_command("docker")
		_require_command("gcloud")
		_require_command("jq")
		_restore_site(pool_plan, site_plan, backup_export_path)
		last_step = "Shared demo site restore completed"
		if settings.edge_proxy_mode == "shared_nginx_proxy" and site_plan.primary_domain:
			_start_edge_proxy(settings)
			_reload_edge_proxy(settings)
			last_step = "Shared edge proxy route ensured"
		dns_ready = _ensure_dns_record(site_plan.primary_domain, settings)
		last_step = "Cloud DNS ensured" if dns_ready else last_step
		message = "Shared demo site restored from exported backup."

	result = _build_result(
		payload,
		settings,
		pool_plan,
		site_plan,
		dns_ready=dns_ready,
		edge_proxy_ready=edge_proxy_ready,
		last_step=last_step,
		message=message,
		status_reason="Shared demo site restore prepared.",
		override_backup_export_path=backup_export_path,
	)
	result["restored_backup_manifest"] = f"{backup_export_path.rstrip('/')}/manifest-latest.json"
	result["db_restore_tested_on"] = date.today().isoformat() if settings.execute else None
	return result


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
	runtime_root = Path(_env("IFITWALA_SHARED_DEMO_BENCH_ROOT", required=True)).expanduser()
	return RuntimeSettings(
		runtime_root=runtime_root,
		runtime_image=_env("IFITWALA_SHARED_DEMO_BENCH_IMAGE", required=True),
		db_host=_env("IFITWALA_SHARED_DEMO_BENCH_DB_HOST", required=True),
		db_port=int(_env("IFITWALA_SHARED_DEMO_BENCH_DB_PORT", default=str(DEFAULT_DB_PORT))),
		db_root_user=_env("IFITWALA_SHARED_DEMO_BENCH_DB_ROOT_USER", required=True),
		db_root_password=_env("IFITWALA_SHARED_DEMO_BENCH_DB_ROOT_PASSWORD", required=True),
		admin_password=_env("IFITWALA_SHARED_DEMO_BENCH_ADMIN_PASSWORD", required=True),
		gcs_files_bucket=_env("IFITWALA_SHARED_DEMO_BENCH_GCS_FILES_BUCKET", required=True),
		gcs_backups_bucket=_env("IFITWALA_SHARED_DEMO_BENCH_GCS_BACKUPS_BUCKET", required=True),
		domain_suffix=_env("IFITWALA_SHARED_DEMO_BENCH_DOMAIN_SUFFIX", default=None),
		dns_zone=_env("IFITWALA_SHARED_DEMO_BENCH_DNS_ZONE", default=None),
		dns_target_ip=_env("IFITWALA_SHARED_DEMO_BENCH_DNS_TARGET_IP", default=None),
		dns_ttl=int(_env("IFITWALA_SHARED_DEMO_BENCH_DNS_TTL", default=str(DEFAULT_DNS_TTL))),
		gcloud_project=_env("IFITWALA_SHARED_DEMO_BENCH_GCLOUD_PROJECT", default=None),
		edge_proxy_mode=_env("IFITWALA_SHARED_DEMO_BENCH_EDGE_PROXY_MODE", default=DEFAULT_EDGE_PROXY_MODE),
		edge_proxy_root=Path(
			_env(
				"IFITWALA_SHARED_DEMO_BENCH_EDGE_PROXY_ROOT",
				default=str(runtime_root / EDGE_PROXY_ROOT_NAME),
			)
		).expanduser(),
		http_port_base=int(
			_env("IFITWALA_SHARED_DEMO_BENCH_HTTP_PORT_BASE", default=str(DEFAULT_HTTP_PORT_BASE))
		),
		execute=_env("IFITWALA_SHARED_DEMO_BENCH_EXECUTE", default="0") == "1",
	)


def _build_pool_plan(payload: dict[str, Any], settings: RuntimeSettings) -> PoolPlan:
	runtime_pool = payload.get("runtime_pool") or {}
	pool_name = str(runtime_pool.get("pool_name") or runtime_pool.get("name") or "").strip()
	pool_reference = str(runtime_pool.get("pool_reference") or runtime_pool.get("name") or "").strip()
	if not pool_reference:
		raise SystemExit("Runtime pool payload is required for the shared demo bench adapter.")

	pool_slug = _slugify(pool_reference)
	pool_dir = settings.runtime_root / POOLS_ROOT_NAME / pool_slug
	existing_env = _read_existing_env(pool_dir / ".env")
	http_port = int(
		existing_env.get("HTTP_PORT") or _allocate_http_port(settings.runtime_root, settings.http_port_base)
	)

	return PoolPlan(
		pool_name=pool_name or pool_reference,
		pool_reference=pool_reference,
		pool_slug=pool_slug,
		pool_dir=pool_dir,
		compose_project_name=existing_env.get("COMPOSE_PROJECT_NAME") or f"ifw-bench-{pool_slug}",
		http_port=http_port,
	)


def _build_site_plan(payload: dict[str, Any], settings: RuntimeSettings, pool_plan: PoolPlan) -> SitePlan:
	environment = payload.get("environment", {})
	site_name = _require_site_name(payload)
	site_slug = _slugify(site_name)
	site_manifest_path = pool_plan.pool_dir / "runtime-config" / "sites" / f"{site_slug}.json"
	existing_site = _read_json(site_manifest_path)
	primary_domain = (
		environment.get("primary_domain")
		or existing_site.get("primary_domain")
		or _default_domain(site_slug, settings.domain_suffix)
	)
	db_name = (
		environment.get("db_name") or existing_site.get("db_name") or f"site_{site_slug.replace('-', '_')}"
	)
	db_user = (
		environment.get("db_user") or existing_site.get("db_user") or f"user_{site_slug.replace('-', '_')}"
	)
	db_password = existing_site.get("db_password") or _secret_token()
	ingress_access_mode = _resolve_ingress_access_mode(payload)
	ingress_allowlist = tuple(_resolve_ingress_allowlist(payload, ingress_access_mode))

	return SitePlan(
		site_name=site_name,
		site_slug=site_slug,
		primary_domain=primary_domain,
		host_header_value=primary_domain,
		db_name=db_name,
		db_user=db_user,
		db_password=db_password,
		files_prefix=f"sites/{site_name}/files/",
		backups_prefix=f"sites/{site_name}/daily/",
		backup_export_prefix=f"gs://{settings.gcs_backups_bucket}/sites/{site_name}/daily/",
		file_storage_provider=environment.get("file_storage_provider") or "GCS",
		file_storage_class=environment.get("file_storage_class") or "Frequent Access",
		backup_storage_provider=environment.get("backup_storage_provider") or "GCS",
		backup_storage_class=environment.get("backup_storage_class") or "Infrequent Access",
		ingress_access_mode=ingress_access_mode,
		ingress_allowlist=ingress_allowlist,
		site_manifest_path=site_manifest_path,
		payload_snapshot_path=pool_plan.pool_dir / "runtime-config" / "payloads" / f"{site_slug}.json",
	)


def _render_pool_assets(
	pool_plan: PoolPlan,
	site_plan: SitePlan,
	payload: dict[str, Any],
	settings: RuntimeSettings,
) -> None:
	pool_plan.pool_dir.mkdir(parents=True, exist_ok=True)
	(pool_plan.pool_dir / "logs").mkdir(exist_ok=True)
	(pool_plan.pool_dir / "sites").mkdir(exist_ok=True)
	(pool_plan.pool_dir / "nginx").mkdir(exist_ok=True)
	(pool_plan.pool_dir / "runtime-config").mkdir(exist_ok=True)
	(pool_plan.pool_dir / "runtime-config" / "sites").mkdir(exist_ok=True)
	(pool_plan.pool_dir / "runtime-config" / "payloads").mkdir(exist_ok=True)

	(pool_plan.pool_dir / "compose.yaml").write_text((TEMPLATES_DIR / "compose.yaml").read_text())
	(pool_plan.pool_dir / "nginx" / "default.conf").write_text(
		(TEMPLATES_DIR / "nginx-default.conf").read_text()
	)
	(pool_plan.pool_dir / ".env").write_text(_render_env(pool_plan, settings))
	(pool_plan.pool_dir / "sites" / "common_site_config.json").write_text(
		_render_common_site_config(settings)
	)
	site_plan.site_manifest_path.write_text(_render_site_manifest(site_plan, pool_plan, payload))
	site_plan.payload_snapshot_path.write_text(json.dumps(payload, indent=2, sort_keys=True))


def _render_env(pool_plan: PoolPlan, settings: RuntimeSettings) -> str:
	return "\n".join(
		[
			f"COMPOSE_PROJECT_NAME={pool_plan.compose_project_name}",
			f"RUNTIME_IMAGE={settings.runtime_image}",
			f"HTTP_PORT={pool_plan.http_port}",
			f"FOUNDER_RUNTIME_SCRIPTS_DIR={FOUNDER_RUNTIME_SCRIPTS_DIR}",
			f"SHARED_DEMO_BENCH_SCRIPTS_DIR={SCRIPTS_DIR}",
			f"DB_HOST={settings.db_host}",
			f"DB_PORT={settings.db_port}",
			f"DB_ROOT_USER={settings.db_root_user}",
			f"DB_ROOT_PASSWORD={settings.db_root_password}",
			f"ADMIN_PASSWORD={settings.admin_password}",
			"REDIS_CACHE_URL=redis://redis-cache:6379",
			"REDIS_QUEUE_URL=redis://redis-queue:6379",
			"REDIS_SOCKETIO_URL=redis://redis-socketio:6379",
			f"GCS_PROJECT={settings.gcloud_project or ''}",
			f"GCS_FILES_BUCKET={settings.gcs_files_bucket}",
			f"GCS_BACKUPS_BUCKET={settings.gcs_backups_bucket}",
			"",
		]
	)


def _render_common_site_config(settings: RuntimeSettings) -> str:
	config = {
		"db_host": settings.db_host,
		"db_port": settings.db_port,
		"redis_cache": "redis://redis-cache:6379",
		"redis_queue": "redis://redis-queue:6379",
		"redis_socketio": "redis://redis-socketio:6379",
		"webserver_port": 8000,
		"socketio_port": 9000,
		"gcs_project": settings.gcloud_project,
		"gcs_files_bucket": settings.gcs_files_bucket,
		"gcs_backups_bucket": settings.gcs_backups_bucket,
		"approved_apps": ["frappe", "ifitwala_ed", "ifitwala_drive"],
	}
	return json.dumps(config, indent=2, sort_keys=True)


def _render_site_manifest(site_plan: SitePlan, pool_plan: PoolPlan, payload: dict[str, Any]) -> str:
	manifest = {
		"site_name": site_plan.site_name,
		"site_slug": site_plan.site_slug,
		"pool_reference": pool_plan.pool_reference,
		"primary_domain": site_plan.primary_domain,
		"host_header_value": site_plan.host_header_value,
		"db_name": site_plan.db_name,
		"db_user": site_plan.db_user,
		"db_password": site_plan.db_password,
		"files_prefix": site_plan.files_prefix,
		"backups_prefix": site_plan.backups_prefix,
		"backup_export_path": site_plan.backup_export_prefix,
		"file_storage_provider": site_plan.file_storage_provider,
		"file_storage_class": site_plan.file_storage_class,
		"backup_storage_provider": site_plan.backup_storage_provider,
		"backup_storage_class": site_plan.backup_storage_class,
		"runtime_reference": _runtime_reference(pool_plan, site_plan),
		"payload_environment": payload.get("environment", {}),
	}
	return json.dumps(manifest, indent=2, sort_keys=True)


def _prepare_edge_proxy(site_plan: SitePlan, pool_plan: PoolPlan, settings: RuntimeSettings) -> None:
	settings.edge_proxy_root.mkdir(parents=True, exist_ok=True)
	(settings.edge_proxy_root / "conf.d").mkdir(exist_ok=True)
	(settings.edge_proxy_root / "compose.yaml").write_text(
		(FOUNDER_EDGE_PROXY_DIR / "compose.yaml").read_text()
	)
	(settings.edge_proxy_root / "nginx.conf").write_text((FOUNDER_EDGE_PROXY_DIR / "nginx.conf").read_text())
	(settings.edge_proxy_root / "conf.d" / f"{site_plan.site_slug}.conf").write_text(
		_render_edge_proxy_route(site_plan, pool_plan)
	)


def _render_edge_proxy_route(site_plan: SitePlan, pool_plan: PoolPlan) -> str:
	template = Template((FOUNDER_EDGE_PROXY_DIR / "route.conf.template").read_text())
	return template.substitute(
		SITE_DOMAIN=site_plan.primary_domain or "_",
		UPSTREAM_PORT=str(pool_plan.http_port),
		SERVER_ACCESS_DIRECTIVES="",
		LOCATION_ACCESS_DIRECTIVES=_render_location_access_directives(site_plan),
		LOCATION_BEHAVIOR_DIRECTIVES=_render_location_behavior_directives(site_plan),
	)


def _render_location_access_directives(site_plan: SitePlan) -> str:
	if site_plan.ingress_access_mode != "Allowlisted":
		return ""

	indent = " " * 8
	lines = [f"{indent}allow {cidr};" for cidr in site_plan.ingress_allowlist]
	lines.append(f"{indent}deny all;")
	return "\n".join(lines) + "\n"


def _render_location_behavior_directives(site_plan: SitePlan) -> str:
	if site_plan.ingress_access_mode != "Disabled":
		return ""
	return "        return 403;\n"


def _start_pool_stack(pool_plan: PoolPlan) -> None:
	_run(["docker", "compose", "up", "-d"], cwd=pool_plan.pool_dir)


def _bootstrap_site(pool_plan: PoolPlan, site_plan: SitePlan, settings: RuntimeSettings) -> None:
	_run(
		[
			"docker",
			"compose",
			"exec",
			"-T",
			"-e",
			f"SITE_NAME={site_plan.site_name}",
			"-e",
			f"DB_HOST={settings.db_host}",
			"-e",
			f"DB_PORT={settings.db_port}",
			"-e",
			f"DB_NAME={site_plan.db_name}",
			"-e",
			f"DB_USER={site_plan.db_user}",
			"-e",
			f"DB_PASSWORD={site_plan.db_password}",
			"-e",
			f"DB_ROOT_USER={settings.db_root_user}",
			"-e",
			f"DB_ROOT_PASSWORD={settings.db_root_password}",
			"-e",
			f"ADMIN_PASSWORD={settings.admin_password}",
			"-e",
			f"SITE_DOMAIN={site_plan.primary_domain or ''}",
			"-e",
			f"FILE_STORAGE_PROVIDER={site_plan.file_storage_provider}",
			"-e",
			f"FILE_STORAGE_CLASS={site_plan.file_storage_class}",
			"-e",
			f"BACKUP_STORAGE_PROVIDER={site_plan.backup_storage_provider}",
			"-e",
			f"BACKUP_STORAGE_CLASS={site_plan.backup_storage_class}",
			"-e",
			f"GCS_PROJECT={settings.gcloud_project or ''}",
			"-e",
			f"GCS_FILES_BUCKET={settings.gcs_files_bucket}",
			"-e",
			f"GCS_FILES_PREFIX={site_plan.files_prefix}",
			"-e",
			f"GCS_BACKUPS_BUCKET={settings.gcs_backups_bucket}",
			"-e",
			f"GCS_BACKUPS_PREFIX={site_plan.backups_prefix}",
			"backend",
			"/bin/bash",
			"/workspace/shared_demo_bench/scripts/provision-site.sh",
		],
		cwd=pool_plan.pool_dir,
	)


def _backup_site(pool_plan: PoolPlan, site_plan: SitePlan) -> str:
	return _run(
		["bash", str(SCRIPTS_DIR / "backup-site.sh"), str(pool_plan.pool_dir), site_plan.site_name],
		cwd=pool_plan.pool_dir,
	).strip()


def _restore_site(pool_plan: PoolPlan, site_plan: SitePlan, backup_export_path: str) -> None:
	_run(
		[
			"bash",
			str(SCRIPTS_DIR / "restore-site.sh"),
			str(pool_plan.pool_dir),
			site_plan.site_name,
			backup_export_path,
		],
		cwd=pool_plan.pool_dir,
	)


def _drop_site(pool_plan: PoolPlan, site_plan: SitePlan, settings: RuntimeSettings) -> None:
	site_dir = pool_plan.pool_dir / "sites" / site_plan.site_name
	if site_dir.exists():
		shutil.rmtree(site_dir)

	site_manifest = _read_json(site_plan.site_manifest_path)
	db_name = str(site_manifest.get("db_name") or site_plan.db_name)
	db_user = str(site_manifest.get("db_user") or site_plan.db_user)
	_run_mysql(
		settings,
		[
			f"DROP DATABASE IF EXISTS `{db_name}`;",
			f"DROP USER IF EXISTS '{db_user}'@'%';",
			"FLUSH PRIVILEGES;",
		],
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


def _remove_edge_proxy_route(site_slug: str, settings: RuntimeSettings) -> None:
	route_path = settings.edge_proxy_root / "conf.d" / f"{site_slug}.conf"
	if route_path.exists():
		route_path.unlink()


def _ensure_dns_record(primary_domain: str | None, settings: RuntimeSettings) -> int:
	if not primary_domain or not settings.dns_zone or not settings.dns_target_ip:
		return 0

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
	if current == settings.dns_target_ip:
		return 1

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

	if current:
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
	return 1


def _remove_dns_record(primary_domain: str | None, settings: RuntimeSettings) -> None:
	if not settings.execute or not primary_domain or not settings.dns_zone:
		return

	_require_command("gcloud")
	domain = _fqdn(primary_domain)
	current = _run(
		[
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
	).strip()
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


def _build_result(
	payload: dict[str, Any],
	settings: RuntimeSettings,
	pool_plan: PoolPlan,
	site_plan: SitePlan,
	*,
	dns_ready: int,
	edge_proxy_ready: int,
	last_step: str,
	message: str,
	status_reason: str,
	override_backup_export_path: str | None = None,
) -> dict[str, Any]:
	environment = payload.get("environment", {})
	return {
		"site_name": site_plan.site_name,
		"primary_domain": site_plan.primary_domain,
		"routing_mode": _routing_mode(
			site_plan,
			settings,
			dns_ready=dns_ready,
			edge_proxy_ready=edge_proxy_ready,
		),
		"dns_ready": dns_ready,
		"tls_ready": 0,
		"host_header_value": site_plan.host_header_value,
		"db_name": site_plan.db_name,
		"db_user": site_plan.db_user,
		"provisioning_job_id": pool_plan.compose_project_name,
		"last_provisioning_step": last_step,
		"provisioning_message": message,
		"runtime_reference": _runtime_reference(pool_plan, site_plan),
		"file_storage_provider": environment.get("file_storage_provider") or site_plan.file_storage_provider,
		"file_storage_class": environment.get("file_storage_class") or site_plan.file_storage_class,
		"backup_storage_provider": environment.get("backup_storage_provider")
		or site_plan.backup_storage_provider,
		"backup_storage_class": environment.get("backup_storage_class") or site_plan.backup_storage_class,
		"backup_export_path": override_backup_export_path or site_plan.backup_export_prefix,
		"status_reason": status_reason,
	}


def _routing_mode(
	site_plan: SitePlan,
	settings: RuntimeSettings,
	*,
	dns_ready: int,
	edge_proxy_ready: int,
) -> str:
	if not site_plan.primary_domain:
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


def _runtime_reference(pool_plan: PoolPlan, site_plan: SitePlan) -> str:
	return f"bench:{pool_plan.pool_reference}:site:{site_plan.site_name}"


def _allocate_http_port(runtime_root: Path, base_port: int) -> int:
	used_ports: set[int] = set()
	for env_file in (runtime_root / POOLS_ROOT_NAME).glob("*/.env"):
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


def _run_mysql(settings: RuntimeSettings, statements: list[str]) -> None:
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
			"\n".join(statements),
		],
		env=env,
	)


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


def _read_json(path: Path) -> dict[str, Any]:
	if not path.exists():
		return {}
	try:
		parsed = json.loads(path.read_text())
	except json.JSONDecodeError as exc:
		raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc
	if not isinstance(parsed, dict):
		raise SystemExit(f"Expected {path} to contain a JSON object.")
	return parsed


def _slugify(value: str) -> str:
	text = SLUG_PATTERN.sub("-", value.strip().lower()).strip("-")
	return text or "runtime-pool"


def _default_domain(slug: str, domain_suffix: str | None) -> str | None:
	if not domain_suffix:
		return None
	return f"{slug}.{domain_suffix.lstrip('.')}"


def _fqdn(value: str) -> str:
	return value if value.endswith(".") else f"{value}."


def _secret_token() -> str:
	return secrets.token_urlsafe(24)


def _gcloud_base_command(settings: RuntimeSettings) -> list[str]:
	base = ["gcloud"]
	if settings.gcloud_project:
		base.extend(["--project", settings.gcloud_project])
	return base


def _env(name: str, *, required: bool = False, default: str | None = None) -> str | None:
	value = os.environ.get(name, default)
	if required and (value is None or str(value).strip() == ""):
		raise SystemExit(f"Missing required environment variable: {name}")
	return value.strip() if isinstance(value, str) else value


def _require_site_name(payload: dict[str, Any]) -> str:
	site_name = str(payload.get("environment", {}).get("site_name") or "").strip()
	if not site_name:
		raise SystemExit("Environment site_name is required.")
	return site_name


def _require_command(command: str) -> None:
	if shutil.which(command):
		return
	raise SystemExit(f"Missing required command: {command}")


def _run(
	command: list[str],
	*,
	cwd: Path | None = None,
	env: dict[str, str] | None = None,
) -> str:
	result = subprocess.run(
		command,
		cwd=str(cwd) if cwd else None,
		env=env,
		text=True,
		capture_output=True,
		check=False,
	)
	if result.returncode != 0:
		message = result.stderr.strip() or result.stdout.strip() or "command failed"
		raise SystemExit(message)
	return result.stdout


if __name__ == "__main__":
	raise SystemExit(main())
