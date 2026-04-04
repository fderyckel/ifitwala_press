from __future__ import annotations

from typing import Any

import frappe
from frappe.model.document import Document

SHARED_RUNTIME = "Shared Runtime"
RESERVED_RUNTIME = "Reserved Runtime"
DEDICATED_RUNTIME = "Dedicated Runtime"
AUTO_DRAINING_STATUSES = {"Draining", "Full", "Disabled"}
SHARED_RUNTIME_POOL = "Shared Runtime Pool"
RESERVED_RUNTIME_POOL = "Reserved Runtime Pool"
DEDICATED_RUNTIME_TARGET = "Dedicated Runtime Target"
DEDICATED_RUNTIME_AND_DB = "Dedicated Runtime + DB"


def assign_runtime_placement(
	environment: Document,
	*,
	tenant: Document | None = None,
	policy: Document | None = None,
) -> None:
	selected_pool = _get_selected_runtime_pool(environment)
	environment.deployment_mode = _resolve_deployment_mode(environment, policy, selected_pool)

	if environment.deployment_mode in {SHARED_RUNTIME, RESERVED_RUNTIME}:
		selected_pool = selected_pool or select_runtime_pool(
			deployment_mode=environment.deployment_mode,
			runtime_provider=getattr(environment, "runtime_provider", None),
			primary_cloud_provider=getattr(environment, "primary_cloud_provider", None),
			region=getattr(environment, "region", None),
		)
		environment.runtime_pool = selected_pool.name
		environment.dedicated_runtime_target = ""
		_apply_runtime_pool_defaults(environment, selected_pool)
	else:
		environment.runtime_pool = ""

	environment.placement_strategy = derive_placement_strategy(environment)


def select_runtime_pool(
	*,
	deployment_mode: str,
	runtime_provider: str | None = None,
	primary_cloud_provider: str | None = None,
	region: str | None = None,
) -> Any:
	candidates = frappe.get_all(
		"Runtime Pool",
		filters={
			"pool_mode": deployment_mode,
			"is_active": 1,
		},
		fields=[
			"name",
			"pool_name",
			"pool_mode",
			"pool_status",
			"orchestrator_type",
			"primary_cloud_provider",
			"runtime_provider",
			"region",
			"pool_reference",
			"site_capacity",
			"assigned_site_count",
		],
	)

	eligible = [
		pool
		for pool in candidates
		if _is_pool_eligible(
			pool,
			runtime_provider=runtime_provider,
			primary_cloud_provider=primary_cloud_provider,
			region=region,
		)
	]

	if not eligible:
		frappe.throw(
			_build_no_pool_message(
				deployment_mode=deployment_mode,
				runtime_provider=runtime_provider,
				primary_cloud_provider=primary_cloud_provider,
				region=region,
			)
		)

	selected = sorted(eligible, key=_pool_sort_key)[0]
	return frappe.get_doc("Runtime Pool", _field(selected, "name"))


def derive_placement_strategy(environment: Document) -> str:
	deployment_mode = str(getattr(environment, "deployment_mode", "") or "").strip()
	database_mode = str(getattr(environment, "database_mode", "") or "").strip()

	if deployment_mode == SHARED_RUNTIME:
		return SHARED_RUNTIME_POOL
	if deployment_mode == RESERVED_RUNTIME:
		return RESERVED_RUNTIME_POOL
	if deployment_mode == DEDICATED_RUNTIME and database_mode == "Dedicated DB Instance":
		return DEDICATED_RUNTIME_AND_DB
	if deployment_mode == DEDICATED_RUNTIME:
		return DEDICATED_RUNTIME_TARGET
	return str(getattr(environment, "placement_strategy", "") or "").strip()


def _resolve_deployment_mode(
	environment: Document, policy: Document | None, selected_pool: Any | None
) -> str:
	deployment_mode = str(getattr(environment, "deployment_mode", "") or "").strip()
	if deployment_mode:
		return deployment_mode

	if selected_pool and getattr(selected_pool, "pool_mode", None):
		return str(_field(selected_pool, "pool_mode"))

	if str(getattr(environment, "dedicated_runtime_target", "") or "").strip():
		return DEDICATED_RUNTIME

	policy_mode = str(getattr(policy, "default_deployment_mode", "") or "").strip()
	if policy_mode:
		return policy_mode

	if str(getattr(environment, "hosting_tier", "") or "").strip() == "VIP":
		return DEDICATED_RUNTIME

	return SHARED_RUNTIME


def _get_selected_runtime_pool(environment: Document) -> Any | None:
	runtime_pool_name = str(getattr(environment, "runtime_pool", "") or "").strip()
	if not runtime_pool_name:
		return None
	return frappe.get_doc("Runtime Pool", runtime_pool_name)


def _apply_runtime_pool_defaults(environment: Document, runtime_pool: Any) -> None:
	if not getattr(environment, "region", None) and getattr(runtime_pool, "region", None):
		environment.region = _field(runtime_pool, "region")

	if not getattr(environment, "primary_cloud_provider", None) and getattr(
		runtime_pool, "primary_cloud_provider", None
	):
		environment.primary_cloud_provider = _field(runtime_pool, "primary_cloud_provider")

	if not getattr(environment, "runtime_provider", None) and getattr(runtime_pool, "runtime_provider", None):
		environment.runtime_provider = _field(runtime_pool, "runtime_provider")


def _is_pool_eligible(
	pool: Any,
	*,
	runtime_provider: str | None,
	primary_cloud_provider: str | None,
	region: str | None,
) -> bool:
	if str(_field(pool, "pool_status") or "").strip() in AUTO_DRAINING_STATUSES:
		return False

	pool_runtime_provider = str(_field(pool, "runtime_provider") or "").strip()
	if runtime_provider and pool_runtime_provider and pool_runtime_provider != runtime_provider:
		return False

	pool_primary_cloud_provider = str(_field(pool, "primary_cloud_provider") or "").strip()
	if (
		primary_cloud_provider
		and pool_primary_cloud_provider
		and pool_primary_cloud_provider != primary_cloud_provider
	):
		return False

	pool_region = str(_field(pool, "region") or "").strip()
	if region and pool_region and pool_region != region:
		return False

	site_capacity = _to_int(_field(pool, "site_capacity"))
	assigned_site_count = _to_int(_field(pool, "assigned_site_count")) or 0
	if site_capacity is not None and assigned_site_count >= site_capacity:
		return False

	return True


def _pool_sort_key(pool: Any) -> tuple[int, int, float, int, str]:
	orchestrator = str(_field(pool, "orchestrator_type") or "").strip()
	assigned = _to_int(_field(pool, "assigned_site_count")) or 0
	capacity = _to_int(_field(pool, "site_capacity"))

	if capacity in (None, 0):
		utilization = 2.0
		capacity_missing = 1
	else:
		utilization = assigned / capacity
		capacity_missing = 0

		return (
			0 if orchestrator == "Bench" else 1,
			capacity_missing,
			utilization,
			assigned,
			str(_field(pool, "pool_name") or _field(pool, "name") or ""),
		)


def _build_no_pool_message(
	*,
	deployment_mode: str,
	runtime_provider: str | None,
	primary_cloud_provider: str | None,
	region: str | None,
) -> str:
	parts = [f"No eligible Runtime Pool is available for {deployment_mode} placement"]
	if region:
		parts.append(f"in {region}")
	if runtime_provider:
		parts.append(f"on runtime provider {runtime_provider}")
	if primary_cloud_provider:
		parts.append(f"with primary cloud {primary_cloud_provider}")
	return " ".join(parts) + "."


def _to_int(value: Any) -> int | None:
	if value in (None, ""):
		return None
	return int(value)


def _field(value: Any, fieldname: str) -> Any:
	if isinstance(value, dict):
		return value.get(fieldname)
	return getattr(value, fieldname, None)
