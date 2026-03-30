from __future__ import annotations

from typing import Any

from frappe.model.document import Document


def build_drive_storage_profile(environment: Document) -> dict[str, Any]:
	backend_name = _normalize_provider(environment.file_storage_provider)
	return {
		"backend_name": backend_name,
		"provider_family": backend_name,
		"bucket_or_container": None,
		"base_prefix": _build_base_prefix(environment),
		"region": getattr(environment, "region", None) or None,
		"endpoint": None,
		"signing_mode": "runtime_managed" if backend_name != "local" else "proxy_only",
		"quota_scope": environment.name,
		"credential_source": "runtime_identity" if backend_name != "local" else "site_config",
		"upload_strategy": "proxy_post" if backend_name == "local" else "signed_put",
	}


def _build_base_prefix(environment: Document) -> str:
	site_name = str(getattr(environment, "site_name", None) or "").strip().strip("/")
	if not site_name:
		return ""
	return f"sites/{site_name}"


def _normalize_provider(value: str | None) -> str:
	text = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
	if text in {"", "local_temporary"}:
		return "local"
	if text in {"s3_compatible", "s3"}:
		return "s3_compatible"
	if text == "gcs":
		return "gcs"
	return text
