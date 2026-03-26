import importlib
import sys
from pathlib import Path
from types import SimpleNamespace

import ifitwala_press

ROOT = Path(__file__).resolve().parents[1]


def test_package_version_is_defined() -> None:
	assert ifitwala_press.__version__


def test_core_frappe_app_files_exist() -> None:
	assert (ROOT / "ifitwala_press" / "hooks.py").is_file()
	assert (ROOT / "ifitwala_press" / "modules.txt").is_file()


def test_architecture_docs_exist() -> None:
	assert (ROOT / "ifitwala_press" / "docs" / "architecture" / "00_control_plane_model.md").is_file()
	assert (ROOT / "ifitwala_press" / "docs" / "architecture" / "08_initial_build_order.md").is_file()
	assert (ROOT / "ifitwala_press" / "docs" / "architecture" / "10_mvp_execution_plan.md").is_file()
	assert (ROOT / "ifitwala_press" / "docs" / "architecture" / "12_upstream_frappe_alignment_2026_q1.md").is_file()
	assert (ROOT / "ifitwala_press" / "docs" / "architecture" / "13_founder_runtime_adapter_contract.md").is_file()
	assert (ROOT / "ifitwala_press" / "docs" / "architecture" / "14_phase1_s3_storage_contract.md").is_file()
	assert (ROOT / "ifitwala_press" / "docs" / "architecture" / "15_founder_runtime_docker_stack.md").is_file()
	assert (ROOT / "ifitwala_press" / "docs" / "architecture" / "16_founder_edge_proxy_contract.md").is_file()
	assert (ROOT / "ifitwala_press" / "docs" / "architecture" / "17_founder_runtime_image_and_host_bootstrap.md").is_file()


def test_runtime_baseline_metadata_is_consistent() -> None:
	pyproject = (ROOT / "pyproject.toml").read_text()

	assert 'requires-python = ">=3.14,<3.15"' in pyproject
	assert 'target-version = "py314"' in pyproject
	assert 'python = "3.14"' in pyproject
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
	):
		assert field_name in environment_source


def test_policy_model_includes_s3_storage_defaults() -> None:
	policy_source = (
		ROOT / "ifitwala_press" / "ifitwala_press" / "doctype" / "tenant_policy" / "tenant_policy.json"
	).read_text()
	for field_name in (
		"default_file_storage_provider",
		"default_file_storage_class",
		"default_backup_storage_provider",
		"default_backup_storage_class",
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
	):
		assert (ROOT / relative_path).is_file()


def test_founder_runtime_payload_includes_storage_contract() -> None:
	service_source = (
		ROOT / "ifitwala_press" / "ifitwala_press" / "services" / "founder_runtime_service.py"
	).read_text()
	for token in (
		'"policy"',
		'"storage"',
		'"file_storage_class"',
		'"backup_storage_provider"',
		'"backup_storage_class"',
		'"site_storage_apps"',
	):
		assert token in service_source


def test_phase_one_storage_docs_lock_s3_baseline() -> None:
	storage_doc = (
		ROOT / "ifitwala_press" / "docs" / "architecture" / "14_phase1_s3_storage_contract.md"
	).read_text()
	for token in (
		"S3-compatible object storage",
		"Frequent Access",
		"Infrequent Access",
		"daily exported site backups",
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
		"Google Cloud DNS",
		"`gcloud dns ...`",
		"`ifitwala_ed`",
		"`ifitwala_drive`",
	):
		assert token in docker_doc


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
		"immutable runtime image",
		"`ifitwala_ed`",
		"`ifitwala_drive`",
		"`docker compose`",
		"systemd timer",
		"`gcloud`",
	):
		assert token in host_doc


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
	assert '"route": "/app/ifitwala-press"' in hooks
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


def test_view_api_files_exist() -> None:
	assert (ROOT / "ifitwala_press" / "api" / "views.py").is_file()


def test_detail_panel_api_methods_are_declared() -> None:
	view_api_source = (ROOT / "ifitwala_press" / "api" / "views.py").read_text()
	assert "def get_tenant_environment_panel(" in view_api_source
	assert "def get_environment_transition_history(" in view_api_source


def test_business_api_methods_are_declared() -> None:
	business_api_source = (ROOT / "ifitwala_press" / "api" / "business.py").read_text()
	for method_name in (
		"get_tenant_business_summary",
		"get_environment_business_summary",
		"record_tenant_subscription",
		"record_usage_snapshot",
		"record_cost_snapshot",
	):
		assert f"def {method_name}(" in business_api_source


def test_app_permission_uses_server_role_lookup(monkeypatch) -> None:
	fake_frappe = SimpleNamespace(get_roles=lambda: ["Ifitwala Press Ops"])
	monkeypatch.setitem(sys.modules, "frappe", fake_frappe)
	sys.modules.pop("ifitwala_press.api.permission", None)

	permission = importlib.import_module("ifitwala_press.api.permission")

	assert permission.has_app_permission() is True

	fake_frappe.get_roles = lambda: ["System Manager"]
	assert permission.has_app_permission() is False
