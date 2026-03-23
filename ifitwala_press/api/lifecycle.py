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
		backup_export_path=backup_export_path,
		status_reason=status_reason,
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
	document = restore_environment_service(environment, reason=reason)
	return _serialize_document(document)


@frappe.whitelist()
def archive_environment(environment: str, reason: str) -> dict[str, Any]:
	_require_lifecycle_role()
	document = archive_environment_service(environment, reason=reason)
	return _serialize_document(document)
