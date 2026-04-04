from __future__ import annotations

import frappe
from frappe.model.document import Document


class RuntimePool(Document):
	def validate(self) -> None:
		self._normalize_text_fields()
		self._validate_capacity_values()

	def _normalize_text_fields(self) -> None:
		for fieldname in (
			"pool_name",
			"region",
			"pool_reference",
			"host_reference",
			"compatibility_key",
			"notes",
		):
			value = self.get(fieldname)
			if isinstance(value, str):
				self.set(fieldname, value.strip())

	def _validate_capacity_values(self) -> None:
		for fieldname, label in (
			("site_capacity", "Site Capacity"),
			("assigned_site_count", "Assigned Site Count"),
		):
			value = self.get(fieldname)
			if value is not None and value != "" and int(value) < 0:
				frappe.throw(f"{label} cannot be negative.")

		if (
			self.site_capacity not in (None, "")
			and self.assigned_site_count not in (None, "")
			and int(self.assigned_site_count) > int(self.site_capacity)
		):
			frappe.throw("Assigned Site Count cannot exceed Site Capacity.")
