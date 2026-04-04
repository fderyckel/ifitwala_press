from __future__ import annotations

import json
import os
import shlex
import subprocess
from typing import Any

import frappe
from frappe.model.document import Document

from ifitwala_press.ifitwala_press.services.founder_runtime_service import build_runtime_payload

ADAPTER_CONFIG_KEY = "ifitwala_press_shared_demo_bench_adapter"
TIMEOUT_CONFIG_KEY = "ifitwala_press_shared_demo_bench_timeout"
DEFAULT_TIMEOUT_SECONDS = 1800


def provision_shared_demo_site(environment: str | Document) -> dict[str, Any]:
	environment_doc = _as_doc("Tenant Environment", environment)
	tenant_doc = frappe.get_doc("Press Tenant", environment_doc.tenant)
	return _run_adapter("provision-shared-demo-site", build_runtime_payload(environment_doc, tenant_doc))


def sync_shared_demo_edge_route(environment: str | Document) -> dict[str, Any]:
	environment_doc = _as_doc("Tenant Environment", environment)
	tenant_doc = frappe.get_doc("Press Tenant", environment_doc.tenant)
	return _run_adapter("sync-shared-demo-edge-route", build_runtime_payload(environment_doc, tenant_doc))


def teardown_shared_demo_site(environment: str | Document, *, reason: str) -> dict[str, Any]:
	environment_doc = _as_doc("Tenant Environment", environment)
	tenant_doc = frappe.get_doc("Press Tenant", environment_doc.tenant)
	payload = build_runtime_payload(environment_doc, tenant_doc)
	payload["teardown_reason"] = reason
	return _run_adapter("teardown-shared-demo-site", payload)


def restore_shared_demo_site(environment: str | Document, *, reason: str) -> dict[str, Any]:
	environment_doc = _as_doc("Tenant Environment", environment)
	tenant_doc = frappe.get_doc("Press Tenant", environment_doc.tenant)
	payload = build_runtime_payload(environment_doc, tenant_doc)
	payload["restore_reason"] = reason
	return _run_adapter("restore-shared-demo-site", payload)


def _run_adapter(action: str, payload: dict[str, Any]) -> dict[str, Any]:
	command = _get_adapter_command()
	result = subprocess.run(
		[*command, action],
		input=json.dumps(payload),
		capture_output=True,
		text=True,
		timeout=_get_timeout_seconds(),
		check=False,
	)

	stdout = result.stdout.strip()
	stderr = result.stderr.strip()

	if result.returncode != 0:
		message = stderr or stdout or f"Adapter exited with code {result.returncode}."
		frappe.throw(f"Shared demo bench adapter failed during {action}: {message}")

	if not stdout:
		return {}

	try:
		parsed = json.loads(stdout)
	except json.JSONDecodeError:
		frappe.throw(f"Shared demo bench adapter returned invalid JSON during {action}.")

	if not isinstance(parsed, dict):
		frappe.throw(f"Shared demo bench adapter must return a JSON object during {action}.")

	return parsed


def _get_adapter_command() -> list[str]:
	configured = frappe.conf.get(ADAPTER_CONFIG_KEY) or os.environ.get(
		"IFITWALA_PRESS_SHARED_DEMO_BENCH_ADAPTER"
	)
	if not configured:
		frappe.throw(
			"Shared demo bench adapter is not configured. Set "
			f"`{ADAPTER_CONFIG_KEY}` in site config or `IFITWALA_PRESS_SHARED_DEMO_BENCH_ADAPTER` in the environment."
		)

	if isinstance(configured, str):
		command = shlex.split(configured)
	else:
		command = [str(part) for part in configured]

	if not command:
		frappe.throw("Shared demo bench adapter command is empty.")

	return command


def _get_timeout_seconds() -> int:
	configured = frappe.conf.get(TIMEOUT_CONFIG_KEY) or os.environ.get(
		"IFITWALA_PRESS_SHARED_DEMO_BENCH_TIMEOUT"
	)
	if configured is None:
		return DEFAULT_TIMEOUT_SECONDS

	try:
		timeout = int(configured)
	except TypeError:
		frappe.throw("Shared demo bench adapter timeout must be an integer number of seconds.")
	except ValueError:
		frappe.throw("Shared demo bench adapter timeout must be an integer number of seconds.")

	if timeout <= 0:
		frappe.throw("Shared demo bench adapter timeout must be greater than zero.")

	return timeout


def _as_doc(doctype: str, document_or_name: str | Document) -> Document:
	if isinstance(document_or_name, str):
		return frappe.get_doc(doctype, document_or_name)
	return document_or_name
