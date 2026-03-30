from __future__ import annotations

import frappe

PRESS_APP_ROLES = (
	"Ifitwala Press Admin",
	"Ifitwala Press Ops",
	"Ifitwala Press Support",
	"Ifitwala Press Sales",
	"Ifitwala Press Finance",
)


def has_app_permission() -> bool:
	user_roles = set(frappe.get_roles())
	return not set(PRESS_APP_ROLES).isdisjoint(user_roles)


def ensure_app_permission(action_label: str = "access Ifitwala Press") -> None:
	if has_app_permission():
		return

	frappe.throw(f"You do not have permission to {action_label}.")
