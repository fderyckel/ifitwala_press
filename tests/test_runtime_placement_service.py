from __future__ import annotations

import importlib
import sys
from types import ModuleType, SimpleNamespace

import pytest


def _load_runtime_placement_module(
	monkeypatch: pytest.MonkeyPatch,
	*,
	runtime_pools: dict[str, object] | None = None,
	pool_rows: list[dict[str, object]] | None = None,
):
	fake_frappe = ModuleType("frappe")

	def _throw(message: str) -> None:
		raise RuntimeError(message)

	fake_frappe.throw = _throw  # type: ignore[attr-defined]
	runtime_pools = runtime_pools or {}
	pool_rows = pool_rows or []

	def _get_doc(doctype: str, name: str):
		if doctype == "Runtime Pool":
			if name not in runtime_pools:
				raise RuntimeError(f"Missing runtime pool fixture: {name}")
			return runtime_pools[name]
		raise RuntimeError(f"Unexpected get_doc lookup: {doctype} {name}")

	def _get_all(doctype: str, **kwargs):
		if doctype != "Runtime Pool":
			raise RuntimeError(f"Unexpected get_all lookup: {doctype}")
		return pool_rows

	fake_frappe.get_doc = _get_doc  # type: ignore[attr-defined]
	fake_frappe.get_all = _get_all  # type: ignore[attr-defined]
	fake_model = ModuleType("frappe.model")
	fake_document = ModuleType("frappe.model.document")
	fake_document.Document = object  # type: ignore[attr-defined]

	monkeypatch.setitem(sys.modules, "frappe", fake_frappe)
	monkeypatch.setitem(sys.modules, "frappe.model", fake_model)
	monkeypatch.setitem(sys.modules, "frappe.model.document", fake_document)
	sys.modules.pop("ifitwala_press.ifitwala_press.services.runtime_placement_service", None)
	return importlib.import_module("ifitwala_press.ifitwala_press.services.runtime_placement_service")


def test_assign_runtime_placement_auto_selects_shared_pool(monkeypatch: pytest.MonkeyPatch) -> None:
	pool_doc = SimpleNamespace(
		name="POOL-A",
		pool_name="Pool A",
		pool_mode="Shared Runtime",
		pool_status="Active",
		orchestrator_type="Bench",
		primary_cloud_provider="Google Cloud",
		runtime_provider="Google Cloud",
		region="us-central1",
	)
	module = _load_runtime_placement_module(
		monkeypatch,
		runtime_pools={"POOL-A": pool_doc},
		pool_rows=[
			{
				"name": "POOL-A",
				"pool_name": "Pool A",
				"pool_mode": "Shared Runtime",
				"pool_status": "Active",
				"orchestrator_type": "Bench",
				"primary_cloud_provider": "Google Cloud",
				"runtime_provider": "Google Cloud",
				"region": "us-central1",
				"site_capacity": 10,
				"assigned_site_count": 3,
			}
		],
	)
	environment = SimpleNamespace(
		deployment_mode="",
		runtime_pool="",
		dedicated_runtime_target="",
		hosting_tier="Sandbox",
		database_mode="Shared DB Fleet",
		runtime_provider="Google Cloud",
		primary_cloud_provider="Google Cloud",
		region="us-central1",
		placement_strategy="",
	)
	policy = SimpleNamespace(default_deployment_mode="Shared Runtime")

	module.assign_runtime_placement(environment, policy=policy)

	assert environment.deployment_mode == "Shared Runtime"
	assert environment.runtime_pool == "POOL-A"
	assert environment.dedicated_runtime_target == ""
	assert environment.placement_strategy == "Shared Runtime Pool"


def test_assign_runtime_placement_prefers_bench_pool_with_headroom(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	pool_a = SimpleNamespace(
		name="POOL-A",
		pool_name="Pool A",
		pool_mode="Shared Runtime",
		pool_status="Active",
		orchestrator_type="Docker Compose",
		primary_cloud_provider="Google Cloud",
		runtime_provider="Google Cloud",
		region="us-central1",
	)
	pool_b = SimpleNamespace(
		name="POOL-B",
		pool_name="Pool B",
		pool_mode="Shared Runtime",
		pool_status="Active",
		orchestrator_type="Bench",
		primary_cloud_provider="Google Cloud",
		runtime_provider="Google Cloud",
		region="us-central1",
	)
	module = _load_runtime_placement_module(
		monkeypatch,
		runtime_pools={"POOL-A": pool_a, "POOL-B": pool_b},
		pool_rows=[
			{
				"name": "POOL-A",
				"pool_name": "Pool A",
				"pool_mode": "Shared Runtime",
				"pool_status": "Active",
				"orchestrator_type": "Docker Compose",
				"primary_cloud_provider": "Google Cloud",
				"runtime_provider": "Google Cloud",
				"region": "us-central1",
				"site_capacity": 10,
				"assigned_site_count": 1,
			},
			{
				"name": "POOL-B",
				"pool_name": "Pool B",
				"pool_mode": "Shared Runtime",
				"pool_status": "Active",
				"orchestrator_type": "Bench",
				"primary_cloud_provider": "Google Cloud",
				"runtime_provider": "Google Cloud",
				"region": "us-central1",
				"site_capacity": 10,
				"assigned_site_count": 2,
			},
		],
	)
	environment = SimpleNamespace(
		deployment_mode="Shared Runtime",
		runtime_pool="",
		dedicated_runtime_target="",
		hosting_tier="Standard",
		database_mode="Shared DB Fleet",
		runtime_provider="Google Cloud",
		primary_cloud_provider="Google Cloud",
		region="us-central1",
		placement_strategy="",
	)

	module.assign_runtime_placement(environment, policy=None)

	assert environment.runtime_pool == "POOL-B"


def test_assign_runtime_placement_vip_defaults_to_dedicated(monkeypatch: pytest.MonkeyPatch) -> None:
	module = _load_runtime_placement_module(monkeypatch)
	environment = SimpleNamespace(
		deployment_mode="",
		runtime_pool="",
		dedicated_runtime_target="vip-runtime-01",
		hosting_tier="VIP",
		database_mode="Dedicated DB Instance",
		runtime_provider="Google Cloud",
		primary_cloud_provider="Google Cloud",
		region="us-central1",
		placement_strategy="",
	)

	module.assign_runtime_placement(environment, policy=None)

	assert environment.deployment_mode == "Dedicated Runtime"
	assert environment.runtime_pool == ""
	assert environment.placement_strategy == "Dedicated Runtime + DB"


def test_assign_runtime_placement_errors_when_no_pool_matches(monkeypatch: pytest.MonkeyPatch) -> None:
	module = _load_runtime_placement_module(
		monkeypatch,
		pool_rows=[
			{
				"name": "POOL-A",
				"pool_name": "Pool A",
				"pool_mode": "Shared Runtime",
				"pool_status": "Full",
				"orchestrator_type": "Bench",
				"primary_cloud_provider": "Google Cloud",
				"runtime_provider": "Google Cloud",
				"region": "us-central1",
				"site_capacity": 2,
				"assigned_site_count": 2,
			}
		],
	)
	environment = SimpleNamespace(
		deployment_mode="Shared Runtime",
		runtime_pool="",
		dedicated_runtime_target="",
		hosting_tier="Standard",
		database_mode="Shared DB Fleet",
		runtime_provider="Google Cloud",
		primary_cloud_provider="Google Cloud",
		region="us-central1",
		placement_strategy="",
	)

	with pytest.raises(RuntimeError, match="No eligible Runtime Pool is available"):
		module.assign_runtime_placement(environment, policy=None)
