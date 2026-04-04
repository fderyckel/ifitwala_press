from __future__ import annotations

import importlib
import sys
from types import ModuleType, SimpleNamespace

import pytest


def _load_runtime_orchestration_module(monkeypatch: pytest.MonkeyPatch):
	calls: list[tuple[str, object]] = []

	fake_frappe = ModuleType("frappe")

	def _throw(message: str) -> None:
		raise RuntimeError(message)

	def _get_doc(doctype: str, name: str):
		if doctype == "Runtime Pool" and name == "POOL-1":
			return SimpleNamespace(orchestrator_type="Bench")
		raise RuntimeError(f"Unexpected get_doc lookup: {doctype} {name}")

	fake_frappe.throw = _throw  # type: ignore[attr-defined]
	fake_frappe.get_doc = _get_doc  # type: ignore[attr-defined]
	fake_model = ModuleType("frappe.model")
	fake_document = ModuleType("frappe.model.document")
	fake_document.Document = object  # type: ignore[attr-defined]

	founder_service = ModuleType("ifitwala_press.ifitwala_press.services.founder_runtime_service")
	founder_service.provision_demo_runtime = lambda environment: (
		calls.append(("founder", environment)) or {"mode": "founder"}
	)  # type: ignore[attr-defined]
	founder_service.restore_demo_runtime = lambda environment, reason: {"mode": "founder"}  # type: ignore[attr-defined]
	founder_service.sync_edge_route = lambda environment: {"mode": "founder"}  # type: ignore[attr-defined]
	founder_service.teardown_demo_runtime = lambda environment, reason: {"mode": "founder"}  # type: ignore[attr-defined]

	shared_service = ModuleType("ifitwala_press.ifitwala_press.services.shared_demo_bench_service")
	shared_service.provision_shared_demo_site = lambda environment: (
		calls.append(("shared", environment)) or {"mode": "shared"}
	)  # type: ignore[attr-defined]
	shared_service.restore_shared_demo_site = lambda environment, reason: {"mode": "shared"}  # type: ignore[attr-defined]
	shared_service.sync_shared_demo_edge_route = lambda environment: {"mode": "shared"}  # type: ignore[attr-defined]
	shared_service.teardown_shared_demo_site = lambda environment, reason: {"mode": "shared"}  # type: ignore[attr-defined]

	monkeypatch.setitem(sys.modules, "frappe", fake_frappe)
	monkeypatch.setitem(sys.modules, "frappe.model", fake_model)
	monkeypatch.setitem(sys.modules, "frappe.model.document", fake_document)
	monkeypatch.setitem(
		sys.modules,
		"ifitwala_press.ifitwala_press.services.founder_runtime_service",
		founder_service,
	)
	monkeypatch.setitem(
		sys.modules,
		"ifitwala_press.ifitwala_press.services.shared_demo_bench_service",
		shared_service,
	)
	sys.modules.pop("ifitwala_press.ifitwala_press.services.runtime_orchestration_service", None)
	module = importlib.import_module("ifitwala_press.ifitwala_press.services.runtime_orchestration_service")
	return module, calls


def test_shared_runtime_pool_dispatches_to_shared_demo_bench(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	module, calls = _load_runtime_orchestration_module(monkeypatch)
	environment = SimpleNamespace(
		runtime_reference="",
		deployment_mode="Shared Runtime",
		runtime_pool="POOL-1",
	)

	result = module.provision_environment_runtime(environment)

	assert result["mode"] == "shared"
	assert calls == [("shared", environment)]


def test_dedicated_runtime_dispatches_to_founder_adapter(monkeypatch: pytest.MonkeyPatch) -> None:
	module, calls = _load_runtime_orchestration_module(monkeypatch)
	environment = SimpleNamespace(
		runtime_reference="compose:ifw-demo",
		deployment_mode="Dedicated Runtime",
		runtime_pool="",
	)

	result = module.provision_environment_runtime(environment)

	assert result["mode"] == "founder"
	assert calls == [("founder", environment)]
