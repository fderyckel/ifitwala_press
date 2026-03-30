from __future__ import annotations

from datetime import date
from typing import Any

import frappe
from frappe.utils import format_datetime

from ifitwala_press.api.permission import ensure_app_permission

LIFECYCLE_ORDER = (
	"Lead",
	"Sandbox Provisioning",
	"Sandbox Active",
	"Sandbox Expired",
	"Production Qualification",
	"Production Provisioning",
	"Live",
	"Suspended",
	"Archived",
	"Provisioning Failed",
)
CAPACITY_ALERT_STATES = {"Warning", "Critical", "Saturated"}
SUSPENDED = "Suspended"
ARCHIVED = "Archived"
PROVISIONING_FAILED = "Provisioning Failed"
LIVE = "Live"
SANDBOX = "Sandbox"


def _coerce_date(value: Any) -> date | None:
	if not value:
		return None

	if isinstance(value, date):
		return value

	return date.fromisoformat(str(value))


def _days_until(value: Any, *, as_of: date) -> int | None:
	target = _coerce_date(value)
	if not target:
		return None
	return (target - as_of).days


def _money(value: Any) -> float:
	try:
		return float(value or 0)
	except TypeError:
		return 0.0
	except ValueError:
		return 0.0


def _build_control_plane_home(
	*,
	tenants: list[dict[str, Any]],
	environments: list[dict[str, Any]],
	as_of: date,
) -> dict[str, Any]:
	active_environments = [row for row in environments if row.get("site_status") != ARCHIVED]
	renewal_candidates = [
		row
		for row in tenants
		if row.get("tenant_status") != ARCHIVED
		and row.get("subscription_status") not in {"Expired", "Cancelled"}
		and (days := _days_until(row.get("contract_end_date"), as_of=as_of)) is not None
		and 0 <= days <= 30
	]
	lifecycle_counts = [
		{
			"state": state,
			"count": sum(1 for row in environments if row.get("site_status") == state),
		}
		for state in LIFECYCLE_ORDER
	]
	top_cost_environments = sorted(
		[
			{
				"name": row.get("name"),
				"tenant": row.get("tenant"),
				"environment_name": row.get("environment_name") or row.get("site_name"),
				"site_status": row.get("site_status"),
				"estimated_monthly_cost": _money(row.get("estimated_monthly_cost")),
			}
			for row in active_environments
			if _money(row.get("estimated_monthly_cost")) > 0
		],
		key=lambda row: row["estimated_monthly_cost"],
		reverse=True,
	)[:5]
	attention_items: list[dict[str, Any]] = []

	for row in environments:
		environment_name = row.get("environment_name") or row.get("site_name") or row.get("name")
		route = ["Form", "Tenant Environment", row.get("name")]
		site_status = row.get("site_status")
		capacity_state = row.get("capacity_state")
		health_score = row.get("health_score")

		if site_status == PROVISIONING_FAILED:
			attention_items.append(
				{
					"priority": 0,
					"indicator": "red",
					"title": "Provisioning failed",
					"detail": environment_name,
					"route": route,
				}
			)

		if capacity_state in {"Critical", "Saturated"}:
			attention_items.append(
				{
					"priority": 1,
					"indicator": "red",
					"title": f"{capacity_state} capacity",
					"detail": environment_name,
					"route": route,
				}
			)
		elif capacity_state == "Warning":
			attention_items.append(
				{
					"priority": 2,
					"indicator": "orange",
					"title": "Capacity warning",
					"detail": environment_name,
					"route": route,
				}
			)

		try:
			health_value = float(health_score) if health_score is not None else None
		except TypeError:
			health_value = None
		except ValueError:
			health_value = None
		if health_value is not None and health_value < 50:
			attention_items.append(
				{
					"priority": 3,
					"indicator": "orange",
					"title": "Low health score",
					"detail": f"{environment_name} ({health_value:.0f})",
					"route": route,
				}
			)

		expires_in_days = _days_until(row.get("expires_on"), as_of=as_of)
		if (
			row.get("environment_type") == SANDBOX
			and site_status not in {ARCHIVED, "Sandbox Expired"}
			and expires_in_days is not None
		):
			if expires_in_days < 0:
				attention_items.append(
					{
						"priority": 4,
						"indicator": "red",
						"title": "Sandbox past expiry",
						"detail": environment_name,
						"route": route,
					}
				)
			elif expires_in_days <= 7:
				attention_items.append(
					{
						"priority": 5,
						"indicator": "orange",
						"title": "Sandbox expires soon",
						"detail": f"{environment_name} ({expires_in_days}d)",
						"route": route,
					}
				)

	for row in tenants:
		route = ["Form", "Press Tenant", row.get("name")]
		tenant_name = row.get("tenant_name") or row.get("name")
		if row.get("vip_flag") and row.get("tenant_status") == SUSPENDED:
			attention_items.append(
				{
					"priority": 1,
					"indicator": "red",
					"title": "Suspended VIP tenant",
					"detail": tenant_name,
					"route": route,
				}
			)

		renewal_days = _days_until(row.get("contract_end_date"), as_of=as_of)
		if (
			row.get("tenant_status") != ARCHIVED
			and row.get("subscription_status") not in {"Expired", "Cancelled"}
			and renewal_days is not None
			and 0 <= renewal_days <= 30
		):
			attention_items.append(
				{
					"priority": 6,
					"indicator": "blue",
					"title": "Contract renewal due soon",
					"detail": f"{tenant_name} ({renewal_days}d)",
					"route": route,
				}
			)

	attention_items.sort(key=lambda row: (row["priority"], row["title"], row["detail"]))

	return {
		"summary_cards": [
			{"label": "Total Tenants", "value": len(tenants), "indicator": "blue"},
			{
				"label": "Live Environments",
				"value": sum(1 for row in environments if row.get("site_status") == LIVE),
				"indicator": "green",
			},
			{
				"label": "Sandbox Environments",
				"value": sum(1 for row in active_environments if row.get("environment_type") == SANDBOX),
				"indicator": "blue",
			},
			{
				"label": "Capacity Alerts",
				"value": sum(
					1 for row in active_environments if row.get("capacity_state") in CAPACITY_ALERT_STATES
				),
				"indicator": "orange",
			},
			{
				"label": "Provisioning Failures",
				"value": sum(1 for row in environments if row.get("site_status") == PROVISIONING_FAILED),
				"indicator": "red",
			},
			{
				"label": "Renewals Due Soon",
				"value": len(renewal_candidates),
				"indicator": "blue",
			},
			{
				"label": "Total Estimated Monthly Cost",
				"value": round(
					sum(_money(row.get("estimated_monthly_cost")) for row in active_environments), 2
				),
				"indicator": "purple",
				"is_currency": True,
			},
		],
		"lifecycle_overview": lifecycle_counts,
		"attention_queue": attention_items[:12],
		"top_cost_environments": top_cost_environments,
	}


@frappe.whitelist()
def get_tenant_environment_panel(tenant: str) -> dict[str, Any]:
	ensure_app_permission("view Ifitwala Press tenant environment panels")
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
	ensure_app_permission("view Ifitwala Press transition history")
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


@frappe.whitelist()
def get_control_plane_home() -> dict[str, Any]:
	ensure_app_permission("view the Ifitwala Press control plane home")
	tenants = frappe.get_all(
		"Press Tenant",
		fields=[
			"name",
			"tenant_name",
			"tenant_status",
			"subscription_status",
			"contract_end_date",
			"vip_flag",
		],
		order_by="modified desc",
	)
	environments = frappe.get_all(
		"Tenant Environment",
		fields=[
			"name",
			"tenant",
			"environment_name",
			"environment_type",
			"site_name",
			"site_status",
			"capacity_state",
			"health_score",
			"estimated_monthly_cost",
			"expires_on",
		],
		order_by="modified desc",
	)
	return _build_control_plane_home(tenants=tenants, environments=environments, as_of=date.today())
