from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import format_datetime, now_datetime


SNAPSHOT_ROLES = {"Ifitwala Press Admin", "Ifitwala Press Ops", "Ifitwala Press Support"}
SUBSCRIPTION_ROLES = {"Ifitwala Press Admin", "Ifitwala Press Sales", "Ifitwala Press Finance"}


def _require_roles(allowed_roles: set[str], action_label: str) -> None:
	user_roles = set(frappe.get_roles())
	if allowed_roles.isdisjoint(user_roles):
		frappe.throw(f"You do not have permission to {action_label}.")


def _format_row_timestamps(row: dict[str, Any], *fieldnames: str) -> dict[str, Any]:
	for fieldname in fieldnames:
		if row.get(fieldname):
			row[f"{fieldname}_display"] = format_datetime(row[fieldname])
	return row


def _get_latest_record(doctype: str, filters: dict[str, Any], fields: list[str], order_by: str) -> dict[str, Any] | None:
	rows = frappe.get_all(
		doctype,
		filters=filters,
		fields=fields,
		order_by=order_by,
		limit_page_length=1,
	)
	return rows[0] if rows else None


@frappe.whitelist()
def get_tenant_business_summary(tenant: str) -> dict[str, Any]:
	subscription = _get_latest_record(
		"Tenant Subscription",
		{"tenant": tenant},
		["name", "plan_name", "subscription_tier", "status", "start_date", "end_date", "billing_cycle", "price", "currency"],
		"modified desc",
	)
	usage_snapshot = _get_latest_record(
		"Tenant Usage Snapshot",
		{"tenant": tenant},
		["name", "environment", "snapshot_on", "active_users_30d", "storage_used_gb", "request_count", "peak_concurrency_estimate"],
		"snapshot_on desc",
	)
	cost_snapshot = _get_latest_record(
		"Tenant Cost Snapshot",
		{"tenant": tenant},
		["name", "environment", "snapshot_on", "db_cost_estimate", "storage_cost_estimate", "compute_cost_estimate", "backup_cost_estimate", "total_cost_estimate", "currency"],
		"snapshot_on desc",
	)

	if usage_snapshot:
		_format_row_timestamps(usage_snapshot, "snapshot_on")
	if cost_snapshot:
		_format_row_timestamps(cost_snapshot, "snapshot_on")

	return {
		"subscription": subscription,
		"usage_snapshot": usage_snapshot,
		"cost_snapshot": cost_snapshot,
	}


@frappe.whitelist()
def get_environment_business_summary(environment: str) -> dict[str, Any]:
	usage_snapshot = _get_latest_record(
		"Tenant Usage Snapshot",
		{"environment": environment},
		["name", "tenant", "snapshot_on", "active_users_30d", "storage_used_gb", "request_count", "avg_concurrency_estimate", "peak_concurrency_estimate", "queue_jobs_processed"],
		"snapshot_on desc",
	)
	cost_snapshot = _get_latest_record(
		"Tenant Cost Snapshot",
		{"environment": environment},
		["name", "tenant", "snapshot_on", "db_cost_estimate", "storage_cost_estimate", "compute_cost_estimate", "backup_cost_estimate", "total_cost_estimate", "currency"],
		"snapshot_on desc",
	)

	if usage_snapshot:
		_format_row_timestamps(usage_snapshot, "snapshot_on")
	if cost_snapshot:
		_format_row_timestamps(cost_snapshot, "snapshot_on")

	return {
		"usage_snapshot": usage_snapshot,
		"cost_snapshot": cost_snapshot,
	}


@frappe.whitelist()
def record_tenant_subscription(
	tenant: str,
	plan_name: str | None = None,
	subscription_tier: str | None = None,
	status: str | None = None,
	start_date: str | None = None,
	end_date: str | None = None,
	billing_cycle: str | None = None,
	price: float | None = None,
	currency: str | None = None,
	notes: str | None = None,
) -> dict[str, Any]:
	_require_roles(SUBSCRIPTION_ROLES, "record tenant subscriptions")

	subscription = frappe.get_doc(
		{
			"doctype": "Tenant Subscription",
			"tenant": tenant,
			"plan_name": plan_name,
			"subscription_tier": subscription_tier,
			"status": status,
			"start_date": start_date,
			"end_date": end_date,
			"billing_cycle": billing_cycle,
			"price": price,
			"currency": currency,
			"notes": notes,
		}
	)
	subscription.insert()
	return {"name": subscription.name, "doctype": subscription.doctype}


@frappe.whitelist()
def record_usage_snapshot(
	tenant: str | None = None,
	environment: str | None = None,
	snapshot_on: str | None = None,
	active_users_30d: int | None = None,
	storage_used_gb: float | None = None,
	file_count: int | None = None,
	request_count: int | None = None,
	avg_concurrency_estimate: float | None = None,
	peak_concurrency_estimate: float | None = None,
	queue_jobs_processed: int | None = None,
	notes: str | None = None,
) -> dict[str, Any]:
	_require_roles(SNAPSHOT_ROLES, "record usage snapshots")

	tenant_name = tenant
	if environment and not tenant_name:
		tenant_name = frappe.db.get_value("Tenant Environment", environment, "tenant")

	snapshot = frappe.get_doc(
		{
			"doctype": "Tenant Usage Snapshot",
			"tenant": tenant_name,
			"environment": environment,
			"snapshot_on": snapshot_on or now_datetime(),
			"active_users_30d": active_users_30d,
			"storage_used_gb": storage_used_gb,
			"file_count": file_count,
			"request_count": request_count,
			"avg_concurrency_estimate": avg_concurrency_estimate,
			"peak_concurrency_estimate": peak_concurrency_estimate,
			"queue_jobs_processed": queue_jobs_processed,
			"notes": notes,
		}
	)
	snapshot.insert()

	if environment:
		environment_doc = frappe.get_doc("Tenant Environment", environment)
		environment_doc.usage_snapshot_on = snapshot.snapshot_on
		environment_doc.save()

	return {"name": snapshot.name, "doctype": snapshot.doctype}


@frappe.whitelist()
def record_cost_snapshot(
	tenant: str | None = None,
	environment: str | None = None,
	snapshot_on: str | None = None,
	db_cost_estimate: float | None = None,
	storage_cost_estimate: float | None = None,
	compute_cost_estimate: float | None = None,
	backup_cost_estimate: float | None = None,
	total_cost_estimate: float | None = None,
	currency: str | None = None,
	notes: str | None = None,
) -> dict[str, Any]:
	_require_roles(SNAPSHOT_ROLES | {"Ifitwala Press Finance"}, "record cost snapshots")

	tenant_name = tenant
	if environment and not tenant_name:
		tenant_name = frappe.db.get_value("Tenant Environment", environment, "tenant")

	snapshot = frappe.get_doc(
		{
			"doctype": "Tenant Cost Snapshot",
			"tenant": tenant_name,
			"environment": environment,
			"snapshot_on": snapshot_on or now_datetime(),
			"db_cost_estimate": db_cost_estimate,
			"storage_cost_estimate": storage_cost_estimate,
			"compute_cost_estimate": compute_cost_estimate,
			"backup_cost_estimate": backup_cost_estimate,
			"total_cost_estimate": total_cost_estimate,
			"currency": currency,
			"notes": notes,
		}
	)
	snapshot.insert()

	if environment:
		environment_doc = frappe.get_doc("Tenant Environment", environment)
		environment_doc.estimated_monthly_cost = snapshot.total_cost_estimate
		environment_doc.save()

	return {"name": snapshot.name, "doctype": snapshot.doctype}
