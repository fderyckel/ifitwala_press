from __future__ import annotations

import frappe
from frappe.model.document import Document


class TenantCostSnapshot(Document):
	def validate(self) -> None:
		if not self.tenant and not self.environment:
			frappe.throw("Tenant or Environment is required for a cost snapshot.")

		component_total = sum(
			float(value or 0)
			for value in (
				self.db_cost_estimate,
				self.storage_cost_estimate,
				self.compute_cost_estimate,
				self.backup_cost_estimate,
			)
		)

		if component_total and not self.total_cost_estimate:
			self.total_cost_estimate = component_total
