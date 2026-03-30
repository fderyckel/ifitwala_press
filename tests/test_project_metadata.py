import importlib
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

import ifitwala_press

ROOT = Path(__file__).resolve().parents[1]


def test_package_version_is_defined() -> None:
	assert ifitwala_press.__version__


def test_core_frappe_app_files_exist() -> None:
	assert (ROOT / "ifitwala_press" / "hooks.py").is_file()
	assert (ROOT / "ifitwala_press" / "modules.txt").is_file()


def test_architecture_docs_exist() -> None:
	docs_root = ROOT / "ifitwala_press" / "docs"
	actual = {path.relative_to(docs_root).as_posix() for path in docs_root.rglob("*.md")}
	expected = {
		"architecture/00_control_plane_model.md",
		"architecture/01_doctype_proposal.md",
		"architecture/02_state_machine.md",
		"architecture/03_operator_surfaces.md",
		"architecture/04_actions_and_services.md",
		"architecture/05_data_and_metrics_scope.md",
		"architecture/06_permissions_and_roles.md",
		"architecture/07_naming_and_conventions.md",
		"architecture/09_infra_rollout_policy.md",
		"architecture/12_upstream_frappe_alignment_2026_q1.md",
		"architecture/13_founder_runtime_adapter_contract.md",
		"architecture/15_founder_runtime_docker_stack.md",
		"architecture/16_founder_edge_proxy_contract.md",
		"architecture/17_founder_runtime_image_and_host_bootstrap.md",
		"architecture/19_hybrid_provider_placement_contract.md",
		"architecture/20_error_event_ingestion_and_triage.md",
		"architecture/22_runtime_libmagic_contract.md",
	}
	removed = {
		"architecture/08_initial_build_order.md",
		"architecture/10_mvp_execution_plan.md",
		"architecture/11_phase1_deployment_contract.md",
		"architecture/14_phase1_s3_storage_contract.md",
		"architecture/18_founder_gcp_diagnostics.md",
		"architecture/21_error_event_ingestion_implementation_plan.md",
		"google/01_audit_archi.md",
		"google/02_cloudsql_mariadb.md",
		"google/03_redis_memorystore_feasibility.md",
	}
	assert expected.issubset(actual)
	assert removed.isdisjoint(actual)
	assert len(actual) <= 17


def test_runtime_baseline_metadata_is_consistent() -> None:
	pyproject = (ROOT / "pyproject.toml").read_text()

	assert 'requires-python = ">=3.14,<3.15"' in pyproject
	assert 'target-version = "py314"' in pyproject
	assert 'python = "3.14"' in pyproject
	assert 'mariadb = "11.4"' in pyproject
	assert 'node = "24+"' in pyproject
	assert 'javascript_package_manager = "yarn"' in pyproject


def test_local_version_files_exist() -> None:
	assert (ROOT / ".python-version").read_text().strip() == "3.14"
	assert (ROOT / ".nvmrc").read_text().strip() == "24"


def test_core_phase_one_doctype_files_exist() -> None:
	assert (ROOT / "ifitwala_press" / "ifitwala_press" / "doctype" / "__init__.py").is_file()
	assert (ROOT / "ifitwala_press" / "ifitwala_press" / "doctype" / "press_tenant" / "__init__.py").is_file()
	assert (ROOT / "ifitwala_press" / "ifitwala_press" / "doctype" / "press_tenant" / "press_tenant.py").is_file()
	assert (ROOT / "ifitwala_press" / "ifitwala_press" / "doctype" / "press_tenant" / "press_tenant.json").is_file()
	assert (ROOT / "ifitwala_press" / "ifitwala_press" / "doctype" / "tenant_environment" / "__init__.py").is_file()
	assert (ROOT / "ifitwala_press" / "ifitwala_press" / "doctype" / "tenant_environment" / "tenant_environment.py").is_file()
	assert (ROOT / "ifitwala_press" / "ifitwala_press" / "doctype" / "tenant_environment" / "tenant_environment.json").is_file()
	assert (ROOT / "ifitwala_press" / "ifitwala_press" / "doctype" / "tenant_transition_log" / "__init__.py").is_file()
	assert (ROOT / "ifitwala_press" / "ifitwala_press" / "doctype" / "tenant_transition_log" / "tenant_transition_log.py").is_file()
	assert (ROOT / "ifitwala_press" / "ifitwala_press" / "doctype" / "tenant_transition_log" / "tenant_transition_log.json").is_file()
	assert (ROOT / "ifitwala_press" / "ifitwala_press" / "doctype" / "tenant_subscription" / "__init__.py").is_file()
	assert (ROOT / "ifitwala_press" / "ifitwala_press" / "doctype" / "tenant_subscription" / "tenant_subscription.py").is_file()
	assert (ROOT / "ifitwala_press" / "ifitwala_press" / "doctype" / "tenant_subscription" / "tenant_subscription.json").is_file()
	assert (ROOT / "ifitwala_press" / "ifitwala_press" / "doctype" / "tenant_usage_snapshot" / "__init__.py").is_file()
	assert (ROOT / "ifitwala_press" / "ifitwala_press" / "doctype" / "tenant_usage_snapshot" / "tenant_usage_snapshot.py").is_file()
	assert (ROOT / "ifitwala_press" / "ifitwala_press" / "doctype" / "tenant_usage_snapshot" / "tenant_usage_snapshot.json").is_file()
	assert (ROOT / "ifitwala_press" / "ifitwala_press" / "doctype" / "tenant_cost_snapshot" / "__init__.py").is_file()
	assert (ROOT / "ifitwala_press" / "ifitwala_press" / "doctype" / "tenant_cost_snapshot" / "tenant_cost_snapshot.py").is_file()
	assert (ROOT / "ifitwala_press" / "ifitwala_press" / "doctype" / "tenant_cost_snapshot" / "tenant_cost_snapshot.json").is_file()


def test_environment_model_includes_founder_runtime_mvp_fields() -> None:
	environment_source = (
		ROOT / "ifitwala_press" / "ifitwala_press" / "doctype" / "tenant_environment" / "tenant_environment.json"
	).read_text()
	for field_name in (
		"demo_seed_mode",
		"demo_seed_reference",
		"ifitwala_drive_branch",
		"socketio_enabled",
		"worker_profile",
		"file_storage_class",
		"backup_storage_provider",
		"backup_storage_class",
		"runtime_reference",
		"backup_export_path",
		"primary_cloud_provider",
		"runtime_provider",
		"object_storage_provider",
		"dns_provider",
	):
		assert field_name in environment_source


def test_policy_model_includes_storage_defaults() -> None:
	policy_source = (
		ROOT / "ifitwala_press" / "ifitwala_press" / "doctype" / "tenant_policy" / "tenant_policy.json"
	).read_text()
	for field_name in (
		"default_file_storage_provider",
		"default_file_storage_class",
		"default_backup_storage_provider",
		"default_backup_storage_class",
		"default_primary_cloud_provider",
		"default_runtime_provider",
		"default_object_storage_provider",
		"default_dns_provider",
	):
		assert field_name in policy_source


def test_service_layer_files_exist() -> None:
	assert (ROOT / "ifitwala_press" / "ifitwala_press" / "services" / "__init__.py").is_file()
	assert (
		ROOT / "ifitwala_press" / "ifitwala_press" / "services" / "environment_lifecycle_service.py"
	).is_file()
	assert (ROOT / "ifitwala_press" / "ifitwala_press" / "services" / "founder_runtime_service.py").is_file()
	assert (ROOT / "ifitwala_press" / "ifitwala_press" / "services" / "transition_log_service.py").is_file()


def test_founder_runtime_ops_assets_exist() -> None:
	for relative_path in (
		"ops/founder_runtime/README.md",
		"ops/founder_runtime/adapter.py",
		"ops/founder_runtime/adapter.env.example",
		"ops/founder_runtime/image/README.md",
		"ops/founder_runtime/image/Dockerfile",
		"ops/founder_runtime/image/build-runtime-image.sh",
		"ops/founder_runtime/image/build.env.example",
		"ops/founder_runtime/host/README.md",
		"ops/founder_runtime/host/bootstrap-founder-vm.sh",
		"ops/founder_runtime/host/install-backup-timer.sh",
		"ops/founder_runtime/host/systemd/ifitwala-founder-backup.service.template",
		"ops/founder_runtime/host/systemd/ifitwala-founder-backup.timer.template",
		"ops/founder_runtime/diagnostics/README.md",
		"ops/founder_runtime/diagnostics/lib.sh",
		"ops/founder_runtime/diagnostics/gcp-platform-doctor.sh",
		"ops/founder_runtime/diagnostics/founder-runtime-doctor.sh",
		"ops/founder_runtime/diagnostics/storage-backup-doctor.sh",
		"ops/founder_runtime/edge_proxy/README.md",
		"ops/founder_runtime/edge_proxy/compose.yaml",
		"ops/founder_runtime/edge_proxy/nginx.conf",
		"ops/founder_runtime/edge_proxy/route.conf.template",
		"ops/founder_runtime/templates/compose.yaml",
		"ops/founder_runtime/templates/nginx-default.conf",
		"ops/founder_runtime/scripts/init-site.sh",
		"ops/founder_runtime/scripts/run-backend.sh",
		"ops/founder_runtime/scripts/run-worker.sh",
		"ops/founder_runtime/scripts/run-scheduler.sh",
		"ops/founder_runtime/scripts/backup-site.sh",
		"ops/founder_runtime/scripts/backup-all-sites.sh",
		"ops/founder_runtime/scripts/restore-site.sh",
	):
		assert (ROOT / relative_path).is_file()


def test_founder_runtime_payload_includes_storage_contract() -> None:
	service_source = (
		ROOT / "ifitwala_press" / "ifitwala_press" / "services" / "founder_runtime_service.py"
	).read_text()
	for token in (
		'"policy"',
		'"providers"',
		'"storage"',
		'"file_storage_class"',
		'"backup_storage_provider"',
		'"backup_storage_class"',
		'"site_storage_apps"',
		'"primary_cloud_provider"',
		'"runtime_provider"',
		'"object_storage_provider"',
		'"dns_provider"',
	):
		assert token in service_source


def test_storage_docs_lock_gcs_baseline() -> None:
	storage_doc = (
		ROOT / "ifitwala_press" / "docs" / "architecture" / "15_founder_runtime_docker_stack.md"
	).read_text()
	for token in (
		"GCS storage contract",
		"frequent-access class",
		"less-frequent class",
		"`ifitwala_ed`",
		"`ifitwala_drive`",
	):
		assert token in storage_doc


def test_founder_runtime_docker_doc_mentions_gcloud_dns() -> None:
	docker_doc = (
		ROOT / "ifitwala_press" / "docs" / "architecture" / "15_founder_runtime_docker_stack.md"
	).read_text()
	for token in (
		"Docker Compose",
		"GCS",
		"Google Cloud DNS",
		"`gcloud dns ...`",
		"`ifitwala_ed`",
		"`ifitwala_drive`",
	):
		assert token in docker_doc


def test_founder_runtime_image_build_locks_libmagic_contract() -> None:
	dockerfile = (ROOT / "ops" / "founder_runtime" / "image" / "Dockerfile").read_text()
	for token in (
		"libmagic1",
		'env/bin/python -c "import magic; print(magic.from_buffer(b\'%PDF-1.7\', mime=True))"',
	):
		assert token in dockerfile


def test_founder_runtime_env_examples_lock_current_founder_refs() -> None:
	build_env = (ROOT / "ops" / "founder_runtime" / "image" / "build.env.example").read_text()
	for token in (
		"ghcr.io/fderyckel/ifitwala-founder-runtime:2026-03-27-libmagic",
		"https://github.com/fderyckel/ifitwala_ed.git",
		"IFITWALA_ED_REF=2026-week13",
		"https://github.com/fderyckel/ifitwala_drive.git",
		"IFITWALA_DRIVE_REF=26-week14",
	):
		assert token in build_env

	adapter_env = (ROOT / "ops" / "founder_runtime" / "adapter.env.example").read_text()
	for token in (
		"ghcr.io/fderyckel/ifitwala-founder-runtime:2026-03-27-libmagic",
		"IFITWALA_FOUNDER_RUNTIME_GCS_FILES_BUCKET=change-me-files-bucket",
		"IFITWALA_FOUNDER_RUNTIME_GCS_BACKUPS_BUCKET=change-me-backups-bucket",
		"IFITWALA_FOUNDER_RUNTIME_DOMAIN_SUFFIX=ifitwala.com",
		"IFITWALA_FOUNDER_RUNTIME_DNS_ZONE=change-me",
		"IFITWALA_FOUNDER_RUNTIME_DNS_TARGET_IP=change-me",
	):
		assert token in adapter_env


def test_founder_host_bootstrap_locks_ubuntu_baseline() -> None:
	host_readme = (ROOT / "ops" / "founder_runtime" / "host" / "README.md").read_text()
	assert "Ubuntu 24.04 LTS" in host_readme

	bootstrap_script = (ROOT / "ops" / "founder_runtime" / "host" / "bootstrap-founder-vm.sh").read_text()
	for token in (
		"/etc/os-release",
		'ID:-}" != "ubuntu"',
		'VERSION_ID:-}" != "24.04"',
	):
		assert token in bootstrap_script
	assert "awscli" not in bootstrap_script


def test_founder_edge_proxy_doc_mentions_shared_routing_bridge() -> None:
	edge_doc = (
		ROOT / "ifitwala_press" / "docs" / "architecture" / "16_founder_edge_proxy_contract.md"
	).read_text()
	for token in (
		"shared nginx edge proxy",
		"Cloud DNS",
		"`Ifitwala_Press` owns",
		"`gcloud dns ...`",
	):
		assert token in edge_doc


def test_founder_host_bootstrap_doc_mentions_image_and_backup_timer() -> None:
	host_doc = (
		ROOT / "ifitwala_press" / "docs" / "architecture" / "17_founder_runtime_image_and_host_bootstrap.md"
	).read_text()
	for token in (
		"Ubuntu 24.04 LTS",
		"immutable runtime image",
		"`ifitwala_ed`",
		"`ifitwala_drive`",
		"`docker compose`",
		"systemd timer",
		"`gcloud`",
		"`gcloud storage`",
	):
		assert token in host_doc


def test_founder_diagnostics_readme_mentions_google_cloud_tools() -> None:
	diagnostics_doc = (ROOT / "ops" / "founder_runtime" / "diagnostics" / "README.md").read_text()
	for token in (
		"`gcp-platform-doctor.sh`",
		"`founder-runtime-doctor.sh`",
		"`storage-backup-doctor.sh`",
		"Cloud Storage",
		"`GCS_*`",
		"Cloud DNS",
	):
		assert token in diagnostics_doc


def test_hybrid_provider_placement_doc_mentions_gcp_and_ovh() -> None:
	provider_doc = (
		ROOT / "ifitwala_press" / "docs" / "architecture" / "19_hybrid_provider_placement_contract.md"
	).read_text()
	for token in (
		"`primary_cloud_provider`",
		"`runtime_provider`",
		"`object_storage_provider`",
		"`dns_provider`",
		"Google Cloud",
		"OVH",
	):
		assert token in provider_doc


def test_api_and_install_files_exist() -> None:
	assert (ROOT / "ifitwala_press" / "api" / "__init__.py").is_file()
	assert (ROOT / "ifitwala_press" / "api" / "business.py").is_file()
	assert (ROOT / "ifitwala_press" / "api" / "lifecycle.py").is_file()
	assert (ROOT / "ifitwala_press" / "api" / "permission.py").is_file()
	assert (ROOT / "ifitwala_press" / "install.py").is_file()


def test_hooks_enable_install_bootstrap() -> None:
	hooks = (ROOT / "ifitwala_press" / "hooks.py").read_text()
	assert 'after_install = "ifitwala_press.install.after_install"' in hooks
	assert 'before_tests = "ifitwala_press.install.before_tests"' in hooks


def test_role_bootstrap_and_lifecycle_api_are_declared() -> None:
	install_source = (ROOT / "ifitwala_press" / "install.py").read_text()
	api_source = (ROOT / "ifitwala_press" / "api" / "lifecycle.py").read_text()

	for role_name in (
		"Ifitwala Press Admin",
		"Ifitwala Press Ops",
		"Ifitwala Press Support",
		"Ifitwala Press Sales",
		"Ifitwala Press Finance",
	):
		assert role_name in install_source

	for method_name in (
		"create_sandbox",
		"complete_sandbox_provisioning",
		"provision_founder_demo_runtime",
		"expire_sandbox",
		"teardown_founder_demo_runtime",
		"qualify_for_production",
		"mark_provisioning_failed",
		"provision_production",
		"mark_live",
		"suspend_environment",
		"restore_environment",
		"archive_environment",
	):
		assert f"def {method_name}(" in api_source


def test_operator_surface_js_files_exist() -> None:
	assert (ROOT / "ifitwala_press" / "public" / "js" / "press_tenant.js").is_file()
	assert (ROOT / "ifitwala_press" / "public" / "js" / "press_tenant_list.js").is_file()
	assert (ROOT / "ifitwala_press" / "public" / "js" / "tenant_environment.js").is_file()
	assert (ROOT / "ifitwala_press" / "public" / "js" / "tenant_environment_list.js").is_file()
	assert (ROOT / "ifitwala_press" / "public" / "css" / "ifitwala_press.css").is_file()
	assert (ROOT / "ifitwala_press" / "public" / "images" / "ifitwala_press_logo.svg").is_file()


def test_workspace_files_exist() -> None:
	assert (ROOT / "ifitwala_press" / "ifitwala_press" / "workspace" / "__init__.py").is_file()
	assert (
		ROOT
		/ "ifitwala_press"
		/ "ifitwala_press"
		/ "workspace"
		/ "ifitwala_press"
		/ "ifitwala_press.json"
	).is_file()


def test_hooks_register_operator_surface_js() -> None:
	hooks = (ROOT / "ifitwala_press" / "hooks.py").read_text()
	assert 'app_include_css = "/assets/ifitwala_press/css/ifitwala_press.css"' in hooks
	assert 'add_to_apps_screen = [' in hooks
	assert '"route": "/app/control-plane-home"' in hooks
	assert '"has_permission": "ifitwala_press.api.permission.has_app_permission"' in hooks
	assert '"Press Tenant": "public/js/press_tenant.js"' in hooks
	assert '"Tenant Environment": "public/js/tenant_environment.js"' in hooks
	assert '"Press Tenant": "public/js/press_tenant_list.js"' in hooks
	assert '"Tenant Environment": "public/js/tenant_environment_list.js"' in hooks


def test_workspace_includes_all_core_doctypes() -> None:
	workspace_source = (
		ROOT
		/ "ifitwala_press"
		/ "ifitwala_press"
		/ "workspace"
		/ "ifitwala_press"
		/ "ifitwala_press.json"
	).read_text()
	for doctype_name in (
		"Press Tenant",
		"Tenant Environment",
		"Tenant Policy",
		"Tenant Subscription",
		"Tenant Usage Snapshot",
		"Tenant Cost Snapshot",
		"Tenant Transition Log",
	):
		assert doctype_name in workspace_source

	assert "Control Plane Home" in workspace_source
	assert '"link_to": "control-plane-home"' in workspace_source
	assert '"type": "Page"' in workspace_source


def test_view_api_files_exist() -> None:
	assert (ROOT / "ifitwala_press" / "api" / "views.py").is_file()


def test_control_plane_home_page_assets_exist() -> None:
	page_root = ROOT / "ifitwala_press" / "ifitwala_press" / "page" / "control_plane_home"
	assert (page_root / "__init__.py").is_file()
	assert (page_root / "control_plane_home.json").is_file()
	assert (page_root / "control_plane_home.js").is_file()


def test_detail_panel_api_methods_are_declared() -> None:
	view_api_source = (ROOT / "ifitwala_press" / "api" / "views.py").read_text()
	assert "def get_control_plane_home(" in view_api_source
	assert "def get_tenant_environment_panel(" in view_api_source
	assert "def get_environment_transition_history(" in view_api_source
	assert "ensure_app_permission(" in view_api_source


def test_business_api_methods_are_declared() -> None:
	business_api_source = (ROOT / "ifitwala_press" / "api" / "business.py").read_text()
	assert "ensure_app_permission(" in business_api_source
	for method_name in (
		"get_tenant_business_summary",
		"get_environment_business_summary",
		"record_tenant_subscription",
		"record_usage_snapshot",
		"record_cost_snapshot",
	):
		assert f"def {method_name}(" in business_api_source


def test_app_permission_uses_server_role_lookup(monkeypatch) -> None:
	def _throw(message: str) -> None:
		raise RuntimeError(message)

	fake_frappe = SimpleNamespace(get_roles=lambda: ["Ifitwala Press Ops"], throw=_throw)
	monkeypatch.setitem(sys.modules, "frappe", fake_frappe)
	sys.modules.pop("ifitwala_press.api.permission", None)

	permission = importlib.import_module("ifitwala_press.api.permission")

	assert permission.has_app_permission() is True
	permission.ensure_app_permission("view dashboards")

	fake_frappe.get_roles = lambda: ["System Manager"]
	assert permission.has_app_permission() is False
	with pytest.raises(RuntimeError, match="view dashboards"):
		permission.ensure_app_permission("view dashboards")
