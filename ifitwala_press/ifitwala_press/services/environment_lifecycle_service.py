from __future__ import annotations

from typing import Any

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

from ifitwala_press.ifitwala_press.services.transition_log_service import create_transition_log

LEAD = "Lead"
SANDBOX_PROVISIONING = "Sandbox Provisioning"
SANDBOX_ACTIVE = "Sandbox Active"
SANDBOX_EXPIRED = "Sandbox Expired"
PRODUCTION_QUALIFICATION = "Production Qualification"
PRODUCTION_PROVISIONING = "Production Provisioning"
LIVE = "Live"
SUSPENDED = "Suspended"
ARCHIVED = "Archived"
PROVISIONING_FAILED = "Provisioning Failed"
DEFAULT_FILE_STORAGE_PROVIDER = "S3 Compatible"
DEFAULT_FILE_STORAGE_CLASS = "Frequent Access"
DEFAULT_BACKUP_STORAGE_PROVIDER = "S3 Compatible"
DEFAULT_BACKUP_STORAGE_CLASS = "Infrequent Access"

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
	LEAD: {SANDBOX_PROVISIONING, PRODUCTION_QUALIFICATION, ARCHIVED},
	SANDBOX_PROVISIONING: {SANDBOX_ACTIVE, PROVISIONING_FAILED, ARCHIVED},
	SANDBOX_ACTIVE: {SANDBOX_EXPIRED, PRODUCTION_QUALIFICATION, SUSPENDED, ARCHIVED},
	SANDBOX_EXPIRED: {SANDBOX_ACTIVE, PRODUCTION_QUALIFICATION, ARCHIVED},
	PRODUCTION_QUALIFICATION: {PRODUCTION_PROVISIONING, ARCHIVED, SANDBOX_ACTIVE},
	PRODUCTION_PROVISIONING: {LIVE, PROVISIONING_FAILED, ARCHIVED},
	LIVE: {SUSPENDED, ARCHIVED},
	SUSPENDED: {LIVE, ARCHIVED},
	PROVISIONING_FAILED: {SANDBOX_PROVISIONING, PRODUCTION_PROVISIONING, ARCHIVED},
}


def create_sandbox(
	tenant: str | Document,
	*,
	site_name: str,
	policy: str | None = None,
	environment_name: str | None = None,
	expiry_date: str | None = None,
	demo_seed_mode: str | None = None,
	demo_seed_reference: str | None = None,
	status_reason: str | None = None,
) -> Document:
	tenant_doc = _as_doc("Press Tenant", tenant)
	policy_name = policy or tenant_doc.default_policy
	policy_doc = _get_policy_doc(policy_name)

	if tenant_doc.tenant_status == ARCHIVED:
		frappe.throw("Archived tenants cannot enter sandbox provisioning.")

	environment = frappe.get_doc(
		{
			"doctype": "Tenant Environment",
			"tenant": tenant_doc.name,
			"environment_name": environment_name or f"{tenant_doc.tenant_name} Sandbox",
			"environment_type": "Sandbox",
			"site_name": site_name,
			"site_status": SANDBOX_PROVISIONING,
			"status_reason": status_reason,
			"policy": policy_name,
			"hosting_tier": "Sandbox",
			"demo_seed_mode": demo_seed_mode or "Blank Site",
			"demo_seed_reference": demo_seed_reference,
			"placement_strategy": "Founder Shared Runtime",
			"expires_on": expiry_date,
		}
	)
	_apply_storage_defaults(environment, policy_doc)
	_update_transition_metadata(environment, status_reason)
	environment.insert()

	create_transition_log(
		tenant=tenant_doc.name,
		environment=environment.name,
		from_state=LEAD,
		to_state=SANDBOX_PROVISIONING,
		message=status_reason or "Sandbox creation initiated.",
		details={"action": "create_sandbox"},
	)
	return environment


def qualify_for_production(
	environment: str | Document,
	*,
	hosting_tier: str,
	database_mode: str,
	conversion_strategy: str,
	policy: str | None = None,
	region: str | None = None,
	status_reason: str | None = None,
) -> Document:
	environment_doc = _as_doc("Tenant Environment", environment)
	_assert_transition_allowed(environment_doc.site_status, PRODUCTION_QUALIFICATION)
	policy_name = policy or environment_doc.policy
	policy_doc = _get_policy_doc(policy_name)

	if environment_doc.environment_type != "Production":
		environment_doc.environment_type = "Production"
	environment_doc.hosting_tier = hosting_tier
	environment_doc.database_mode = database_mode
	environment_doc.policy = policy_name
	environment_doc.region = region or environment_doc.region
	environment_doc.status_reason = status_reason or conversion_strategy
	_apply_storage_defaults(environment_doc, policy_doc)
	_transition_environment(environment_doc, PRODUCTION_QUALIFICATION, status_reason or conversion_strategy)
	return environment_doc


def complete_sandbox_provisioning(
	environment: str | Document,
	*,
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
	file_storage_provider: str | None = None,
	file_storage_class: str | None = None,
	backup_storage_provider: str | None = None,
	backup_storage_class: str | None = None,
	backup_export_path: str | None = None,
	status_reason: str | None = None,
) -> Document:
	environment_doc = _as_doc("Tenant Environment", environment)
	_assert_transition_allowed(environment_doc.site_status, SANDBOX_ACTIVE)

	if environment_doc.environment_type != "Sandbox":
		environment_doc.environment_type = "Sandbox"
	if site_name:
		environment_doc.site_name = site_name
	if primary_domain:
		environment_doc.primary_domain = primary_domain
	if routing_mode:
		environment_doc.routing_mode = routing_mode
	if dns_ready is not None:
		environment_doc.dns_ready = int(bool(dns_ready))
	if tls_ready is not None:
		environment_doc.tls_ready = int(bool(tls_ready))
	if host_header_value:
		environment_doc.host_header_value = host_header_value
	if db_name:
		environment_doc.db_name = db_name
	if db_user:
		environment_doc.db_user = db_user
	if provisioning_job_id:
		environment_doc.provisioning_job_id = provisioning_job_id
	if last_provisioning_step:
		environment_doc.last_provisioning_step = last_provisioning_step
	if provisioning_message:
		environment_doc.provisioning_message = provisioning_message
	if runtime_reference:
		environment_doc.runtime_reference = runtime_reference
	if file_storage_provider:
		environment_doc.file_storage_provider = file_storage_provider
	if file_storage_class:
		environment_doc.file_storage_class = file_storage_class
	if backup_storage_provider:
		environment_doc.backup_storage_provider = backup_storage_provider
	if backup_storage_class:
		environment_doc.backup_storage_class = backup_storage_class
	if backup_export_path:
		environment_doc.backup_export_path = backup_export_path
	_transition_environment(
		environment_doc,
		SANDBOX_ACTIVE,
		status_reason or "Sandbox provisioning completed.",
	)
	return environment_doc


def provision_production(
	environment: str | Document,
	*,
	site_name: str | None = None,
	provisioning_job_id: str | None = None,
	primary_domain: str | None = None,
	status_reason: str | None = None,
) -> Document:
	environment_doc = _as_doc("Tenant Environment", environment)
	_assert_transition_allowed(environment_doc.site_status, PRODUCTION_PROVISIONING)

	if environment_doc.environment_type != "Production":
		environment_doc.environment_type = "Production"
	if site_name:
		environment_doc.site_name = site_name
	if primary_domain:
		environment_doc.primary_domain = primary_domain
	environment_doc.provisioning_job_id = provisioning_job_id
	_transition_environment(environment_doc, PRODUCTION_PROVISIONING, status_reason or "Production provisioning started.")
	return environment_doc


def mark_provisioning_failed(
	environment: str | Document,
	*,
	reason: str,
	last_provisioning_step: str | None = None,
	provisioning_job_id: str | None = None,
	provisioning_message: str | None = None,
) -> Document:
	environment_doc = _as_doc("Tenant Environment", environment)
	_assert_transition_allowed(environment_doc.site_status, PROVISIONING_FAILED)

	if last_provisioning_step:
		environment_doc.last_provisioning_step = last_provisioning_step
	if provisioning_job_id:
		environment_doc.provisioning_job_id = provisioning_job_id
	if provisioning_message:
		environment_doc.provisioning_message = provisioning_message
	_transition_environment(environment_doc, PROVISIONING_FAILED, reason)
	return environment_doc


def expire_sandbox(
	environment: str | Document,
	*,
	reason: str,
	last_provisioning_step: str | None = None,
	provisioning_message: str | None = None,
	runtime_reference: str | None = None,
	backup_export_path: str | None = None,
) -> Document:
	environment_doc = _as_doc("Tenant Environment", environment)
	_assert_transition_allowed(environment_doc.site_status, SANDBOX_EXPIRED)

	if environment_doc.environment_type != "Sandbox":
		frappe.throw("Only sandbox environments can be expired.")

	if last_provisioning_step:
		environment_doc.last_provisioning_step = last_provisioning_step
	if provisioning_message:
		environment_doc.provisioning_message = provisioning_message
	if runtime_reference:
		environment_doc.runtime_reference = runtime_reference
	if backup_export_path:
		environment_doc.backup_export_path = backup_export_path

	_transition_environment(environment_doc, SANDBOX_EXPIRED, reason)
	return environment_doc


def mark_live(
	environment: str | Document,
	*,
	status_reason: str | None = None,
) -> Document:
	environment_doc = _as_doc("Tenant Environment", environment)
	_assert_transition_allowed(environment_doc.site_status, LIVE)
	environment_doc.environment_type = "Production"
	_transition_environment(environment_doc, LIVE, status_reason or "Production environment marked live.")

	tenant_doc = frappe.get_doc("Press Tenant", environment_doc.tenant)
	tenant_doc.active_environment = environment_doc.name
	tenant_doc.save()

	return environment_doc


def suspend_environment(environment: str | Document, *, reason: str) -> Document:
	environment_doc = _as_doc("Tenant Environment", environment)
	_assert_transition_allowed(environment_doc.site_status, SUSPENDED)
	_transition_environment(environment_doc, SUSPENDED, reason)
	return environment_doc


def restore_environment(environment: str | Document, *, reason: str) -> Document:
	environment_doc = _as_doc("Tenant Environment", environment)
	_assert_transition_allowed(environment_doc.site_status, LIVE)
	_transition_environment(environment_doc, LIVE, reason)
	return environment_doc


def archive_environment(environment: str | Document, *, reason: str) -> Document:
	environment_doc = _as_doc("Tenant Environment", environment)
	_assert_transition_allowed(environment_doc.site_status, ARCHIVED)
	_transition_environment(environment_doc, ARCHIVED, reason)
	return environment_doc


def _transition_environment(environment: Document, to_state: str, reason: str | None) -> None:
	from_state = environment.site_status
	environment.site_status = to_state
	environment.status_reason = reason
	_update_transition_metadata(environment, reason)
	environment.save()

	create_transition_log(
		tenant=environment.tenant,
		environment=environment.name,
		from_state=from_state,
		to_state=to_state,
		message=reason,
		details={"action": "state_transition"},
	)


def _update_transition_metadata(environment: Document, reason: str | None) -> None:
	environment.last_transition_on = now_datetime()
	environment.last_transition_by = frappe.session.user
	if reason:
		environment.status_reason = reason


def _assert_transition_allowed(from_state: str, to_state: str) -> None:
	allowed_states = ALLOWED_TRANSITIONS.get(from_state, set())
	if to_state not in allowed_states:
		frappe.throw(f"Transition from {from_state} to {to_state} is not allowed.")


def _apply_storage_defaults(environment: Document, policy: Document | None) -> None:
	environment.file_storage_provider = (
		environment.file_storage_provider
		or getattr(policy, "default_file_storage_provider", None)
		or DEFAULT_FILE_STORAGE_PROVIDER
	)
	environment.file_storage_class = (
		environment.file_storage_class
		or getattr(policy, "default_file_storage_class", None)
		or DEFAULT_FILE_STORAGE_CLASS
	)
	environment.backup_storage_provider = (
		environment.backup_storage_provider
		or getattr(policy, "default_backup_storage_provider", None)
		or DEFAULT_BACKUP_STORAGE_PROVIDER
	)
	environment.backup_storage_class = (
		environment.backup_storage_class
		or getattr(policy, "default_backup_storage_class", None)
		or DEFAULT_BACKUP_STORAGE_CLASS
	)

	if not environment.storage_quota_gb and policy and policy.storage_quota_gb not in (None, ""):
		environment.storage_quota_gb = policy.storage_quota_gb


def _get_policy_doc(policy_name: str | None) -> Document | None:
	if not policy_name:
		return None
	return frappe.get_doc("Tenant Policy", policy_name)


def _as_doc(doctype: str, document_or_name: str | Document) -> Document:
	if isinstance(document_or_name, str):
		return frappe.get_doc(doctype, document_or_name)
	return document_or_name
