from __future__ import annotations

import importlib
import sys
from types import ModuleType, SimpleNamespace

import pytest


def _load_tenant_environment_module(
	monkeypatch: pytest.MonkeyPatch, *, runtime_pools: dict[str, object] | None = None
):
	fake_frappe = ModuleType("frappe")

	def _throw(message: str) -> None:
		raise RuntimeError(message)

	fake_frappe.throw = _throw  # type: ignore[attr-defined]
	runtime_pools = runtime_pools or {}

	def _get_doc(doctype: str, name: str):
		if doctype == "Runtime Pool":
			if name not in runtime_pools:
				raise RuntimeError(f"Missing runtime pool fixture: {name}")
			return runtime_pools[name]
		raise RuntimeError(f"Unexpected get_doc lookup: {doctype} {name}")

	fake_frappe.get_doc = _get_doc  # type: ignore[attr-defined]
	fake_model = ModuleType("frappe.model")
	fake_document = ModuleType("frappe.model.document")
	fake_document.Document = object  # type: ignore[attr-defined]

	monkeypatch.setitem(sys.modules, "frappe", fake_frappe)
	monkeypatch.setitem(sys.modules, "frappe.model", fake_model)
	monkeypatch.setitem(sys.modules, "frappe.model.document", fake_document)
	sys.modules.pop("ifitwala_press.ifitwala_press.doctype.tenant_environment.tenant_environment", None)
	return importlib.import_module(
		"ifitwala_press.ifitwala_press.doctype.tenant_environment.tenant_environment"
	)


def test_manual_site_status_edit_is_blocked(monkeypatch: pytest.MonkeyPatch) -> None:
	module = _load_tenant_environment_module(monkeypatch)
	previous = SimpleNamespace(site_status="Sandbox Active", last_transition_on=None, last_transition_by=None)
	current = SimpleNamespace(
		site_status="Live",
		last_transition_on=None,
		last_transition_by=None,
		flags=SimpleNamespace(),
		is_new=lambda: False,
		get_doc_before_save=lambda: previous,
	)

	with pytest.raises(
		RuntimeError, match="Site Status must be changed through Ifitwala Press lifecycle actions"
	):
		module.TenantEnvironment._validate_lifecycle_edit_discipline(current)


def test_service_guard_flag_allows_controlled_transition(monkeypatch: pytest.MonkeyPatch) -> None:
	module = _load_tenant_environment_module(monkeypatch)
	previous = SimpleNamespace(site_status="Sandbox Active", last_transition_on=None, last_transition_by=None)
	current = SimpleNamespace(
		site_status="Live",
		last_transition_on="2026-03-28 10:00:00",
		last_transition_by="ops@example.com",
		flags=SimpleNamespace(ifitwala_allow_lifecycle_transition=True),
		is_new=lambda: False,
		get_doc_before_save=lambda: previous,
	)

	module.TenantEnvironment._validate_lifecycle_edit_discipline(current)


def test_allowlisted_ingress_requires_cidr_rows(monkeypatch: pytest.MonkeyPatch) -> None:
	module = _load_tenant_environment_module(monkeypatch)
	current = SimpleNamespace(
		ingress_access_mode="Allowlisted",
		get=lambda fieldname: [] if fieldname == "ingress_allowlist" else None,
	)

	with pytest.raises(
		RuntimeError,
		match="Ingress Allowlist must contain at least one CIDR when Ingress Access Mode is Allowlisted",
	):
		module.TenantEnvironment._validate_ingress_access_constraints(current)


def test_ingress_allowlist_cidrs_are_normalized(monkeypatch: pytest.MonkeyPatch) -> None:
	module = _load_tenant_environment_module(monkeypatch)
	row = SimpleNamespace(cidr="203.0.113.10", notes=" Office ")
	current = SimpleNamespace(
		ingress_access_mode="Allowlisted",
		get=lambda fieldname: [row] if fieldname == "ingress_allowlist" else None,
	)

	module.TenantEnvironment._validate_ingress_access_constraints(current)

	assert row.cidr == "203.0.113.10/32"


def test_live_shared_runtime_requires_runtime_pool(monkeypatch: pytest.MonkeyPatch) -> None:
	module = _load_tenant_environment_module(monkeypatch)
	current = SimpleNamespace(
		deployment_mode="Shared Runtime",
		runtime_pool="",
		dedicated_runtime_target="",
		site_status="Live",
	)

	with pytest.raises(
		RuntimeError,
		match="Runtime Pool is required before a shared or reserved runtime environment can be marked Live",
	):
		module.TenantEnvironment._validate_runtime_placement_constraints(current)


def test_runtime_pool_mode_must_match_environment_deployment_mode(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	module = _load_tenant_environment_module(
		monkeypatch,
		runtime_pools={
			"DEMO-POOL": SimpleNamespace(
				pool_mode="Reserved Runtime",
				is_active=1,
				pool_status="Active",
				runtime_provider="Google Cloud",
				region="us-central1",
			)
		},
	)
	current = SimpleNamespace(
		deployment_mode="Shared Runtime",
		runtime_pool="DEMO-POOL",
		dedicated_runtime_target="",
		site_status="Sandbox Provisioning",
		runtime_provider="Google Cloud",
		region="us-central1",
	)

	with pytest.raises(RuntimeError, match="cannot back Shared Runtime placement"):
		module.TenantEnvironment._validate_runtime_placement_constraints(current)


def test_dedicated_runtime_cannot_reference_runtime_pool(monkeypatch: pytest.MonkeyPatch) -> None:
	module = _load_tenant_environment_module(monkeypatch)
	current = SimpleNamespace(
		deployment_mode="Dedicated Runtime",
		runtime_pool="DEMO-POOL",
		dedicated_runtime_target="dedicated-demo-host-01",
		site_status="Production Qualification",
		runtime_reference="",
	)

	with pytest.raises(
		RuntimeError,
		match="Runtime Pool can only be set when Deployment Mode is Shared Runtime or Reserved Runtime",
	):
		module.TenantEnvironment._validate_runtime_placement_constraints(current)
