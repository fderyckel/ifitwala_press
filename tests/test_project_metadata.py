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
