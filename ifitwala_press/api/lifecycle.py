from __future__ import annotations

from typing import Any

import frappe

from ifitwala_press.ifitwala_press.services.environment_lifecycle_service import (
	archive_environment as archive_environment_service,
	create_sandbox as create_sandbox_service,
	mark_live as mark_live_service,
	provision_production as provision_production_service,
	qualify_for_production as qualify_for_production_service,
	restore_environment as restore_environment_service,
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
	status_reason: str | None = None,
) -> dict[str, Any]:
	_require_lifecycle_role()
	document = create_sandbox_service(
		tenant,
		site_name=site_name,
		policy=policy,
		environment_name=environment_name,
		expiry_date=expiry_date,
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
