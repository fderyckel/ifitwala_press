from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import now_datetime


def create_transition_log(
	*,
	tenant: str | None,
	environment: str | None,
	from_state: str | None,
	to_state: str | None,
	trigger_type: str = "Manual",
	success: bool = True,
	message: str | None = None,
	job_id: str | None = None,
	details: dict[str, Any] | None = None,
) -> Any:
	log = frappe.get_doc(
		{
			"doctype": "Tenant Transition Log",
			"tenant": tenant,
			"environment": environment,
			"from_state": from_state,
			"to_state": to_state,
			"trigger_type": trigger_type,
			"triggered_by": frappe.session.user if trigger_type == "Manual" else None,
			"job_id": job_id,
			"success": 1 if success else 0,
			"message": message,
			"details_json": frappe.as_json(details or {}),
			"transition_on": now_datetime(),
		}
	)
	log.insert()
	return log
