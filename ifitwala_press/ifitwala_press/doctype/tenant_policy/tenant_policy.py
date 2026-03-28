from __future__ import annotations

import frappe
from frappe.model.document import Document


class TenantPolicy(Document):
	def validate(self) -> None:
		self._validate_quota_values()
		self._validate_lifecycle_rules()
		self._validate_backup_rules()
		self._validate_provider_defaults()
		self._validate_storage_defaults()
		self._validate_policy_constraints()

	def _validate_quota_values(self) -> None:
		for fieldname, label in (
			("worker_quota", "Worker Quota"),
			("web_quota", "Web Quota"),
			("storage_quota_gb", "Storage Quota (GB)"),
			("max_background_jobs", "Max Background Jobs"),
			("max_file_size_mb", "Max File Size (MB)"),
			("sandbox_expiry_days", "Sandbox Expiry Days"),
			("grace_period_days", "Grace Period Days"),
			("backup_retention_days", "Backup Retention Days"),
			("restore_test_frequency_days", "Restore Test Frequency Days"),
		):
			value = self.get(fieldname)
			if value is not None and value != "" and float(value) < 0:
				frappe.throw(f"{label} cannot be negative.")

	def _validate_lifecycle_rules(self) -> None:
		if self.policy_type == "Sandbox" and self.sandbox_expiry_days in (None, ""):
			frappe.throw("Sandbox Expiry Days is required for Sandbox policies.")

		if self.requires_fresh_production_site and self.allow_in_place_upgrade:
			frappe.throw("A policy that requires a fresh production site cannot allow in-place upgrade.")

	def _validate_backup_rules(self) -> None:
		if self.backup_frequency == "None" and self.backup_retention_days:
			frappe.throw("Backup Retention Days must be empty when Backup Frequency is None.")

		if self.requires_restore_test and self.backup_frequency == "None":
			frappe.throw("Restore tests require a backup frequency other than None.")

		if self.requires_restore_test and not self.restore_test_frequency_days:
			frappe.throw("Restore Test Frequency Days is required when Requires Restore Test is enabled.")

	def _validate_provider_defaults(self) -> None:
		if self.policy_type != "Sandbox" and self.default_primary_cloud_provider == "OVH":
			frappe.throw("Only Sandbox policies can default Primary Cloud Provider to OVH.")

		if self.policy_type != "Sandbox" and self.default_runtime_provider == "OVH":
			frappe.throw("Only Sandbox policies can default Runtime Provider to OVH.")

		if self.default_file_storage_provider == "GCS" and self.default_object_storage_provider != "Google Cloud":
			frappe.throw("GCS file storage requires Default Object Storage Provider to be Google Cloud.")

		if self.default_backup_storage_provider == "GCS" and self.default_object_storage_provider != "Google Cloud":
			frappe.throw("GCS backup storage requires Default Object Storage Provider to be Google Cloud.")

	def _validate_storage_defaults(self) -> None:
		if self.default_file_storage_provider == "Local Temporary" and self.policy_type != "Sandbox":
			frappe.throw("Only Sandbox policies can default File Storage Provider to Local Temporary.")

		if self.default_file_storage_provider == "GCS" and self.default_file_storage_class != "Frequent Access":
			frappe.throw("GCS file storage must use Frequent Access for live site files.")

		if self.backup_frequency != "None" and not self.default_backup_storage_provider:
			frappe.throw("Default Backup Storage Provider is required when backups are enabled.")

		if self.backup_frequency != "None" and not self.default_backup_storage_class:
			frappe.throw("Default Backup Storage Class is required when backups are enabled.")

		if self.backup_frequency != "None" and self.default_backup_storage_provider == "Local Temporary":
			frappe.throw("Retained backups cannot use Local Temporary storage.")

		if self.default_backup_storage_provider == "GCS" and self.default_backup_storage_class != "Infrequent Access":
			frappe.throw("GCS backup storage must use Infrequent Access for daily retained backups.")

	def _validate_policy_constraints(self) -> None:
		if self.policy_type == "VIP" and self.default_database_mode == "Shared DB Fleet":
			frappe.throw("VIP policies cannot default to the Shared DB Fleet database mode.")

		if self.policy_type == "Sandbox" and self.default_database_mode == "Dedicated DB Instance":
			frappe.throw("Sandbox policies cannot default to Dedicated DB Instance.")
