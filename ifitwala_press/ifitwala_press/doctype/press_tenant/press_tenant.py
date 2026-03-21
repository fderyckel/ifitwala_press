from __future__ import annotations

import re

import frappe
from frappe.model.document import Document


TENANT_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class PressTenant(Document):
	def validate(self) -> None:
		self._normalize_tenant_slug()
		self._validate_contract_dates()
		self._validate_vip_constraints()

	def _normalize_tenant_slug(self) -> None:
		if not self.tenant_slug:
			return

		normalized = re.sub(r"[^a-z0-9-]+", "-", self.tenant_slug.strip().lower().replace("_", "-"))
		normalized = re.sub(r"-{2,}", "-", normalized).strip("-")
		self.tenant_slug = normalized

		if not self.tenant_slug or not TENANT_SLUG_PATTERN.fullmatch(self.tenant_slug):
			frappe.throw("Tenant Slug must use lowercase letters, numbers, and hyphens only.")

	def _validate_contract_dates(self) -> None:
		if self.contract_start_date and self.contract_end_date and self.contract_end_date < self.contract_start_date:
			frappe.throw("Contract End Date cannot be before Contract Start Date.")

	def _validate_vip_constraints(self) -> None:
		if self.vip_flag and self.subscription_tier == "Sandbox":
			frappe.throw("VIP tenants cannot use the Sandbox subscription tier.")

		if self.subscription_tier == "VIP" and self.default_hosting_tier == "Shared":
			frappe.throw("VIP subscription tier cannot use Shared as the default hosting tier.")
