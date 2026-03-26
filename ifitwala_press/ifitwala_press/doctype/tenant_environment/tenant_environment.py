from __future__ import annotations

import re

import frappe
from frappe.model.document import Document

SITE_NAME_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$")
LIVE_STATE = "Live"
S3_COMPATIBLE = "S3 Compatible"
LOCAL_TEMPORARY = "Local Temporary"
FREQUENT_ACCESS = "Frequent Access"
INFREQUENT_ACCESS = "Infrequent Access"
GCS = "GCS"
GOOGLE_CLOUD = "Google Cloud"
OVH = "OVH"
GOOGLE_CLOUD_DNS = "Google Cloud DNS"


class TenantEnvironment(Document):
	def validate(self) -> None:
		self._normalize_site_name()
		self._normalize_runtime_fields()
		self._validate_demo_seed_configuration()
		self._validate_hosting_and_database_constraints()
		self._validate_provider_constraints()
		self._validate_storage_constraints()
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
			"primary_cloud_provider",
			"runtime_provider",
			"object_storage_provider",
			"dns_provider",
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

	def _validate_provider_constraints(self) -> None:
		if self.environment_type != "Sandbox" and self.primary_cloud_provider == OVH:
			frappe.throw("Only sandbox environments can currently place Primary Cloud Provider on OVH.")

		if self.environment_type != "Sandbox" and self.runtime_provider == OVH:
			frappe.throw("Only sandbox environments can currently place Runtime Provider on OVH.")

		if self.file_storage_provider == GCS and self.object_storage_provider != GOOGLE_CLOUD:
			frappe.throw("GCS file storage requires Object Storage Provider to be Google Cloud.")

		if self.backup_storage_provider == GCS and self.object_storage_provider != GOOGLE_CLOUD:
			frappe.throw("GCS backup storage requires Object Storage Provider to be Google Cloud.")

	def _validate_storage_constraints(self) -> None:
		if self.file_storage_provider == LOCAL_TEMPORARY and self.environment_type != "Sandbox":
			frappe.throw("Only sandbox environments can use Local Temporary file storage.")

		if self.file_storage_provider == S3_COMPATIBLE and self.file_storage_class != FREQUENT_ACCESS:
			frappe.throw("S3-compatible file storage must use Frequent Access for live site files in phase 1.")

		if bool(self.backup_storage_provider) != bool(self.backup_storage_class):
			frappe.throw("Backup Storage Provider and Backup Storage Class must be set together.")

		if self.backup_storage_provider == LOCAL_TEMPORARY:
			frappe.throw("Retained backups cannot use Local Temporary storage.")

		if self.backup_storage_provider == S3_COMPATIBLE and self.backup_storage_class != INFREQUENT_ACCESS:
			frappe.throw("S3-compatible backup storage must use Infrequent Access for phase-1 daily backups.")

		if self.policy:
			policy_doc = frappe.get_doc("Tenant Policy", self.policy)
			if policy_doc.backup_frequency != "None" and not self.backup_storage_provider:
				frappe.throw("Backup Storage Provider is required when the linked policy retains backups.")

	def _validate_routing_constraints(self) -> None:
		if self.routing_mode == "Public" and not self.primary_domain:
			frappe.throw("Primary Domain is required when Routing Mode is Public.")

		if self.routing_mode == "Public" and not self.dns_provider:
			frappe.throw("DNS Provider is required when Routing Mode is Public.")

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

		if not self.ifitwala_drive_branch:
			frappe.throw("Ifitwala Drive Branch is required before an environment can be marked Live.")

		if not self.primary_cloud_provider:
			frappe.throw("Primary Cloud Provider is required before an environment can be marked Live.")

		if not self.runtime_provider:
			frappe.throw("Runtime Provider is required before an environment can be marked Live.")

		if not self.object_storage_provider:
			frappe.throw("Object Storage Provider is required before an environment can be marked Live.")

		if not self.dns_provider:
			frappe.throw("DNS Provider is required before an environment can be marked Live.")

		if self.primary_cloud_provider != GOOGLE_CLOUD:
			frappe.throw("Primary Cloud Provider must be Google Cloud before an environment can be marked Live.")

		if self.runtime_provider != GOOGLE_CLOUD:
			frappe.throw("Runtime Provider must be Google Cloud before an environment can be marked Live.")

		if self.object_storage_provider != GOOGLE_CLOUD:
			frappe.throw("Object Storage Provider must be Google Cloud before an environment can be marked Live.")

		if self.dns_provider != GOOGLE_CLOUD_DNS:
			frappe.throw("DNS Provider must be Google Cloud DNS before an environment can be marked Live.")

		if self.file_storage_provider != S3_COMPATIBLE:
			frappe.throw("File Storage Provider must be S3 Compatible before an environment can be marked Live.")

		if self.file_storage_class != FREQUENT_ACCESS:
			frappe.throw("File Storage Class must be Frequent Access before an environment can be marked Live.")

		if self.backup_storage_provider != S3_COMPATIBLE:
			frappe.throw("Backup Storage Provider must be S3 Compatible before an environment can be marked Live.")

		if self.backup_storage_class != INFREQUENT_ACCESS:
			frappe.throw("Backup Storage Class must be Infrequent Access before an environment can be marked Live.")

		policy_doc = frappe.get_doc("Tenant Policy", self.policy)
		if policy_doc.backup_frequency == "None":
			frappe.throw("Policy must retain backups before an environment can be marked Live.")

		if self.database_mode == "Dedicated DB Instance" and not self.db_instance_name:
			frappe.throw("DB Instance Name is required before a dedicated environment can be marked Live.")
