from __future__ import annotations

import json
import os
import shlex
import subprocess
from typing import Any

import frappe
from frappe.model.document import Document

from ifitwala_press.ifitwala_press.services.runtime_storage_profile_service import (
	build_drive_storage_profile,
)

ADAPTER_CONFIG_KEY = "ifitwala_press_founder_runtime_adapter"
TIMEOUT_CONFIG_KEY = "ifitwala_press_founder_runtime_timeout"
DEFAULT_TIMEOUT_SECONDS = 1800


def provision_demo_runtime(environment: str | Document) -> dict[str, Any]:
	environment_doc = _as_doc("Tenant Environment", environment)
	tenant_doc = frappe.get_doc("Press Tenant", environment_doc.tenant)
	return _run_adapter(
		"provision-demo-runtime",
		_build_payload(environment_doc, tenant_doc),
	)


def teardown_demo_runtime(environment: str | Document, *, reason: str) -> dict[str, Any]:
	environment_doc = _as_doc("Tenant Environment", environment)
	tenant_doc = frappe.get_doc("Press Tenant", environment_doc.tenant)
	payload = _build_payload(environment_doc, tenant_doc)
	payload["teardown_reason"] = reason
	return _run_adapter(
		"teardown-demo-runtime",
		payload,
	)


def restore_demo_runtime(environment: str | Document, *, reason: str) -> dict[str, Any]:
	environment_doc = _as_doc("Tenant Environment", environment)
	tenant_doc = frappe.get_doc("Press Tenant", environment_doc.tenant)
	payload = _build_payload(environment_doc, tenant_doc)
	payload["restore_reason"] = reason
	return _run_adapter(
		"restore-demo-runtime",
		payload,
	)


def _build_payload(environment: Document, tenant: Document) -> dict[str, Any]:
	policy_doc = frappe.get_doc("Tenant Policy", environment.policy) if environment.policy else None
	drive_storage_profile = build_drive_storage_profile(environment)
	return {
		"tenant": {
			"name": tenant.name,
			"tenant_name": tenant.tenant_name,
			"tenant_slug": tenant.tenant_slug,
			"organization_type": tenant.organization_type,
			"country": tenant.country,
			"timezone": tenant.timezone,
			"primary_contact_name": tenant.primary_contact_name,
			"primary_contact_email": tenant.primary_contact_email,
			"primary_contact_phone": tenant.primary_contact_phone,
			"estimated_students": tenant.estimated_students,
			"estimated_staff": tenant.estimated_staff,
			"estimated_guardians": tenant.estimated_guardians,
			"estimated_peak_concurrency": tenant.estimated_peak_concurrency,
		},
		"policy": {
			"name": policy_doc.name if policy_doc else environment.policy,
			"backup_frequency": policy_doc.backup_frequency if policy_doc else None,
			"backup_retention_days": policy_doc.backup_retention_days if policy_doc else None,
			"storage_quota_gb": policy_doc.storage_quota_gb if policy_doc else environment.storage_quota_gb,
			"max_file_size_mb": policy_doc.max_file_size_mb if policy_doc else None,
			"default_primary_cloud_provider": policy_doc.default_primary_cloud_provider
			if policy_doc
			else None,
			"default_runtime_provider": policy_doc.default_runtime_provider if policy_doc else None,
			"default_object_storage_provider": policy_doc.default_object_storage_provider
			if policy_doc
			else None,
			"default_dns_provider": policy_doc.default_dns_provider if policy_doc else None,
		},
		"environment": {
			"name": environment.name,
			"environment_name": environment.environment_name,
			"environment_type": environment.environment_type,
			"site_name": environment.site_name,
			"site_status": environment.site_status,
			"policy": environment.policy,
			"hosting_tier": environment.hosting_tier,
			"placement_strategy": environment.placement_strategy,
			"primary_cloud_provider": environment.primary_cloud_provider,
			"runtime_provider": environment.runtime_provider,
			"object_storage_provider": environment.object_storage_provider,
			"dns_provider": environment.dns_provider,
			"primary_domain": environment.primary_domain,
			"routing_mode": environment.routing_mode,
			"region": environment.region,
			"frappe_branch": environment.frappe_branch,
			"ifitwala_ed_branch": environment.ifitwala_ed_branch,
			"ifitwala_drive_branch": environment.ifitwala_drive_branch,
			"deployment_mode": environment.deployment_mode,
			"database_mode": environment.database_mode,
			"db_provider": environment.db_provider,
			"db_instance_name": environment.db_instance_name,
			"db_name": environment.db_name,
			"db_user": environment.db_user,
			"socketio_enabled": environment.socketio_enabled,
			"worker_profile": environment.worker_profile,
			"file_storage_provider": environment.file_storage_provider,
			"file_storage_class": environment.file_storage_class,
			"backup_storage_provider": environment.backup_storage_provider,
			"backup_storage_class": environment.backup_storage_class,
			"expires_on": str(environment.expires_on) if environment.expires_on else None,
			"demo_seed_mode": environment.demo_seed_mode,
			"demo_seed_reference": environment.demo_seed_reference,
			"runtime_reference": environment.runtime_reference,
			"backup_export_path": environment.backup_export_path,
		},
		"providers": {
			"primary_cloud_provider": environment.primary_cloud_provider,
			"runtime_provider": environment.runtime_provider,
			"object_storage_provider": environment.object_storage_provider,
			"dns_provider": environment.dns_provider,
			"db_provider": environment.db_provider,
		},
		"storage": {
			"file_storage_provider": environment.file_storage_provider,
			"file_storage_class": environment.file_storage_class,
			"backup_storage_provider": environment.backup_storage_provider,
			"backup_storage_class": environment.backup_storage_class,
			"backup_frequency": policy_doc.backup_frequency if policy_doc else None,
			"backup_retention_days": policy_doc.backup_retention_days if policy_doc else None,
			"storage_quota_gb": environment.storage_quota_gb
			or (policy_doc.storage_quota_gb if policy_doc else None),
			"shared_site_storage": True,
			"site_storage_apps": ["ifitwala_ed", "ifitwala_drive"],
			"drive_storage_profile": drive_storage_profile,
		},
		"runtime": {
			"drive_storage_profile": drive_storage_profile,
		},
	}


def _run_adapter(action: str, payload: dict[str, Any]) -> dict[str, Any]:
	command = _get_adapter_command()
	result = subprocess.run(
		[*command, action],
		input=json.dumps(payload),
		capture_output=True,
		text=True,
		timeout=_get_timeout_seconds(),
		check=False,
	)

	stdout = result.stdout.strip()
	stderr = result.stderr.strip()

	if result.returncode != 0:
		message = stderr or stdout or f"Adapter exited with code {result.returncode}."
		frappe.throw(f"Founder runtime adapter failed during {action}: {message}")

	if not stdout:
		return {}

	try:
		parsed = json.loads(stdout)
	except json.JSONDecodeError:
		frappe.throw(f"Founder runtime adapter returned invalid JSON during {action}.")

	if not isinstance(parsed, dict):
		frappe.throw(f"Founder runtime adapter must return a JSON object during {action}.")

	return parsed


def _get_adapter_command() -> list[str]:
	configured = frappe.conf.get(ADAPTER_CONFIG_KEY) or os.environ.get(
		"IFITWALA_PRESS_FOUNDER_RUNTIME_ADAPTER"
	)
	if not configured:
		frappe.throw(
			"Founder runtime adapter is not configured. Set "
			f"`{ADAPTER_CONFIG_KEY}` in site config or `IFITWALA_PRESS_FOUNDER_RUNTIME_ADAPTER` in the environment."
		)

	if isinstance(configured, str):
		command = shlex.split(configured)
	else:
		command = [str(part) for part in configured]

	if not command:
		frappe.throw("Founder runtime adapter command is empty.")

	return command


def _get_timeout_seconds() -> int:
	configured = frappe.conf.get(TIMEOUT_CONFIG_KEY) or os.environ.get(
		"IFITWALA_PRESS_FOUNDER_RUNTIME_TIMEOUT"
	)
	if configured is None:
		return DEFAULT_TIMEOUT_SECONDS

	try:
		timeout = int(configured)
	except TypeError, ValueError:
		frappe.throw("Founder runtime adapter timeout must be an integer number of seconds.")

	if timeout <= 0:
		frappe.throw("Founder runtime adapter timeout must be greater than zero.")

	return timeout


def _as_doc(doctype: str, document_or_name: str | Document) -> Document:
	if isinstance(document_or_name, str):
		return frappe.get_doc(doctype, document_or_name)
	return document_or_name
