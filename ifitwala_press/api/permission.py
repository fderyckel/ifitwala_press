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
	return any(frappe.has_role(role_name) for role_name in PRESS_APP_ROLES)
