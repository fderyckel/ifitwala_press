from pathlib import Path

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


def test_service_layer_files_exist() -> None:
	assert (ROOT / "ifitwala_press" / "ifitwala_press" / "services" / "__init__.py").is_file()
	assert (
		ROOT / "ifitwala_press" / "ifitwala_press" / "services" / "environment_lifecycle_service.py"
	).is_file()
	assert (ROOT / "ifitwala_press" / "ifitwala_press" / "services" / "transition_log_service.py").is_file()


def test_api_and_install_files_exist() -> None:
	assert (ROOT / "ifitwala_press" / "api" / "__init__.py").is_file()
	assert (ROOT / "ifitwala_press" / "api" / "business.py").is_file()
	assert (ROOT / "ifitwala_press" / "api" / "lifecycle.py").is_file()
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


def test_hooks_register_operator_surface_js() -> None:
	hooks = (ROOT / "ifitwala_press" / "hooks.py").read_text()
	assert 'app_include_css = "/assets/ifitwala_press/css/ifitwala_press.css"' in hooks
	assert '"Press Tenant": "public/js/press_tenant.js"' in hooks
	assert '"Tenant Environment": "public/js/tenant_environment.js"' in hooks
	assert '"Press Tenant": "public/js/press_tenant_list.js"' in hooks
	assert '"Tenant Environment": "public/js/tenant_environment_list.js"' in hooks


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
