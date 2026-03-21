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


def test_service_layer_files_exist() -> None:
	assert (ROOT / "ifitwala_press" / "ifitwala_press" / "services" / "__init__.py").is_file()
	assert (
		ROOT / "ifitwala_press" / "ifitwala_press" / "services" / "environment_lifecycle_service.py"
	).is_file()
	assert (ROOT / "ifitwala_press" / "ifitwala_press" / "services" / "transition_log_service.py").is_file()
