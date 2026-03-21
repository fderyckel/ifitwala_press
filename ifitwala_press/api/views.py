from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import format_datetime


@frappe.whitelist()
def get_tenant_environment_panel(tenant: str) -> dict[str, Any]:
	environments = frappe.get_all(
		"Tenant Environment",
		filters={"tenant": tenant},
		fields=[
			"name",
			"environment_name",
			"environment_type",
			"site_status",
			"site_name",
			"hosting_tier",
			"primary_domain",
			"health_score",
			"capacity_state",
		],
		order_by="modified desc",
	)

	return {"environments": environments}


@frappe.whitelist()
def get_environment_transition_history(environment: str, limit: int = 10) -> dict[str, Any]:
	transition_logs = frappe.get_all(
		"Tenant Transition Log",
		filters={"environment": environment},
		fields=[
			"name",
			"from_state",
			"to_state",
			"trigger_type",
			"triggered_by",
			"success",
			"message",
			"transition_on",
		],
		order_by="transition_on desc",
		limit_page_length=limit,
	)

	for row in transition_logs:
		if row.get("transition_on"):
			row["transition_on_display"] = format_datetime(row["transition_on"])

	return {"transition_logs": transition_logs}
