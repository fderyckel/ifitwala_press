from __future__ import annotations

import frappe
from frappe.model.document import Document


class TenantTransitionLog(Document):
	def validate(self) -> None:
		self._validate_append_only()
		self._validate_transition_shape()
		self._validate_manual_trigger()
		self._validate_failure_message()

	def _validate_append_only(self) -> None:
		if not self.is_new():
			frappe.throw("Tenant Transition Log is append-only and cannot be edited after creation.")

	def _validate_transition_shape(self) -> None:
		if self.from_state and self.to_state and self.from_state == self.to_state:
			frappe.throw("From State and To State cannot be identical in Tenant Transition Log.")

	def _validate_manual_trigger(self) -> None:
		if self.trigger_type == "Manual" and not self.triggered_by:
			frappe.throw("Triggered By is required when Trigger Type is Manual.")

	def _validate_failure_message(self) -> None:
		if not self.success and not self.message:
			frappe.throw("Message is required when Success is unchecked.")
