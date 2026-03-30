from __future__ import annotations

import frappe

PRESS_ROLES = (
	"Ifitwala Press Admin",
	"Ifitwala Press Ops",
	"Ifitwala Press Support",
	"Ifitwala Press Sales",
	"Ifitwala Press Finance",
)


def after_install() -> None:
	ensure_press_roles()


def before_tests() -> None:
	ensure_press_roles()


def ensure_press_roles() -> None:
	for role_name in PRESS_ROLES:
		if frappe.db.exists("Role", role_name):
			continue

		role = frappe.get_doc(
			{
				"doctype": "Role",
				"role_name": role_name,
				"desk_access": 1,
			}
		)
		role.insert(ignore_permissions=True)
