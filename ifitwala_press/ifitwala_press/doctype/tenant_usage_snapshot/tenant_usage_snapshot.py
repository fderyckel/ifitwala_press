from __future__ import annotations

import frappe
from frappe.model.document import Document


class TenantUsageSnapshot(Document):
	def validate(self) -> None:
		if not self.tenant and not self.environment:
			frappe.throw("Tenant or Environment is required for a usage snapshot.")
