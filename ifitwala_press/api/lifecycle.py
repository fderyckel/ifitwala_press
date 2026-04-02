from __future__ import annotations

from typing import Any

import frappe

from ifitwala_press.ifitwala_press.services.environment_lifecycle_service import (
	archive_environment as archive_environment_service,
)
from ifitwala_press.ifitwala_press.services.environment_lifecycle_service import (
	complete_sandbox_provisioning as complete_sandbox_provisioning_service,
)
from ifitwala_press.ifitwala_press.services.environment_lifecycle_service import (
	create_sandbox as create_sandbox_service,
)
from ifitwala_press.ifitwala_press.services.environment_lifecycle_service import (
	expire_sandbox as expire_sandbox_service,
)
from ifitwala_press.ifitwala_press.services.environment_lifecycle_service import (
	mark_live as mark_live_service,
)
from ifitwala_press.ifitwala_press.services.environment_lifecycle_service import (
	mark_provisioning_failed as mark_provisioning_failed_service,
)
from ifitwala_press.ifitwala_press.services.environment_lifecycle_service import (
	provision_production as provision_production_service,
)
from ifitwala_press.ifitwala_press.services.environment_lifecycle_service import (
	qualify_for_production as qualify_for_production_service,
)
from ifitwala_press.ifitwala_press.services.environment_lifecycle_service import (
	restore_environment as restore_environment_service,
)
from ifitwala_press.ifitwala_press.services.environment_lifecycle_service import (
	suspend_environment as suspend_environment_service,
)
from ifitwala_press.ifitwala_press.services.founder_runtime_service import (
	provision_demo_runtime as provision_demo_runtime_service,
)
from ifitwala_press.ifitwala_press.services.founder_runtime_service import (
	restore_demo_runtime as restore_demo_runtime_service,
)
from ifitwala_press.ifitwala_press.services.founder_runtime_service import (
	sync_edge_route as sync_edge_route_service,
)
from ifitwala_press.ifitwala_press.services.founder_runtime_service import (
	teardown_demo_runtime as teardown_demo_runtime_service,
)

ACTION_ROLES = {"Ifitwala Press Admin", "Ifitwala Press Ops"}


def _require_lifecycle_role() -> None:
	user_roles = set(frappe.get_roles())
	if ACTION_ROLES.isdisjoint(user_roles):
		frappe.throw("You do not have permission to run Ifitwala Press lifecycle actions.")


def _serialize_document(document: Any) -> dict[str, Any]:
	return {
		"name": document.name,
		"doctype": document.doctype,
		"site_status": getattr(document, "site_status", None),
		"tenant": getattr(document, "tenant", None),
	}


@frappe.whitelist()
def create_sandbox(
	tenant: str,
	site_name: str,
	policy: str | None = None,
	environment_name: str | None = None,
	expiry_date: str | None = None,
	demo_seed_mode: str | None = None,
	demo_seed_reference: str | None = None,
	status_reason: str | None = None,
) -> dict[str, Any]:
	_require_lifecycle_role()
	document = create_sandbox_service(
		tenant,
		site_name=site_name,
		policy=policy,
		environment_name=environment_name,
		expiry_date=expiry_date,
		demo_seed_mode=demo_seed_mode,
		demo_seed_reference=demo_seed_reference,
		status_reason=status_reason,
	)
	return _serialize_document(document)


@frappe.whitelist()
def complete_sandbox_provisioning(
	environment: str,
	site_name: str | None = None,
	primary_domain: str | None = None,
	routing_mode: str | None = None,
	dns_ready: int | bool | None = None,
	tls_ready: int | bool | None = None,
	host_header_value: str | None = None,
	db_name: str | None = None,
	db_user: str | None = None,
	provisioning_job_id: str | None = None,
	last_provisioning_step: str | None = None,
	provisioning_message: str | None = None,
	runtime_reference: str | None = None,
	primary_cloud_provider: str | None = None,
	runtime_provider: str | None = None,
	object_storage_provider: str | None = None,
	dns_provider: str | None = None,
	file_storage_provider: str | None = None,
	file_storage_class: str | None = None,
	backup_storage_provider: str | None = None,
	backup_storage_class: str | None = None,
	backup_export_path: str | None = None,
	status_reason: str | None = None,
) -> dict[str, Any]:
	_require_lifecycle_role()
	document = complete_sandbox_provisioning_service(
		environment,
		site_name=site_name,
		primary_domain=primary_domain,
		routing_mode=routing_mode,
		dns_ready=dns_ready,
		tls_ready=tls_ready,
		host_header_value=host_header_value,
		db_name=db_name,
		db_user=db_user,
		provisioning_job_id=provisioning_job_id,
		last_provisioning_step=last_provisioning_step,
		provisioning_message=provisioning_message,
		runtime_reference=runtime_reference,
		primary_cloud_provider=primary_cloud_provider,
		runtime_provider=runtime_provider,
		object_storage_provider=object_storage_provider,
		dns_provider=dns_provider,
		file_storage_provider=file_storage_provider,
		file_storage_class=file_storage_class,
		backup_storage_provider=backup_storage_provider,
		backup_storage_class=backup_storage_class,
		backup_export_path=backup_export_path,
		status_reason=status_reason,
	)
	return _serialize_document(document)


@frappe.whitelist()
def provision_founder_demo_runtime(
	environment: str,
	status_reason: str | None = None,
) -> dict[str, Any]:
	_require_lifecycle_role()
	try:
		result = provision_demo_runtime_service(environment)
	except Exception as exc:
		mark_provisioning_failed_service(
			environment,
			reason=str(exc),
			last_provisioning_step="Founder runtime provisioning",
			provisioning_message=str(exc),
		)
		raise

	document = complete_sandbox_provisioning_service(
		environment,
		site_name=result.get("site_name"),
		primary_domain=result.get("primary_domain"),
		routing_mode=result.get("routing_mode"),
		dns_ready=result.get("dns_ready"),
		tls_ready=result.get("tls_ready"),
		host_header_value=result.get("host_header_value"),
		db_name=result.get("db_name"),
		db_user=result.get("db_user"),
		provisioning_job_id=result.get("provisioning_job_id"),
		last_provisioning_step=result.get("last_provisioning_step"),
		provisioning_message=result.get("provisioning_message"),
		runtime_reference=result.get("runtime_reference"),
		primary_cloud_provider=result.get("primary_cloud_provider"),
		runtime_provider=result.get("runtime_provider"),
		object_storage_provider=result.get("object_storage_provider"),
		dns_provider=result.get("dns_provider"),
		file_storage_provider=result.get("file_storage_provider"),
		file_storage_class=result.get("file_storage_class"),
		backup_storage_provider=result.get("backup_storage_provider"),
		backup_storage_class=result.get("backup_storage_class"),
		backup_export_path=result.get("backup_export_path"),
		status_reason=status_reason or result.get("status_reason") or "Founder demo runtime provisioned.",
	)
	return _serialize_document(document)


@frappe.whitelist()
def qualify_for_production(
	environment: str,
	hosting_tier: str,
	database_mode: str,
	conversion_strategy: str,
	policy: str | None = None,
	region: str | None = None,
	primary_cloud_provider: str | None = None,
	runtime_provider: str | None = None,
	object_storage_provider: str | None = None,
	dns_provider: str | None = None,
	status_reason: str | None = None,
) -> dict[str, Any]:
	_require_lifecycle_role()
	document = qualify_for_production_service(
		environment,
		hosting_tier=hosting_tier,
		database_mode=database_mode,
		conversion_strategy=conversion_strategy,
		policy=policy,
		region=region,
		primary_cloud_provider=primary_cloud_provider,
		runtime_provider=runtime_provider,
		object_storage_provider=object_storage_provider,
		dns_provider=dns_provider,
		status_reason=status_reason,
	)
	return _serialize_document(document)


@frappe.whitelist()
def mark_provisioning_failed(
	environment: str,
	reason: str,
	last_provisioning_step: str | None = None,
	provisioning_job_id: str | None = None,
	provisioning_message: str | None = None,
) -> dict[str, Any]:
	_require_lifecycle_role()
	document = mark_provisioning_failed_service(
		environment,
		reason=reason,
		last_provisioning_step=last_provisioning_step,
		provisioning_job_id=provisioning_job_id,
		provisioning_message=provisioning_message,
	)
	return _serialize_document(document)


@frappe.whitelist()
def expire_sandbox(
	environment: str,
	reason: str,
	last_provisioning_step: str | None = None,
	provisioning_message: str | None = None,
	runtime_reference: str | None = None,
	backup_export_path: str | None = None,
) -> dict[str, Any]:
	_require_lifecycle_role()
	document = expire_sandbox_service(
		environment,
		reason=reason,
		last_provisioning_step=last_provisioning_step,
		provisioning_message=provisioning_message,
		runtime_reference=runtime_reference,
		backup_export_path=backup_export_path,
	)
	return _serialize_document(document)


@frappe.whitelist()
def teardown_founder_demo_runtime(
	environment: str,
	reason: str,
) -> dict[str, Any]:
	_require_lifecycle_role()
	result = teardown_demo_runtime_service(environment, reason=reason)
	document = expire_sandbox_service(
		environment,
		reason=reason,
		last_provisioning_step=result.get("last_provisioning_step") or "Founder runtime teardown",
		provisioning_message=result.get("provisioning_message"),
		runtime_reference=result.get("runtime_reference"),
		backup_export_path=result.get("backup_export_path"),
	)
	return _serialize_document(document)


@frappe.whitelist()
def sync_founder_edge_route(environment: str) -> dict[str, Any]:
	_require_lifecycle_role()
	environment_doc = frappe.get_doc("Tenant Environment", environment)
	runtime_reference = str(getattr(environment_doc, "runtime_reference", "") or "").strip()
	if not runtime_reference.startswith("compose:"):
		frappe.throw("Founder edge route sync is currently implemented only for founder runtimes.")

	if not getattr(environment_doc, "primary_domain", None):
		frappe.throw("Primary Domain is required before the founder edge route can be synced.")

	result = sync_edge_route_service(environment_doc)
	if result.get("routing_mode"):
		environment_doc.routing_mode = result.get("routing_mode")
	if result.get("host_header_value"):
		environment_doc.host_header_value = result.get("host_header_value")
	if result.get("last_provisioning_step"):
		environment_doc.last_provisioning_step = result.get("last_provisioning_step")
	if result.get("provisioning_message"):
		environment_doc.provisioning_message = result.get("provisioning_message")
	if result.get("status_reason"):
		environment_doc.status_reason = result.get("status_reason")
	environment_doc.save()
	return _serialize_document(environment_doc)


@frappe.whitelist()
def provision_production(
	environment: str,
	site_name: str | None = None,
	provisioning_job_id: str | None = None,
	primary_domain: str | None = None,
	status_reason: str | None = None,
) -> dict[str, Any]:
	_require_lifecycle_role()
	document = provision_production_service(
		environment,
		site_name=site_name,
		provisioning_job_id=provisioning_job_id,
		primary_domain=primary_domain,
		status_reason=status_reason,
	)
	return _serialize_document(document)


@frappe.whitelist()
def mark_live(environment: str, status_reason: str | None = None) -> dict[str, Any]:
	_require_lifecycle_role()
	document = mark_live_service(environment, status_reason=status_reason)
	return _serialize_document(document)


@frappe.whitelist()
def suspend_environment(environment: str, reason: str) -> dict[str, Any]:
	_require_lifecycle_role()
	document = suspend_environment_service(environment, reason=reason)
	return _serialize_document(document)


@frappe.whitelist()
def restore_environment(environment: str, reason: str) -> dict[str, Any]:
	_require_lifecycle_role()
	environment_doc = frappe.get_doc("Tenant Environment", environment)
	runtime_reference = str(getattr(environment_doc, "runtime_reference", "") or "").strip()
	if not runtime_reference.startswith("compose:"):
		frappe.throw("Restore workflow is currently implemented only for founder runtimes.")

	if not getattr(environment_doc, "backup_export_path", None):
		frappe.throw("Backup Export Path is required before a founder runtime can be restored.")

	result = restore_demo_runtime_service(environment_doc, reason=reason)
	document = restore_environment_service(environment, reason=reason)
	if result.get("last_provisioning_step"):
		document.last_provisioning_step = result.get("last_provisioning_step")
	if result.get("provisioning_message"):
		document.provisioning_message = result.get("provisioning_message")
	if result.get("runtime_reference"):
		document.runtime_reference = result.get("runtime_reference")
	if result.get("backup_export_path"):
		document.backup_export_path = result.get("backup_export_path")
	if result.get("db_restore_tested_on"):
		document.db_restore_tested_on = result.get("db_restore_tested_on")
	document.save()
	return _serialize_document(document)


@frappe.whitelist()
def archive_environment(environment: str, reason: str) -> dict[str, Any]:
	_require_lifecycle_role()
	document = archive_environment_service(environment, reason=reason)
	return _serialize_document(document)
