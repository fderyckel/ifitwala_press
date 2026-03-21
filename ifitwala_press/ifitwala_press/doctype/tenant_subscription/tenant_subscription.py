from __future__ import annotations

import frappe
from frappe.model.document import Document


class TenantSubscription(Document):
	def validate(self) -> None:
		if self.start_date and self.end_date and self.end_date < self.start_date:
			frappe.throw("End Date cannot be before Start Date.")
