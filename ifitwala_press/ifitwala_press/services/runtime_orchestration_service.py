from __future__ import annotations

from typing import Any

import frappe
from frappe.model.document import Document

from ifitwala_press.ifitwala_press.services.founder_runtime_service import (
	provision_demo_runtime,
	restore_demo_runtime,
	sync_edge_route,
	teardown_demo_runtime,
)
from ifitwala_press.ifitwala_press.services.shared_demo_bench_service import (
	provision_shared_demo_site,
	restore_shared_demo_site,
	sync_shared_demo_edge_route,
	teardown_shared_demo_site,
)

SHARED_RUNTIME = "Shared Runtime"
RESERVED_RUNTIME = "Reserved Runtime"


def provision_environment_runtime(environment: str | Document) -> dict[str, Any]:
	environment_doc = _as_doc("Tenant Environment", environment)
	if _uses_shared_demo_bench(environment_doc):
		return provision_shared_demo_site(environment_doc)
	return provision_demo_runtime(environment_doc)


def teardown_environment_runtime(environment: str | Document, *, reason: str) -> dict[str, Any]:
	environment_doc = _as_doc("Tenant Environment", environment)
	if _uses_shared_demo_bench(environment_doc):
		return teardown_shared_demo_site(environment_doc, reason=reason)
	return teardown_demo_runtime(environment_doc, reason=reason)


def restore_environment_runtime(environment: str | Document, *, reason: str) -> dict[str, Any]:
	environment_doc = _as_doc("Tenant Environment", environment)
	if _uses_shared_demo_bench(environment_doc):
		return restore_shared_demo_site(environment_doc, reason=reason)
	return restore_demo_runtime(environment_doc, reason=reason)


def sync_environment_edge_route(environment: str | Document) -> dict[str, Any]:
	environment_doc = _as_doc("Tenant Environment", environment)
	if _uses_shared_demo_bench(environment_doc):
		return sync_shared_demo_edge_route(environment_doc)
	return sync_edge_route(environment_doc)


def _uses_shared_demo_bench(environment: Document) -> bool:
	runtime_reference = str(getattr(environment, "runtime_reference", "") or "").strip()
	if runtime_reference.startswith("bench:"):
		return True
	if runtime_reference.startswith("compose:"):
		return False

	deployment_mode = str(getattr(environment, "deployment_mode", "") or "").strip()
	if deployment_mode not in {SHARED_RUNTIME, RESERVED_RUNTIME}:
		return False

	runtime_pool_name = str(getattr(environment, "runtime_pool", "") or "").strip()
	if not runtime_pool_name:
		frappe.throw("Runtime Pool is required before a shared runtime environment can be provisioned.")

	runtime_pool = frappe.get_doc("Runtime Pool", runtime_pool_name)
	orchestrator_type = str(getattr(runtime_pool, "orchestrator_type", "") or "").strip()
	if orchestrator_type != "Bench":
		frappe.throw(
			f"Runtime Pool {runtime_pool_name} uses {orchestrator_type or 'no orchestrator type'} and is not supported by the shared demo bench adapter."
		)
	return True


def _as_doc(doctype: str, document_or_name: str | Document) -> Document:
	if isinstance(document_or_name, str):
		return frappe.get_doc(doctype, document_or_name)
	return document_or_name
