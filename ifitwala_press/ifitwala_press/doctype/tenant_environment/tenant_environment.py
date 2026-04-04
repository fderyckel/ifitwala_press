from __future__ import annotations

import ipaddress
import re

import frappe
from frappe.model.document import Document

SITE_NAME_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$")
LIVE_STATE = "Live"
LOCAL_TEMPORARY = "Local Temporary"
FREQUENT_ACCESS = "Frequent Access"
INFREQUENT_ACCESS = "Infrequent Access"
GCS = "GCS"
GOOGLE_CLOUD = "Google Cloud"
OVH = "OVH"
GOOGLE_CLOUD_DNS = "Google Cloud DNS"
SHARED_RUNTIME = "Shared Runtime"
RESERVED_RUNTIME = "Reserved Runtime"
DEDICATED_RUNTIME = "Dedicated Runtime"
LIFECYCLE_GUARD_FLAG = "ifitwala_allow_lifecycle_transition"


class TenantEnvironment(Document):
	def validate(self) -> None:
		self._normalize_site_name()
		self._validate_lifecycle_edit_discipline()
		self._normalize_runtime_fields()
		self._apply_runtime_pool_defaults()
		self._validate_demo_seed_configuration()
		self._validate_hosting_and_database_constraints()
		self._validate_runtime_placement_constraints()
		self._validate_provider_constraints()
		self._validate_storage_constraints()
		self._validate_routing_constraints()
		self._validate_ingress_access_constraints()
		self._validate_live_requirements()

	def _normalize_site_name(self) -> None:
		if not self.site_name:
			return

		self.site_name = self.site_name.strip().lower()
		if not SITE_NAME_PATTERN.fullmatch(self.site_name):
			frappe.throw("Site Name must use lowercase letters, numbers, dots, and hyphens only.")

	def _validate_lifecycle_edit_discipline(self) -> None:
		if self.is_new():
			return

		allow_transition = bool(getattr(getattr(self, "flags", None), LIFECYCLE_GUARD_FLAG, False))
		if allow_transition:
			return

		previous = self.get_doc_before_save()
		if not previous:
			return

		if getattr(previous, "site_status", None) != getattr(self, "site_status", None):
			frappe.throw("Site Status must be changed through Ifitwala Press lifecycle actions.")

		if getattr(previous, "last_transition_on", None) != getattr(self, "last_transition_on", None):
			frappe.throw("Last Transition On is system-managed and cannot be edited directly.")

		if getattr(previous, "last_transition_by", None) != getattr(self, "last_transition_by", None):
			frappe.throw("Last Transition By is system-managed and cannot be edited directly.")

	def _normalize_runtime_fields(self) -> None:
		for fieldname in (
			"frappe_branch",
			"ifitwala_ed_branch",
			"ifitwala_drive_branch",
			"worker_profile",
			"demo_seed_reference",
			"runtime_reference",
			"runtime_pool",
			"dedicated_runtime_target",
			"backup_export_path",
			"deployment_mode",
			"deployment_mode_notes",
			"primary_cloud_provider",
			"runtime_provider",
			"object_storage_provider",
			"dns_provider",
			"primary_domain",
			"host_header_value",
			"ingress_access_mode",
			"region",
			"db_instance_name",
			"db_name",
			"db_user",
		):
			value = self.get(fieldname)
			if isinstance(value, str):
				self.set(fieldname, value.strip())

		for row in self.get("ingress_allowlist") or []:
			cidr = getattr(row, "cidr", None)
			if isinstance(cidr, str):
				row.cidr = cidr.strip()
			notes = getattr(row, "notes", None)
			if isinstance(notes, str):
				row.notes = notes.strip()

	def _apply_runtime_pool_defaults(self) -> None:
		if not self.runtime_pool:
			return

		pool_doc = frappe.get_doc("Runtime Pool", self.runtime_pool)

		if not self.region and getattr(pool_doc, "region", None):
			self.region = pool_doc.region

		if not self.primary_cloud_provider and getattr(pool_doc, "primary_cloud_provider", None):
			self.primary_cloud_provider = pool_doc.primary_cloud_provider

		if not self.runtime_provider and getattr(pool_doc, "runtime_provider", None):
			self.runtime_provider = pool_doc.runtime_provider

	def _validate_demo_seed_configuration(self) -> None:
		if self.demo_seed_mode == "Restore Demo Backup" and not self.demo_seed_reference:
			frappe.throw("Demo Seed Reference is required when Demo Seed Mode is Restore Demo Backup.")

	def _validate_hosting_and_database_constraints(self) -> None:
		if self.hosting_tier == "VIP" and self.database_mode == "Shared DB Fleet":
			frappe.throw("VIP hosting tier cannot use the Shared DB Fleet database mode.")

		if self.database_mode == "Dedicated DB Instance" and not self.db_instance_name:
			frappe.throw("DB Instance Name is required for Dedicated DB Instance mode.")

	def _validate_runtime_placement_constraints(self) -> None:
		if not self.deployment_mode:
			if self.runtime_pool or self.dedicated_runtime_target:
				frappe.throw("Deployment Mode is required before runtime placement can be assigned.")
			return

		if self.deployment_mode in {SHARED_RUNTIME, RESERVED_RUNTIME}:
			if self.dedicated_runtime_target:
				frappe.throw(
					"Dedicated Runtime Target can only be set when Deployment Mode is Dedicated Runtime."
				)

			if not self.runtime_pool:
				if self.site_status == LIVE_STATE:
					frappe.throw(
						"Runtime Pool is required before a shared or reserved runtime environment can be marked Live."
					)
				return

			pool_doc = frappe.get_doc("Runtime Pool", self.runtime_pool)
			if getattr(pool_doc, "pool_mode", None) != self.deployment_mode:
				frappe.throw(
					f"Runtime Pool {self.runtime_pool} uses {getattr(pool_doc, 'pool_mode', 'no mode')} "
					f"and cannot back {self.deployment_mode} placement."
				)

			if not int(getattr(pool_doc, "is_active", 0)):
				frappe.throw(f"Runtime Pool {self.runtime_pool} is inactive and cannot receive placement.")

			if getattr(pool_doc, "pool_status", None) == "Disabled":
				frappe.throw(f"Runtime Pool {self.runtime_pool} is disabled and cannot receive placement.")

			pool_runtime_provider = getattr(pool_doc, "runtime_provider", None)
			if (
				pool_runtime_provider
				and self.runtime_provider
				and pool_runtime_provider != self.runtime_provider
			):
				frappe.throw(
					f"Runtime Pool {self.runtime_pool} runs on {pool_runtime_provider}, not {self.runtime_provider}."
				)

			pool_region = getattr(pool_doc, "region", None)
			if pool_region and self.region and pool_region != self.region:
				frappe.throw(f"Runtime Pool {self.runtime_pool} is in {pool_region}, not {self.region}.")

			return

		if self.deployment_mode == DEDICATED_RUNTIME:
			if self.runtime_pool:
				frappe.throw(
					"Runtime Pool can only be set when Deployment Mode is Shared Runtime or Reserved Runtime."
				)

			if self.site_status == LIVE_STATE and not (
				self.dedicated_runtime_target or self.runtime_reference
			):
				frappe.throw(
					"Dedicated Runtime Target is required before a dedicated runtime environment can be marked Live."
				)

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

		if self.file_storage_provider == GCS and self.file_storage_class != FREQUENT_ACCESS:
			frappe.throw("GCS file storage must use Frequent Access for live site files.")

		if bool(self.backup_storage_provider) != bool(self.backup_storage_class):
			frappe.throw("Backup Storage Provider and Backup Storage Class must be set together.")

		if self.backup_storage_provider == LOCAL_TEMPORARY:
			frappe.throw("Retained backups cannot use Local Temporary storage.")

		if self.backup_storage_provider == GCS and self.backup_storage_class != INFREQUENT_ACCESS:
			frappe.throw("GCS backup storage must use Infrequent Access for daily retained backups.")

		if self.policy:
			policy_doc = frappe.get_doc("Tenant Policy", self.policy)
			if policy_doc.backup_frequency != "None" and not self.backup_storage_provider:
				frappe.throw("Backup Storage Provider is required when the linked policy retains backups.")

	def _validate_routing_constraints(self) -> None:
		if self.routing_mode == "Public" and not self.primary_domain:
			frappe.throw("Primary Domain is required when Routing Mode is Public.")

		if self.routing_mode == "Public" and not self.dns_provider:
			frappe.throw("DNS Provider is required when Routing Mode is Public.")

	def _validate_ingress_access_constraints(self) -> None:
		mode = self.ingress_access_mode or "Public"
		allowlist = self.get("ingress_allowlist") or []

		if mode == "Allowlisted" and not allowlist:
			frappe.throw(
				"Ingress Allowlist must contain at least one CIDR when Ingress Access Mode is Allowlisted."
			)

		if mode != "Allowlisted" and allowlist:
			frappe.throw("Ingress Allowlist rows are only allowed when Ingress Access Mode is Allowlisted.")

		seen: set[str] = set()
		for row in allowlist:
			cidr = str(getattr(row, "cidr", "") or "").strip()
			if not cidr:
				frappe.throw("Ingress Allowlist CIDR is required.")
			try:
				network = ipaddress.ip_network(cidr, strict=False)
			except ValueError:
				frappe.throw(f"{cidr} is not a valid ingress CIDR.")
			normalized = str(network)
			if normalized in seen:
				frappe.throw(f"Duplicate ingress allowlist CIDR: {normalized}.")
			seen.add(normalized)
			row.cidr = normalized

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
			frappe.throw(
				"Primary Cloud Provider must be Google Cloud before an environment can be marked Live."
			)

		if self.runtime_provider != GOOGLE_CLOUD:
			frappe.throw("Runtime Provider must be Google Cloud before an environment can be marked Live.")

		if self.object_storage_provider != GOOGLE_CLOUD:
			frappe.throw(
				"Object Storage Provider must be Google Cloud before an environment can be marked Live."
			)

		if self.dns_provider != GOOGLE_CLOUD_DNS:
			frappe.throw("DNS Provider must be Google Cloud DNS before an environment can be marked Live.")

		if self.file_storage_provider != GCS:
			frappe.throw("File Storage Provider must be GCS before an environment can be marked Live.")

		if self.file_storage_class != FREQUENT_ACCESS:
			frappe.throw(
				"File Storage Class must be Frequent Access before an environment can be marked Live."
			)

		if self.backup_storage_provider != GCS:
			frappe.throw("Backup Storage Provider must be GCS before an environment can be marked Live.")

		if self.backup_storage_class != INFREQUENT_ACCESS:
			frappe.throw(
				"Backup Storage Class must be Infrequent Access before an environment can be marked Live."
			)

		policy_doc = frappe.get_doc("Tenant Policy", self.policy)
		if policy_doc.backup_frequency == "None":
			frappe.throw("Policy must retain backups before an environment can be marked Live.")

		if not self.backup_export_path:
			frappe.throw("Backup Export Path is required before an environment can be marked Live.")

		if not self.db_restore_tested_on:
			frappe.throw("DB Restore Tested On is required before an environment can be marked Live.")

		if self.database_mode == "Dedicated DB Instance" and not self.db_instance_name:
			frappe.throw("DB Instance Name is required before a dedicated environment can be marked Live.")
