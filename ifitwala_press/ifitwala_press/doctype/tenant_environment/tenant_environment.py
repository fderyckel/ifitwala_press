from __future__ import annotations

import re

import frappe
from frappe.model.document import Document

SITE_NAME_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$")
LIVE_STATE = "Live"


class TenantEnvironment(Document):
	def validate(self) -> None:
		self._normalize_site_name()
		self._normalize_runtime_fields()
		self._validate_demo_seed_configuration()
		self._validate_hosting_and_database_constraints()
		self._validate_routing_constraints()
		self._validate_live_requirements()

	def _normalize_site_name(self) -> None:
		if not self.site_name:
			return

		self.site_name = self.site_name.strip().lower()
		if not SITE_NAME_PATTERN.fullmatch(self.site_name):
			frappe.throw("Site Name must use lowercase letters, numbers, dots, and hyphens only.")

	def _normalize_runtime_fields(self) -> None:
		for fieldname in (
			"frappe_branch",
			"ifitwala_ed_branch",
			"ifitwala_drive_branch",
			"worker_profile",
			"demo_seed_reference",
			"runtime_reference",
			"backup_export_path",
		):
			value = self.get(fieldname)
			if isinstance(value, str):
				self.set(fieldname, value.strip())

	def _validate_demo_seed_configuration(self) -> None:
		if self.demo_seed_mode == "Restore Demo Backup" and not self.demo_seed_reference:
			frappe.throw("Demo Seed Reference is required when Demo Seed Mode is Restore Demo Backup.")

	def _validate_hosting_and_database_constraints(self) -> None:
		if self.hosting_tier == "VIP" and self.database_mode == "Shared DB Fleet":
			frappe.throw("VIP hosting tier cannot use the Shared DB Fleet database mode.")

		if self.database_mode == "Dedicated DB Instance" and not self.db_instance_name:
			frappe.throw("DB Instance Name is required for Dedicated DB Instance mode.")

	def _validate_routing_constraints(self) -> None:
		if self.routing_mode == "Public" and not self.primary_domain:
			frappe.throw("Primary Domain is required when Routing Mode is Public.")

	def _validate_live_requirements(self) -> None:
		if self.site_status != LIVE_STATE:
			return

		if not self.policy:
			frappe.throw("Policy is required before an environment can be marked Live.")

		if not self.deployment_mode:
			frappe.throw("Deployment Mode is required before an environment can be marked Live.")

		if not self.database_mode:
			frappe.throw("Database Mode is required before an environment can be marked Live.")

		if not self.ifitwala_ed_branch:
			frappe.throw("Ifitwala Ed Branch is required before an environment can be marked Live.")

		if self.database_mode == "Dedicated DB Instance" and not self.db_instance_name:
			frappe.throw("DB Instance Name is required before a dedicated environment can be marked Live.")
