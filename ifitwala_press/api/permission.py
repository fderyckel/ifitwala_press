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
